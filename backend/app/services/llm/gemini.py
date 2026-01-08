import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from app.core.config import settings
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

# --- Structured Output Models ---
class RelevanceGrade(BaseModel):
    binary_score: str = Field(description=" 'yes' or 'no' score to indicate whether the document is relevant to the question")

class GeminiService:
    def __init__(self):
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.embed_model = "models/text-embedding-004"
        
        # Initialize Chat Models
        self.llm_flash = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0
        )
        self.llm_pro = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.3
        )

    async def embed_query(self, text: str) -> List[float]:
        """
        Generates embedding for a retrieval query (Async).
        Used by the Search Service.
        """
        try:
            result = genai.embed_content(
                model=self.embed_model,
                content=text,
                task_type="retrieval_query"
            )
            return result['embedding']
        except Exception as e:
            logger.error(f"Failed to embed query: {e}")
            raise e

    def embed_content(self, text: str) -> Optional[List[float]]:
        """
        Generates embedding for document content (Synchronous).
        Used by the Celery Worker pipeline.
        """
        try:
            # Note: We use the sync genai call here because Celery tasks are synchronous
            result = genai.embed_content(
                model=self.embed_model,
                content=text,
                task_type="retrieval_document"
            )
            return result['embedding']
        except Exception as e:
            logger.error(f"Failed to embed content: {e}")
            return None

    async def grade_relevance(self, question: str, context: str) -> RelevanceGrade:
        """Determines if a code chunk is relevant to the user query."""
        structured_llm = self.llm_flash.with_structured_output(RelevanceGrade)
        prompt = f"""You are a strict grader assessing the relevance of a retrieved code snippet to a user question.
        Question: {question}
        Code Snippet:
        {context[:2000]}...
        If the code snippet contains keywords, logic, or definitions related to the question, grade it as 'yes'.
        Otherwise, grade it as 'no'."""
        try:
            return await structured_llm.ainvoke(prompt)
        except Exception:
            return RelevanceGrade(binary_score="yes")

    async def generate_rag_response(self, question: str, context: List[any]) -> str:
        """Generates the final answer using the Pro model."""
        context_str = "\n\n".join(
            [f"File: {doc.metadata.get('file_path', 'unknown')}\nCode:\n{doc.page_content}" for doc in context]
        )
        prompt = f"""You are CodeSense, an expert AI software engineer.
        Answer the user's question based strictly on the provided context.
        Guidelines:
        - If the answer is not in the code, admit it.
        - Cite specific file names.
        - Use Markdown.
        
        Question: {question}
        Context:
        {context_str}"""
        response = await self.llm_pro.ainvoke(prompt)
        return response.content