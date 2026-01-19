import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class QueryRewriter:
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1" if os.getenv("OPENROUTER_API_KEY") else None
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        self.model = "google/gemini-2.0-flash-001" 

    def refine_query(self, original_query: str) -> str:
        """
        Rewrites a user query to be more suitable for retrieval.
        """
        system_prompt = (
            "You are an AI assistant that optimizes queries for a RAG system. "
            "Your task is to rewrite the user's query to be specific, keyword-rich, and suitable for semantic search. "
            "Remove unnecessary conversational filler. Return ONLY the rewritten query."
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": original_query}
                ]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            # Fallback to original if LLM fails
            return original_query
            
_rewriter = None
def get_rewriter():
    global _rewriter
    if _rewriter is None:
        _rewriter = QueryRewriter()
    return _rewriter
