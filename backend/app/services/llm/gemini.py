import google.generativeai as genai
import os
from typing import Generator

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

    def stream_chat(self, prompt: str) -> Generator[str, None, None]:
        """
        Streams raw response from Gemini based on a provided full prompt.
        No prompt engineering happens here.
        """
        try:
            response = self.chat_model.generate_content(prompt, stream=True)
            
            buffer = ""
            is_first_chunk = True
            
            for chunk in response:
                if not chunk.text:
                    continue
                    
                text = chunk.text
                
                # Cleanup: Remove Markdown code block wrappers if they appear at start/end
                # This is a common artifact with code-heavy models
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
            
            # Flush remaining buffer (remove trailing ``` if present)
            if buffer.endswith("```"):
                yield buffer[:-3]
            else:
                yield buffer
                
        except Exception as e:
            yield f"\n\n[AI Error: {str(e)}]"

    def perform_audit(self, file_contents: dict):
        # We construct the prompt here just for the audit specific task
        # In a full refactor, this would also move to AuditService
        context = ""
        for path, content in list(file_contents.items())[:10]:
            context += f"--- FILE: {path} ---\n{content[:1500]}\n\n"

        prompt = f"""
        You are performing a high-rigor code audit. Your role is:
        - Senior Staff Engineer
        - Zero tolerance for vague feedback
        - No compliments, no generalities
        - Only concrete, actionable issues

        You are given up to 10 files from a codebase.

        === CODEBASE SNIPPETS ===
        {context}
        === END SNIPPETS ===

        YOUR TASK:
        Identify *exactly 3* critical issues that fall under:
        - Security flaw
        - Performance bottleneck
        - Bad practice / incorrect architecture

        Rules:
        1. Each issue must cite the specific file and line region.
        2. Each issue must be concise and technically correct.
        3. Each fix must show *actual corrected code* — not pseudocode.
        4. Output **ONLY** valid JSON. No prose.

        STRICT OUTPUT FORMAT (no deviations):

        [
        {
            "severity": "High",
            "file": "path/to/file",
            "title": "Short problem title",
            "description": "1-3 sentence explanation of the issue",
            "suggestion": "1-2 sentence change instructions",
            "code_fix": "Corrected code snippet ONLY"
        }
        ]

        Return nothing else.
        """

        try:
            response = self.chat_model.generate_content(prompt)
            clean = response.text.replace("```json", "").replace("```", "").strip()
            return clean
        except Exception as e:
            print(f"Audit Error: {e}")
            return "[]"