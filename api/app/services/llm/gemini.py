import google.generativeai as genai
import os
import time

class GeminiService:
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
        genai.configure(api_key=api_key)
        self.model = "models/text-embedding-004"

    def embed_content(self, text: str):
        try:
            # No sleep, we want speed. 
            # If rate limit hits, the task retry logic handles it or we skip.
            result = genai.embed_content(
                model=self.model,
                content=text,
                task_type="retrieval_document"
            )
            return result['embedding']
        except Exception as e:
            print(f"Embedding error: {str(e)}")
            return None
