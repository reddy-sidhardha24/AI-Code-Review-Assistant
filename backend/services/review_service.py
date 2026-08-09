import json
from typing import TYPE_CHECKING

from fastapi import HTTPException
from pydantic import ValidationError

from models.review_models import StructuredReview


if TYPE_CHECKING:
    from rag.pipeline import RAGPipeline
    from groq import Groq


class ReviewService:
    """
    Handles all AI review-related business logic.

    FastAPI routes should only:
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
        Removes Markdown code fences if the LLM
        accidentally returns them.
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
    # Utility - Validate Findings
    # ============================================================

    @staticmethod
    def validate_findings(
        review: StructuredReview
    ) -> StructuredReview:
        """
        Performs additional backend verification.

        The LLM is not trusted blindly.

        Findings without:
            - evidence
            - file

        are removed.
        """

        # --------------------------------------------------------
        # Validate Bugs
        # --------------------------------------------------------

        verified_bugs = []

        for bug in review.bugs:

            if not bug.evidence.strip():

                print(
                    "Rejected bug without evidence:",
                    bug.title
                )

                continue

            if not bug.file.strip():

                print(
                    "Rejected bug without file:",
                    bug.title
                )

                continue

            verified_bugs.append(
                bug
            )

        review.bugs = verified_bugs

        # --------------------------------------------------------
        # Validate Errors
        # --------------------------------------------------------

        verified_errors = []

        for error in review.errors:

            if not error.evidence.strip():

                print(
                    "Rejected error without evidence:",
                    error.title
                )

                continue

            if not error.file.strip():

                print(
                    "Rejected error without file:",
                    error.title
                )

                continue

            verified_errors.append(
                error
            )

        review.errors = verified_errors

        return review

    # ============================================================
    # Generate Review
    # ============================================================

    def generate_review(
        self,
        question: str
    ) -> StructuredReview:

        # --------------------------------------------------------
        # Validate Question
        # --------------------------------------------------------

        question = question.strip()

        if not question:

            raise HTTPException(
                status_code=400,
                detail="Review question cannot be empty."
            )

        # --------------------------------------------------------
        # Check Vector Database
        # --------------------------------------------------------

        if not self.rag_pipeline.vector_database_exists():

            raise HTTPException(
                status_code=400,
                detail="Please upload a project first."
            )

        try:

            # ====================================================
            # Detect Review Intent
            # ====================================================

            detected_modes = (
                self.rag_pipeline
                .prompt_builder
                .detect_review_modes(
                    question
                )
            )

            print(
                "\nDetected Review Types:",
                detected_modes
            )

            # ====================================================
            # Generate RAG Prompt
            # ====================================================

            print(
                "\nGenerating RAG prompt..."
            )

            prompt = (
                self.rag_pipeline
                .generate_prompt(
                    question
                )
            )

            # ====================================================
            # Prompt Size
            # ====================================================

            prompt_characters = len(
                prompt
            )

            estimated_prompt_tokens = max(
                1,
                prompt_characters // 4
            )

            print(
                "Prompt Characters:",
                prompt_characters
            )

            print(
                "Estimated Prompt Tokens:",
                estimated_prompt_tokens
            )

            if estimated_prompt_tokens > 5200:

                print(
                    "WARNING: Prompt is becoming too large."
                )

            # ====================================================
            # Groq Request
            # ====================================================

            print(
                "\nSending request to Groq..."
            )

            response = (
                self.client
                .chat
                .completions
                .create(

                    model="llama-3.1-8b-instant",

                    temperature=0.1,

                    response_format={
                        "type": "json_object"
                    },

                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are an expert senior "
                                "software engineer performing "
                                "grounded code analysis. "
                                "Use only the supplied project "
                                "metadata and retrieved source "
                                "code. "
                                "Do not invent files, lines, "
                                "bugs, or evidence. "
                                "Return exactly one valid JSON "
                                "object and no Markdown."
                            )
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )
            )

            # ====================================================
            # Extract Model Response
            # ====================================================

            raw_answer = (
                response
                .choices[0]
                .message
                .content
            )

            if not raw_answer:

                raise HTTPException(
                    status_code=502,
                    detail=(
                        "AI model returned "
                        "an empty response."
                    )
                )

            print(
                "\n========== RAW AI RESPONSE =========="
            )

            print(
                raw_answer
            )

            print(
                "====================================="
            )

            # ====================================================
            # Clean JSON
            # ====================================================

            cleaned_answer = (
                self.clean_json_response(
                    raw_answer
                )
            )

            # ====================================================
            # Parse JSON
            # ====================================================

            try:

                review_json = json.loads(
                    cleaned_answer
                )

            except json.JSONDecodeError as e:

                print(
                    "\n========== JSON PARSE ERROR =========="
                )

                print(
                    repr(e)
                )

                print(
                    "\nCleaned Response:"
                )

                print(
                    cleaned_answer
                )

                raise HTTPException(
                    status_code=502,
                    detail=(
                        "AI model returned "
                        "invalid JSON."
                    )
                )

            # ====================================================
            # Ensure Object
            # ====================================================

            if not isinstance(
                review_json,
                dict
            ):

                raise HTTPException(
                    status_code=502,
                    detail=(
                        "AI model returned an invalid "
                        "review object."
                    )
                )

            # ====================================================
            # Add Detected Review Types
            # ====================================================

            review_json.setdefault(
                "review_types",
                list(detected_modes)
            )

            review_json.setdefault(
                "question",
                question
            )

            # ====================================================
            # Validate Structured Review
            # ====================================================

            try:

                review = (
                    StructuredReview
                    .model_validate(
                        review_json
                    )
                )

            except ValidationError as e:

                print(
                    "\n========== REVIEW VALIDATION ERROR =========="
                )

                print(
                    e
                )

                print(
                    "\n========== AI REVIEW JSON =========="
                )

                print(
                    json.dumps(
                        review_json,
                        indent=2,
                        ensure_ascii=False
                    )
                )

                raise HTTPException(
                    status_code=502,
                    detail=(
                        "The AI review did not match "
                        "the required response structure."
                    )
                )

            # ====================================================
            # Backend Finding Validation
            # ====================================================

            review = (
                self.validate_findings(
                    review
                )
            )

            # ====================================================
            # Return Review
            # ====================================================

            print(
                "\nAI review generated successfully."
            )

            return review

        except HTTPException:
            raise

        except Exception as e:

            print(
                "\n========== REVIEW ERROR =========="
            )

            print(
                repr(e)
            )

            raise HTTPException(
                status_code=500,
                detail=(
                    "Failed to generate AI code review."
                )
            )