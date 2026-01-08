import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from app.core.config import settings
from typing import List
import logging
import json
import re

logger = logging.getLogger(__name__)

# --- Data Models ---
class RelevanceGrade(BaseModel):
    binary_score: str = Field(description="'yes' or 'no' score to indicate whether the document is relevant to the question")

class GeminiService:
    def __init__(self):
        if not settings.GOOGLE_API_KEY:
             raise ValueError("GOOGLE_API_KEY is not set in environment variables.")
        
        # 1. Configure Synchronous Client (For Ingestion Worker)
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.embed_model = "models/text-embedding-004"
        
        # 2. Configure Async LangChain Client (For Chat Agent)
        self.llm_flash = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0
        )
        self.llm_pro = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.3
        )

    # --- Worker Method (Synchronous) ---
    def embed_content(self, text: str) -> List[float]:
        """
        Used by Celery Worker to embed code chunks.
        """
        try:
            if not text or not text.strip():
                return []
            result = genai.embed_content(
                model=self.embed_model,
                content=text,
                task_type="retrieval_document"
            )
            return result['embedding']
        except Exception as e:
            logger.error(f"Gemini Embedding Error: {e}")
            return []

    # --- Agent Methods (Asynchronous) ---
    async def embed_query(self, text: str) -> List[float]:
        """
        Used by VectorSearchService to embed the user's question.
        """
        try:
            result = genai.embed_content(
                model=self.embed_model,
                content=text,
                task_type="retrieval_query"
            )
            return result['embedding']
        except Exception as e:
            logger.error(f"Gemini Query Embedding Error: {e}")
            return []

    async def grade_relevance(self, question: str, context: str) -> RelevanceGrade:
        """
        Manually parses JSON from Gemini to avoid library version conflicts.
        """
        prompt = f"""You are a strict relevance grader.

        Question: {question}

        Code Snippet:
        {context[:2000]}...

        Assess if the snippet is relevant to the question.
        Respond ONLY in JSON with the following strict schema:
        {{
            "binary_score": "yes" or "no"
        }}
        """
        
        try:
            # 1. Invoke Model
            response = await self.llm_flash.ainvoke(prompt)
            content = response.content.strip()

            # 2. Clean Markdown (Gemini often wraps JSON in ```json ... ```)
            if content.startswith("```json"):
                content = content[7:]
            elif content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            
            content = content.strip()

            # 3. Parse JSON
            data = json.loads(content)
            
            # 4. Validate with Pydantic
            return RelevanceGrade(**data)

        except Exception as e:
            logger.error(f"Grading Error (Manual Parse): {e}. Content was: {content if 'content' in locals() else 'Unknown'}")
            # Fallback to 'yes' to ensure the user gets an answer even if grading fails
            return RelevanceGrade(binary_score="yes")

    async def generate_rag_response(self, question: str, context: List[any]) -> str:
        """
        Generates the final answer using the context.
        Handles both LangChain Documents and Pydantic ChunkCitation objects.
        """
        context_str = ""
        for doc in context:
            # Handle Pydantic ChunkCitation (flattened attributes)
            if hasattr(doc, "file_path"): 
                file_path = doc.file_path
                content = doc.content_preview
            # Handle LangChain Document (nested metadata)
            else:
                file_path = doc.metadata.get("file_path", "unknown")
                content = doc.page_content
                
            context_str += f"File: {file_path}\nCode:\n{content}\n\n"

        prompt = f"""You are CodeSense, an expert AI software engineer.
        Answer the user's question based strictly on the provided context.
        
        Guidelines:
        - If the answer is not in the code, admit it.
        - Cite specific file names and variable names.
        - Use Markdown for code blocks.
        
        Question: {question}
        
        Context:
        {context_str}
        """
        
        response = await self.llm_pro.ainvoke(prompt)
        return response.content
        """
        Generates the final answer using the context.
        """
        # Format context from the retrieved documents
        context_str = "\n\n".join(
            [f"File: {doc.metadata.get('file_path', 'unknown')}\nCode:\n{doc.page_content}" for doc in context]
        )

        prompt = f"""You are CodeSense, an expert AI software engineer.
        Answer the user's question based strictly on the provided context.
        
        Guidelines:
        - If the answer is not in the code, admit it.
        - Cite specific file names and variable names.
        - Use Markdown for code blocks.
        
        Question: {question}
        
        Context:
        {context_str}
        """
        
        response = await self.llm_pro.ainvoke(prompt)
        return response.content