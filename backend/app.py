# backend/app.py

import os
import json
import shutil
import zipfile
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


# ============================================================
# Request Model
# ============================================================

class ReviewRequest(BaseModel):

    question: str = Field(
        min_length=1,
        max_length=2000
    )


# ============================================================
# Project Information
# ============================================================

class ProjectInfo(BaseModel):

    name: Optional[str] = None

    languages: List[str] = Field(
        default_factory=list
    )

    total_files: int = Field(
        default=0,
        ge=0
    )

    total_lines: int = Field(
        default=0,
        ge=0
    )


# ============================================================
# File Analyzed
# ============================================================

class FileAnalyzed(BaseModel):

    file_name: str

    path: str

    language: str


# ============================================================
# Bug Finding
# ============================================================

class BugFinding(BaseModel):

    title: str

    type: Literal[
        "confirmed",
        "conditional",
        "possible_risk"
    ]

    severity: Literal[
        "critical",
        "high",
        "medium",
        "low"
    ]

    file: str

    line: Optional[int] = None

    line_range: Optional[str] = None

    evidence: str

    description: str

    impact: str

    fix: str

    confidence: int = Field(
        default=0,
        ge=0,
        le=100
    )


# ============================================================
# Error Finding
# ============================================================

class ErrorFinding(BaseModel):

    type: str

    title: str

    file: str

    line: Optional[int] = None

    line_range: Optional[str] = None

    evidence: str = ""

    description: str

    impact: str = ""

    fix: str

    confidence: int = Field(
        default=0,
        ge=0,
        le=100
    )


# ============================================================
# Performance
# ============================================================

class PerformanceIssue(BaseModel):

    title: str = ""

    description: str = ""

    file: str = ""

    line: Optional[int] = None

    line_range: Optional[str] = None

    evidence: str = ""

    impact: str = ""

    suggestion: str = ""

    confidence: int = Field(
        default=0,
        ge=0,
        le=100
    )


class PerformanceInfo(BaseModel):

    time_complexity: str = ""

    space_complexity: str = ""

    issues: List[PerformanceIssue] = Field(
        default_factory=list
    )


# ============================================================
# Security
# ============================================================

class SecurityInfo(BaseModel):

    issues_found: int = Field(
        default=0,
        ge=0
    )

    issues: List[str] = Field(
        default_factory=list
    )


# ============================================================
# Code Quality
# ============================================================

class CodeQualityInfo(BaseModel):

    observations: List[str] = Field(
        default_factory=list
    )

    suggestions: List[str] = Field(
        default_factory=list
    )


# ============================================================
# Structured Review
# ============================================================

class StructuredReview(BaseModel):

    project: ProjectInfo

    question: str

    # New field from dynamic PromptBuilder
    review_types: List[str] = Field(
        default_factory=list
    )

    answer_summary: str = ""

    files_analyzed: List[FileAnalyzed] = Field(
        default_factory=list
    )

    bugs: List[BugFinding] = Field(
        default_factory=list
    )

    errors: List[ErrorFinding] = Field(
        default_factory=list
    )

    # --------------------------------------------------------
    # These are now Optional.
    #
    # Explanation-only questions should NOT be forced to
    # generate meaningless performance/security sections.
    # --------------------------------------------------------

    performance: Optional[
        PerformanceInfo
    ] = None

    security: Optional[
        SecurityInfo
    ] = None

    code_quality: Optional[
        CodeQualityInfo
    ] = None

    key_methods: List[str] = Field(
        default_factory=list
    )

    key_classes: List[str] = Field(
        default_factory=list
    )

    libraries: List[str] = Field(
        default_factory=list
    )

    expected_output: Optional[str] = None

    score: Optional[float] = None

    confidence: int = Field(
        default=0,
        ge=0,
        le=100
    )

    final_verdict: str = ""


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

@app.post("/upload-project")
async def upload_project(
    file: UploadFile = File(...)
):

    zip_path = None

    try:

        # ----------------------------------------------------
        # Validate Filename
        # ----------------------------------------------------

        if not file.filename:

            raise HTTPException(
                status_code=400,
                detail="Invalid file."
            )

        # ----------------------------------------------------
        # Validate Extension
        # ----------------------------------------------------

        if not file.filename.lower().endswith(
            ".zip"
        ):

            raise HTTPException(
                status_code=400,
                detail="Please upload a ZIP file."
            )

        # ----------------------------------------------------
        # Safe Filename
        # ----------------------------------------------------

        safe_filename = Path(
            file.filename
        ).name

        zip_path = (
            UPLOAD_DIR /
            safe_filename
        )

        # ----------------------------------------------------
        # Save ZIP
        # ----------------------------------------------------

        with open(
            zip_path,
            "wb"
        ) as buffer:

            shutil.copyfileobj(
                file.file,
                buffer
            )

        # ----------------------------------------------------
        # Validate ZIP
        # ----------------------------------------------------

        if not zipfile.is_zipfile(
            zip_path
        ):

            zip_path.unlink(
                missing_ok=True
            )

            raise HTTPException(
                status_code=400,
                detail=(
                    "Uploaded file is not "
                    "a valid ZIP archive."
                )
            )

        # ----------------------------------------------------
        # Project Name
        # ----------------------------------------------------

        project_name = Path(
            safe_filename
        ).stem

        project_folder = (
            EXTRACT_DIR /
            project_name
        )

        # ----------------------------------------------------
        # Remove Existing Extraction
        # ----------------------------------------------------

        if project_folder.exists():

            shutil.rmtree(
                project_folder
            )

        project_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        # ----------------------------------------------------
        # Safe ZIP Extraction
        # ----------------------------------------------------

        with zipfile.ZipFile(
            zip_path,
            "r"
        ) as zip_ref:

            extraction_root = (
                project_folder.resolve()
            )

            for member in zip_ref.infolist():

                target_path = (
                    project_folder /
                    member.filename
                ).resolve()

                try:

                    target_path.relative_to(
                        extraction_root
                    )

                except ValueError:

                    raise HTTPException(
                        status_code=400,
                        detail=(
                            "Unsafe file path detected "
                            "inside ZIP archive."
                        )
                    )

            zip_ref.extractall(
                project_folder
            )

        # ----------------------------------------------------
        # Build RAG Database
        # ----------------------------------------------------

        metadata = (
            rag_pipeline.build_vector_database(
                str(project_folder)
            )
        )

        # ----------------------------------------------------
        # Response
        # ----------------------------------------------------

        return {
            "success": True,
            "message": (
                "Project uploaded and "
                "indexed successfully."
            ),
            "project_name": project_name,
            "metadata": metadata
        }

    except HTTPException:
        raise

    except zipfile.BadZipFile:

        raise HTTPException(
            status_code=400,
            detail="Invalid or corrupted ZIP file."
        )

    except Exception as e:

        print(
            "Upload Error:",
            repr(e)
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to process "
                "uploaded project."
            )
        )

    finally:

        try:
            await file.close()
        except Exception:
            pass


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