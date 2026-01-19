from mcp.server.fastmcp import FastMCP
from openworker.utils.readers import read_file_content
from openworker.rag.security import secure_path
import os
from pathlib import Path

import logging
import sys

# Configure logging to stderr to avoid breaking MCP stdout protocol
logging.basicConfig(level=logging.INFO, stream=sys.stderr)
os.environ["ANONYMIZED_TELEMETRY"] = "False"

# Suppress verbose MCP internal logs
logging.getLogger("mcp").setLevel(logging.WARNING)

# Initialize FastMCP Server
mcp = FastMCP("macopenworker")

@mcp.tool()
@secure_path(arg_name="path")
def read_file(path: str) -> str:
    """
    Read the content of a local file. Supports PDF, Docx, Excel, Text, Code.
    Args:
        path: Absolute path to the file.
    """
    return read_file_content(path)

@mcp.tool()
@secure_path(arg_name="directory")
def list_files(directory: str) -> str:
    """
    List files in a directory recursively.
    Args:
        directory: Absolute path to the directory.
    """
    path = Path(directory)
    if not path.exists() or not path.is_dir():
        return f"Error: Directory not found {directory}"
    
    files = []
    for p in path.rglob("*"):
        if p.is_file() and not p.name.startswith("."):
            files.append(str(p))
    return "\n".join(files[:1000]) # hard limit to avoid context blowup

@mcp.tool()
@secure_path(arg_name="path")
def write_file(path: str, content: str) -> str:
    """
    Write content to a file. Overwrites if exists.
    Args:
        path: Absolute path.
        content: Text content to write.
    """
    try:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"

@mcp.tool()
@secure_path(arg_name="directory")
def index_folder(directory: str) -> str:
    """
    Index a folder for RAG knowledge base.
    Args:
        directory: Absolute path to folder.
    """
    from openworker.rag.store import get_store
    try:
        store = get_store()
        return store.index_directory(directory)
    except Exception as e:
        return f"Error indexing: {str(e)}"

@mcp.tool()
def search_knowledge(query: str) -> str:
    """
    Search the indexed knowledge base (RAG).
    Uses query refinement, hybrid search, and reranking.
    Args:
        query: Search query.
    """
    from openworker.rag.store import get_store
    from openworker.rag.query_rewriter import get_rewriter
    
    try:
        # 1. Refine Query
        rewriter = get_rewriter()
        refined_query = rewriter.refine_query(query)
        # logging.info(f"Refined query: '{query}' -> '{refined_query}'")
        
        # 2. Search (Hybrid + Rerank)
        store = get_store()
        results = store.query(refined_query)
        
        # Format results
        output = [f"Original Query: {query}", f"Refined Query: {refined_query}", "---"]
        if results['documents']:
            for i, doc_list in enumerate(results['documents']):
                for j, doc in enumerate(doc_list):
                    meta = results['metadatas'][i][j]
                    output.append(f"[Source: {meta.get('source', '?')}]\n{doc}\n")
        return "\n---\n".join(output)
    except Exception as e:
        return f"Error searching: {str(e)}"

@mcp.tool()
def reset_knowledge_base() -> str:
    """
    Clear the RAG knowledge base (delete index).
    Reference: openworker/rag/store.py
    """
    from openworker.rag.store import get_store
    try:
        store = get_store()
        return store.clear_index()
    except Exception as e:
        return f"Error resetting: {str(e)}"

if __name__ == "__main__":
    mcp.run()
