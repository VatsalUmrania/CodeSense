import google.generativeai as genai
import os

class GeminiService:
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found")
        genai.configure(api_key=api_key)
        self.embed_model = "models/text-embedding-004"
        # Ensure using a model that supports streaming
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

    def generate_response_stream(self, query: str, context: str, history: list = []):
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
        2. Cite specific file names using markdown links: [filename](path/to/file).
        3. Format in Markdown.

        """
        
        try:
            response = self.chat_model.generate_content(prompt, stream=True)
            
            # Buffer to handle potential wrapping removal
            buffer = ""
            is_first_chunk = True
            
            for chunk in response:
                try:
                    if chunk.text:
                        text = chunk.text
                        
                        # Check first chunk for starting ```markdown or ```
                        if is_first_chunk:
                            text = text.lstrip()
                            if text.startswith("```markdown"):
                                text = text[11:]
                            elif text.startswith("```"):
                                text = text[3:]
                            is_first_chunk = False
                        
                        buffer += text
                        
                        # Yield buffer but keep last few chars to check for ending ```
                        if len(buffer) > 3:
                            to_yield = buffer[:-3]
                            buffer = buffer[-3:]
                            yield to_yield
                            
                except Exception:
                    continue
            
            # Process remaining buffer (remove trailing ``` if present)
            if buffer.endswith("```"):
                yield buffer[:-3]
            else:
                yield buffer
                
        except Exception as e:
            yield f"\n\n[AI Error: {str(e)}]"

    # ... (Keep perform_audit method as is)
    def perform_audit(self, file_contents: dict):
        context = ""
        for path, content in list(file_contents.items())[:10]:
            context += f"--- FILE: {path} ---\n{content[:1500]}\n\n"

        prompt = f"""
        You are a Senior Staff Engineer conducting a critical code audit.
        
        CODEBASE CHUNK:
        {context}
        
        TASK:
        Identify exactly 3 critical issues (Security, Performance, or Bad Practice).
        For each issue, provide a SPECIFIC code fix.
        
        Output ONLY valid JSON in this format:
        [
            {{
                "severity": "High",
                "title": "Short Title",
                "description": "Concise explanation",
                "suggestion": "Brief instruction on what to change",
                "code_fix": "The corrected code snippet"
            }}
        ]
        """
        try:
            response = self.chat_model.generate_content(prompt)
            clean = response.text.replace("```json", "").replace("```", "").strip()
            return clean
        except Exception as e:
            print(f"Audit Error: {e}")
            return "[]"