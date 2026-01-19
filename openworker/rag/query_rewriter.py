from openworker.prompts.rag import RAG_SYSTEM_PROMPT
from openworker.core.llm import LLMClient



class QueryRewriter:
    def __init__(self):
        self.llm = LLMClient(model="google/gemini-2.0-flash-001") 

    def refine_query(self, original_query: str) -> str:
        """
        Rewrites a user query to be more suitable for retrieval.
        """
        system_prompt = RAG_SYSTEM_PROMPT
        
        try:
            message = self.llm.chat(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": original_query}
                ]
            )
            return message.content.strip() if message.content else original_query
        except Exception as e:
            # Fallback to original if LLM fails
            return original_query
            
_rewriter = None
def get_rewriter():
    global _rewriter
    if _rewriter is None:
        _rewriter = QueryRewriter()
    return _rewriter
