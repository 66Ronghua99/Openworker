import os
import chromadb
from sentence_transformers import SentenceTransformer, CrossEncoder
from rank_bm25 import BM25Okapi
from pathlib import Path
from openworker.utils.readers import read_file_content
from openworker.rag.splitters import RecursiveTextSplitter
import numpy as np

class RagStore:
    def __init__(self, persist_path: str = "./.store"):
        self.client = chromadb.PersistentClient(path=persist_path)
        self.collection = self.client.get_or_create_collection(name="documents")
        
        # Models
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2') 
        self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        self.splitter = RecursiveTextSplitter(chunk_size=1000, chunk_overlap=100)
        
        # In-memory BM25
        self.bm25 = None
        self.bm25_corpus = []  # List of document texts
        self.bm25_ids = []     # List of corresponding IDs
        
        # Try to load existing data for BM25
        self._load_bm25()

    def _load_bm25(self):
        """Reloads corpus from ChromaDB to build BM25 index."""
        # Warning: This scales poorly for millions of docs. Fine for thousands.
        existing = self.collection.get()
        if existing['documents']:
            self.bm25_corpus = existing['documents']
            self.bm25_ids = existing['ids']
            tokenized_corpus = [doc.split(" ") for doc in self.bm25_corpus]
            self.bm25 = BM25Okapi(tokenized_corpus)

    def index_directory(self, directory: str):
        import hashlib
        from datetime import datetime
        
        path = Path(directory)
        if not path.exists():
            return "Directory not found."

        ids_batch, docs_batch, metas_batch = [], [], []
        count = 0
        
        for p in path.rglob("*"):
            if p.is_file() and not p.name.startswith("."):
                try:
                    content = read_file_content(str(p))
                    if not content or content.startswith("Error"):
                        continue
                        
                    # Compute Hash
                    file_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
                    last_modified = datetime.fromtimestamp(p.stat().st_mtime).isoformat()
                    
                    # Compute relative path for cleaner metadata
                    rel_path = str(p.relative_to(path.parent))
                    
                    # Splitting
                    chunks = self.splitter.split_text(content)
                    
                    for i, chunk in enumerate(chunks):
                        # Unique ID: Hash + Index (ensures if file content changes, ID changes)
                        # Actually, keeping ID deterministic based on path + index is better for updates,
                        # BUT we want to detect content changes. 
                        # Let's use path+index as ID, and simple overwrite.
                        doc_id = f"{rel_path}_{i}"
                        
                        ids_batch.append(doc_id)
                        docs_batch.append(chunk)
                        metas_batch.append({
                            "source": str(p),
                            "chunk": i,
                            "root_path": str(path),
                            "file_hash": file_hash,
                            "updated_at": last_modified
                        })
                    
                    count += 1
                except Exception as e:
                    print(f"Skipping {p}: {e}")

        if ids_batch:
            # Update Vector DB
            embeddings = self.embedder.encode(docs_batch, show_progress_bar=False).tolist()
            # Upsert (overwrite if ID exists)
            self.collection.upsert(ids=ids_batch, documents=docs_batch, embeddings=embeddings, metadatas=metas_batch)
            
            # Update BM25
            self._load_bm25()
        
        return f"Indexed {count} files. Total chunks: {len(self.bm25_ids)}"

    def query(self, query_text: str, n_results: int = 10):
        # Security: Get allowed paths
        from openworker.security import get_guard
        allowed_paths = get_guard()._get_allowed_folders()
        if not allowed_paths:
             return {"documents": [], "metadatas": []}
             
        # Create filter for authorized roots
        # ChromaDB requires at least 2 items for $or
        if len(allowed_paths) == 1:
            where_filter = {"root_path": allowed_paths[0]}
        else:
            where_filter = {"$or": [{"root_path": p} for p in allowed_paths]}

        # 1. Vector Search
        query_embedding = self.embedder.encode([query_text], show_progress_bar=False).tolist()
        vector_res = self.collection.query(
            query_embeddings=query_embedding, 
            n_results=n_results,
            where=where_filter
        )
        
        vec_ids = vector_res['ids'][0] if vector_res['ids'] else []
        vec_docs = vector_res['documents'][0] if vector_res['documents'] else []
        vec_metas = vector_res['metadatas'][0] if vector_res['metadatas'] else []
        
        # 2. BM25 Search
        bm25_docs = []
        if self.bm25:
            tokenized_query = query_text.split(" ")
            # Get top N BM25
            bm25_top = self.bm25.get_top_n(tokenized_query, self.bm25_corpus, n=n_results)
            # We need the metadata/IDs for these. Inefficient lookup map here:
            for doc in bm25_top:
                try:
                    idx = self.bm25_corpus.index(doc)
                    if self.bm25_ids[idx] not in vec_ids:
                        vec_ids.append(self.bm25_ids[idx])
                        vec_docs.append(self.bm25_corpus[idx])
                        # Fetch metadata from collection is slow, so maybe skipping or implementing a cache?
                        # For now, let's just use what we have in mem or query by ID
                        meta = self.collection.get(ids=[self.bm25_ids[idx]])['metadatas'][0]
                        vec_metas.append(meta)
                except:
                    continue

        # 3. Reranking
        if not vec_docs:
            return {"documents": [], "metadatas": []}

        pairs = [[query_text, doc] for doc in vec_docs]
        scores = self.reranker.predict(pairs)
        
        # Sort by score
        scored_results = sorted(zip(vec_docs, vec_metas, scores), key=lambda x: x[2], reverse=True)
        
        # Return top 5
        top_k = scored_results[:5]
        
        # Format to match previous structure
        return {
            "documents": [[x[0] for x in top_k]],
            "metadatas": [[x[1] for x in top_k]]
        }

    def clear_index(self):
        """Clears the entire knowledge base."""
        try:
            self.client.delete_collection("documents")
            self.collection = self.client.get_or_create_collection(name="documents")
            self.bm25 = None
            self.bm25_corpus = []
            self.bm25_ids = []
            return "Knowledge base cleared successfully."
        except Exception as e:
            return f"Error clearing knowledge base: {str(e)}"

# Singleton
_store = None
def get_store():
    global _store
    if _store is None:
        _store = RagStore()
    return _store
