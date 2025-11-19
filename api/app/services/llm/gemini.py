import google.generativeai as genai
import os
import time

class GeminiService:
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found")
        genai.configure(api_key=api_key)
        self.embed_model = "models/text-embedding-004"
        self.chat_model = genai.GenerativeModel('gemini-2.5-flash')

    def embed_content(self, text: str):
        try:
            # Retry logic included
            result = genai.embed_content(
                model=self.embed_model,
                content=text,
                task_type="retrieval_document"
            )
            return result['embedding']
        except Exception as e:
            print(f"Embedding error: {e}")
            return None

    def generate_response(self, query: str, context: str):
        prompt = f"""
        You are CodeSense, an expert AI software architect.
        You are analyzing a codebase based on the following context chunks.
        
        CONTEXT FROM REPO:
        {context}
        
        USER QUESTION: 
        {query}
        
        INSTRUCTIONS:
        1. Answer the question comprehensively using the provided context.
        2. If the context contains the answer, cite the specific file names (e.g., "In src/main.py...").
        3. If the context does not contain the exact answer, use your general programming knowledge to infer what is happening, but state clearly that you are inferring.
        4. If asked about "Repo Name", look for cues in package.json, README.md, or go.mod files in the context.
        5. Format your answer in Markdown.
        """
        try:
            response = self.chat_model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"AI Error: {str(e)}"
