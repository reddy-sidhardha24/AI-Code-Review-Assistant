# backend/app.py

import os
import json

from pathlib import Path
from typing import List, Optional, Literal

from dotenv import load_dotenv

from fastapi import (
    FastAPI,
    HTTPException,
    UploadFile,
    File
)


from fastapi.middleware.cors import CORSMiddleware

from pydantic import (
    BaseModel,
    Field,
    ValidationError
)

from groq import Groq

from rag.pipeline import RAGPipeline
from uploads.upload_service import UploadService
from services.review_service import ReviewService
from models.review_models import (
    ReviewRequest,
    StructuredReview,
    
)

# ============================================================
# Environment Variables
# ============================================================

load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY not found in .env"
    )


# ============================================================
# Groq Client
# ============================================================

client = Groq(
    api_key=API_KEY
)


# ============================================================
# RAG Pipeline
# ============================================================

rag_pipeline = RAGPipeline()

# ============================================================
# Directories
# ============================================================

UPLOAD_DIR = Path("uploads")

UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True
)


EXTRACT_DIR = Path("extracted")

EXTRACT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

upload_service = UploadService(
    upload_dir=UPLOAD_DIR,
    extract_dir=EXTRACT_DIR,
    rag_pipeline=rag_pipeline
)


review_service = ReviewService(
    rag_pipeline=rag_pipeline,
    groq_client=client
)


# ============================================================
# FastAPI Application
# ============================================================

app = FastAPI(
    title="AI Code Review Assistant",
    version="1.1.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# ============================================================
# Paste Code Request
# ============================================================

class PasteCodeRequest(BaseModel):

    filename: str

    code: str


# ============================================================
# Utility - Clean LLM JSON
# ============================================================

def clean_json_response(
    content: str
) -> str:

    """
    Removes Markdown code fences if the model accidentally
    returns them.
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

def validate_findings(
    review: StructuredReview
) -> StructuredReview:

    """
    Performs additional backend verification.

    The LLM is not trusted blindly.
    Findings without evidence are removed.
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
# Home API
# ============================================================

@app.get("/")
def home():

    return {
        "success": True,
        "message": (
            "AI Code Review Assistant "
            "Backend Running Successfully"
        ),
        "version": "1.1.0"
    }


# ============================================================
# Project Information API
# ============================================================

@app.get("/project-info")
def project_info():

    metadata = (
        rag_pipeline.get_project_metadata()
    )

    if not metadata:

        raise HTTPException(
            status_code=404,
            detail="No project is currently indexed."
        )

    return {
        "success": True,
        "project": metadata
    }


# ============================================================
# Upload Project API
# ============================================================



@app.post("/upload-files")
async def upload_files(
    files: List[UploadFile] = File(...)
):
    try:

        return await upload_service.process_multiple_files(
            files
        )

    except HTTPException:
        raise

    except Exception as e:

        print(
            "Upload Files Error:",
            repr(e)
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to upload source files."
        )

    finally:

        for file in files:
            try:
                await file.close()
            except Exception:
                pass
            
@app.post("/paste-code")
def paste_code(
    data: PasteCodeRequest
):
    try:

        return upload_service.process_paste_code(
            code=data.code,
            filename=data.filename
        )

    except HTTPException:
        raise

    except Exception as e:

        print(
            "Paste Code Error:",
            repr(e)
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to process pasted code."
        )
# ============================================================
# Review Project API
# ============================================================

@app.post("/review")
def review_project(
    data: ReviewRequest
):

    try:

        # ----------------------------------------------------
        # Validate Question
        # ----------------------------------------------------

        question = (
            data.question.strip()
        )

        if not question:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Review question "
                    "cannot be empty."
                )
            )

        # ----------------------------------------------------
        # Check Vector Database
        # ----------------------------------------------------

        if not (
            rag_pipeline
            .vector_database_exists()
        ):

            raise HTTPException(
                status_code=400,
                detail=(
                    "Please upload a "
                    "project first."
                )
            )

        # ----------------------------------------------------
        # Detect Review Intent
        # ----------------------------------------------------

        detected_modes = (
            rag_pipeline
            .prompt_builder
            .detect_review_modes(
                question
            )
        )

        print(
            "\nDetected Review Types:",
            detected_modes
        )

        # ----------------------------------------------------
        # Generate Dynamic RAG Prompt
        # ----------------------------------------------------

        prompt = (
            rag_pipeline.generate_prompt(
                question
            )
        )

        # ----------------------------------------------------
        # Debug Prompt Size
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # Safety Check
        #
        # This is intentionally conservative because your
        # Groq account already hit a 6000 TPM request limit.
        # ----------------------------------------------------

        if estimated_prompt_tokens > 5200:

            print(
                "WARNING: Prompt is becoming too large."
            )

        # ----------------------------------------------------
        # Groq Request
        # ----------------------------------------------------

        response = (
            client.chat.completions.create(

                model="llama-3.1-8b-instant",

                temperature=0.1,

                # Force JSON response where supported.
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
                            "code. Return one valid JSON "
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

        # ----------------------------------------------------
        # Extract Response
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # Clean JSON
        # ----------------------------------------------------

        cleaned_answer = (
            clean_json_response(
                raw_answer
            )
        )

        # ----------------------------------------------------
        # Parse JSON
        # ----------------------------------------------------

        try:

            review_json = json.loads(
                cleaned_answer
            )

        except json.JSONDecodeError as e:

            print(
                "\nINVALID GROQ JSON"
            )

            print(
                raw_answer
            )

            print(
                "\nJSON ERROR:"
            )

            print(
                str(e)
            )

            raise HTTPException(
                status_code=502,
                detail=(
                    "The AI model returned "
                    "invalid JSON."
                )
            )

        # ----------------------------------------------------
        # Make Review Types Reliable
        #
        # Do not blindly trust the LLM to correctly reproduce
        # something our backend already knows.
        # ----------------------------------------------------

        review_json[
            "review_types"
        ] = sorted(
            list(
                detected_modes
            )
        )

        # ----------------------------------------------------
        # Keep Original Question Reliable
        # ----------------------------------------------------

        review_json[
            "question"
        ] = question

        # ----------------------------------------------------
        # Validate Structure
        # ----------------------------------------------------

        try:

            validated_review = (
                StructuredReview
                .model_validate(
                    review_json
                )
            )

        except ValidationError as e:

            print(
                "\nREVIEW VALIDATION ERROR"
            )

            print(
                e
            )

            print(
                "\nRECEIVED JSON:"
            )

            print(
                json.dumps(
                    review_json,
                    indent=2
                )
            )

            raise HTTPException(
                status_code=502,
                detail=(
                    "The AI review did not "
                    "match the required "
                    "response structure."
                )
            )

        # ----------------------------------------------------
        # Evidence Validation
        # ----------------------------------------------------

        validated_review = (
            validate_findings(
                validated_review
            )
        )

        # ----------------------------------------------------
        # Enforce Dynamic Sections
        #
        # This prevents the model from filling irrelevant
        # sections for simple questions.
        # ----------------------------------------------------

        modes = set(
            validated_review.review_types
        )

        full_review = (
            "full_review" in modes
        )

        if (
            "performance" not in modes
            and not full_review
        ):
            validated_review.performance = None

        if (
            "security" not in modes
            and not full_review
        ):
            validated_review.security = None

        if (
            "code_quality" not in modes
            and not full_review
        ):
            validated_review.code_quality = None

        if (
            "output" not in modes
            and not full_review
        ):
            validated_review.expected_output = None

        # ----------------------------------------------------
        # Score Protection
        # ----------------------------------------------------

        score_keywords = [
            "score",
            "rating",
            "rate this",
            "code quality score",
            "project score"
        ]

        score_requested = any(
            keyword in question.lower()
            for keyword in score_keywords
        )

        if not score_requested:

            validated_review.score = None

        # ----------------------------------------------------
        # Final Response
        # ----------------------------------------------------

        return {
            "success": True,

            "question": question,

            "review_types": (
                validated_review
                .review_types
            ),

            "review": (
                validated_review
                .model_dump()
            )
        }

    except HTTPException:
        raise

    except Exception as e:

        # ----------------------------------------------------
        # Groq / Other API Errors
        # ----------------------------------------------------

        error_text = str(e)

        print(
            "\nReview Error:",
            error_text
        )

        # ----------------------------------------------------
        # Token / Request Size Problem
        # ----------------------------------------------------

        if (
            "413" in error_text
            or "Request too large" in error_text
            or "tokens per minute" in error_text
        ):

            raise HTTPException(
                status_code=413,
                detail=(
                    "The retrieved code and prompt are "
                    "too large for the current AI model "
                    "token limit. Reduce retrieved context "
                    "or try a more specific question."
                )
            )

        # ----------------------------------------------------
        # Rate Limit
        # ----------------------------------------------------

        if (
            "429" in error_text
            or "rate_limit" in error_text.lower()
        ):

            raise HTTPException(
                status_code=429,
                detail=(
                    "AI model rate limit reached. "
                    "Please try again shortly."
                )
            )

        # ----------------------------------------------------
        # Generic Failure
        # ----------------------------------------------------

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to generate "
                "code review."
            )
        )