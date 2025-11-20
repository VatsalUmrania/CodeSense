# import google.generativeai as genai
# import os
# import time

# class GeminiService:
#     def __init__(self):
#         api_key = os.getenv("GOOGLE_API_KEY")
#         if not api_key:
#             raise ValueError("GOOGLE_API_KEY not found")
#         genai.configure(api_key=api_key)
#         self.embed_model = "models/text-embedding-004"
#         # Ensure you use a valid model name (e.g., gemini-1.5-flash)
#         self.chat_model = genai.GenerativeModel('gemini-2.5-flash') 

#     def embed_content(self, text: str):
#         try:
#             result = genai.embed_content(
#                 model=self.embed_model,
#                 content=text,
#                 task_type="retrieval_document"
#             )
#             return result['embedding']
#         except Exception as e:
#             print(f"Embedding error: {e}")
#             return None

#     def generate_response(self, query: str, context: str, history: list = []):
#         # --- Format History for Prompt ---
#         history_text = ""
#         # We take the last 10 messages to avoid token limits
#         for msg in history[-10:]: 
#             role = "User" if msg['role'] == "user" else "AI"
#             history_text += f"{role}: {msg['content']}\n"

#         prompt = f"""
#         You are CodeSense, an expert AI software architect.
        
#         ### CONTEXT FROM REPO:
#         {context}
        
#         ### CONVERSATION HISTORY:
#         {history_text}
        
#         ### USER QUESTION: 
#         {query}
        
#         ### INSTRUCTIONS:
#         1. Answer the question comprehensively using the provided context.
#         2. Use the conversation history to understand follow-up questions (e.g., "Why did you say that?").
#         3. If the context contains the answer, cite the specific file names.
#         4. If the context is missing, infer based on general knowledge but admit it.
#         5. Format your answer in Markdown.
#         """
        
#         try:
#             response = self.chat_model.generate_content(prompt)
#             return response.text
#         except Exception as e:
#             return f"AI Error: {str(e)}"



import google.generativeai as genai
import os

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
            result = genai.embed_content(
                model=self.embed_model,
                content=text,
                task_type="retrieval_document"
            )
            return result['embedding']
        except Exception as e:
            print(f"Embedding error: {e}")
            return None

    def generate_response(self, query: str, context: str, history: list = []):
        history_text = ""
        for msg in history[-10:]: 
            role = "User" if msg['role'] == "user" else "AI"
            history_text += f"{role}: {msg['content']}\n"

        prompt = f"""
        You are CodeSense, an expert AI software architect.
        
        ### CONTEXT FROM REPO:
        {context}
        
        ### CONVERSATION HISTORY:
        {history_text}
        
        ### USER QUESTION: 
        {query}
        
        ### INSTRUCTIONS:
        1. Answer comprehensively using context.
        2. Cite specific file names.
        3. Format in Markdown.
        """
        try:
            response = self.chat_model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"AI Error: {str(e)}"

    # --- UPDATED: Audit with Code Fix ---
    def perform_audit(self, file_contents: dict):
        context = ""
        # Limit to top files to fit context
        for path, content in list(file_contents.items())[:10]:
            context += f"--- FILE: {path} ---\n{content[:1500]}\n\n"

        prompt = f"""
        You are a Senior Staff Engineer conducting a critical code audit.
        
        CODEBASE CHUNK:
        {context}
        
        TASK:
        Identify exactly 3 critical issues (Security, Performance, or Bad Practice).
        For each issue, provide a SPECIFIC code fix.
        
        Output ONLY valid JSON in this format (ensure strings are properly escaped):
        [
            {{
                "severity": "High",
                "title": "Short Title",
                "description": "Concise explanation",
                "suggestion": "Brief instruction on what to change",
                "code_fix": "The corrected code snippet (plain text, no markdown backticks inside)"
            }}
        ]
        """
        try:
            response = self.chat_model.generate_content(prompt)
            # Clean formatting
            clean = response.text.replace("```json", "").replace("```", "").strip()
            return clean
        except Exception as e:
            print(f"Audit Error: {e}")
            return "[]"