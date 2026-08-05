import json
from typing import TYPE_CHECKING

from fastapi import HTTPException

# Avoid circular imports during development
if TYPE_CHECKING:
    from rag.pipeline import RAGPipeline
    from groq import Groq


class ReviewService:
    """
    Handles all AI review-related business logic.

    The FastAPI route should only:
        1. Receive the request
        2. Call this service
        3. Return the response
    """

    def __init__(
        self,
        rag_pipeline: "RAGPipeline",
        groq_client: "Groq"
    ):
        self.rag_pipeline = rag_pipeline
        self.client = groq_client

    # ============================================================
    # Utility - Clean LLM JSON
    # ============================================================

    @staticmethod
    def clean_json_response(
        content: str
    ) -> str:
        """
        Removes Markdown code fences if
        the LLM accidentally returns them.
        """

        content = content.strip()

        if content.startswith("```json"):
            content = content[7:]

        elif content.startswith("```"):
            content = content[3:]

        if content.endswith("```"):
            content = content[:-3]

        return content.strip()

    # ============================================================
    # Placeholder
    # ============================================================

    def generate_review(
        self,
        question: str
    ):
        """
        Full review generation logic
        will be moved here after the
        review models are extracted
        from app.py.
        """

        raise NotImplementedError(
            "Review generation has not yet been moved "
            "from app.py."
        )