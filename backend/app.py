# ============================================================
# AI CODE REVIEW ASSISTANT
# backend/app.py
# ============================================================

import os
import json

from pathlib import Path
from typing import List, Any

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
    ValidationError
)

from groq import Groq

from rag.pipeline import RAGPipeline

from uploads.upload_service import UploadService

from services.review_service import ReviewService

from models.review_models import (
    ReviewRequest,
    StructuredReview
)


# ============================================================
# ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY not found in .env"
    )


# ============================================================
# GROQ CLIENT
# ============================================================

client = Groq(
    api_key=API_KEY
)


# ============================================================
# RAG PIPELINE
# ============================================================

rag_pipeline = RAGPipeline()


# ============================================================
# DIRECTORIES
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
# UPLOAD SERVICE
# ============================================================

upload_service = UploadService(
    upload_dir=UPLOAD_DIR,
    extract_dir=EXTRACT_DIR,
    rag_pipeline=rag_pipeline
)


# ============================================================
# REVIEW SERVICE
# ============================================================

review_service = ReviewService(
    rag_pipeline=rag_pipeline,
    groq_client=client
)


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="AI Code Review Assistant",
    version="1.3.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"]
)


# ============================================================
# PASTE CODE REQUEST
# ============================================================

class PasteCodeRequest(BaseModel):

    filename: str

    code: str


# ============================================================
# GROQ STRICT JSON SCHEMA
# ============================================================

def build_groq_schema(
    model: Any
) -> dict:
    """
    Convert a Pydantic model schema into a schema
    compatible with Groq Strict Structured Outputs.

    Important Groq requirements:

    - Every object must have:
        additionalProperties: false

    - Every property must be required.

    - Optional Pydantic fields are represented using
      null through anyOf.

    - Pydantic constraints that are not necessary for
      generation are removed.

    The final response is still validated by Pydantic.
    """

    raw_schema = model.model_json_schema()

    definitions = raw_schema.get(
        "$defs",
        {}
    )


    # ========================================================
    # RESOLVE $REF
    # ========================================================

    def resolve_reference(
        value: Any
    ) -> Any:

        if isinstance(value, dict):

            if "$ref" in value:

                reference = value["$ref"]

                prefix = "#/$defs/"

                if reference.startswith(prefix):

                    name = reference[
                        len(prefix):
                    ]

                    if name in definitions:

                        return resolve_reference(
                            definitions[name]
                        )

                return {}


            return {
                key: resolve_reference(item)
                for key, item in value.items()
                if key != "$defs"
            }


        if isinstance(value, list):

            return [
                resolve_reference(item)
                for item in value
            ]


        return value


    schema = resolve_reference(
        raw_schema
    )


    # ========================================================
    # SANITIZE SCHEMA FOR GROQ
    # ========================================================

    allowed_keys = {
        "type",
        "properties",
        "required",
        "items",
        "enum",
        "anyOf",
        "oneOf",
        "description"
    }


    def sanitize(
        value: Any
    ) -> Any:

        if isinstance(value, list):

            return [
                sanitize(item)
                for item in value
            ]


        if not isinstance(
            value,
            dict
        ):

            return value


        result = {}


        # ----------------------------------------------------
        # OBJECT
        # ----------------------------------------------------

        if value.get("type") == "object":

            result["type"] = "object"

            properties = value.get(
                "properties",
                {}
            )

            result["properties"] = {

                key: sanitize(
                    property_schema
                )

                for key, property_schema
                in properties.items()

            }

            # Groq strict mode requires every
            # property to be required.

            result["required"] = list(
                properties.keys()
            )

            result[
                "additionalProperties"
            ] = False

            if "description" in value:

                result["description"] = (
                    value["description"]
                )

            return result


        # ----------------------------------------------------
        # ARRAY
        # ----------------------------------------------------

        if value.get("type") == "array":

            result["type"] = "array"

            if "items" in value:

                result["items"] = sanitize(
                    value["items"]
                )

            if "description" in value:

                result["description"] = (
                    value["description"]
                )

            return result


        # ----------------------------------------------------
        # UNION / OPTIONAL
        # ----------------------------------------------------

        if "anyOf" in value:

            result["anyOf"] = [

                sanitize(item)

                for item in value["anyOf"]

            ]

            if "description" in value:

                result["description"] = (
                    value["description"]
                )

            return result


        # ----------------------------------------------------
        # ENUM / PRIMITIVE
        # ----------------------------------------------------

        for key in allowed_keys:

            if key in value:

                result[key] = sanitize(
                    value[key]
                )


        return result


    return sanitize(
        schema
    )


# ============================================================
# BUILD REVIEW SCHEMA ONCE
# ============================================================

GROQ_REVIEW_SCHEMA = build_groq_schema(
    StructuredReview
)


# ============================================================
# CLEAN LLM JSON
# ============================================================

def clean_json_response(
    content: str
) -> str:

    if not content:

        return ""

    content = content.strip()


    if content.startswith(
        "```json"
    ):

        content = content[
            len("```json"):
        ]


    elif content.startswith(
        "```"
    ):

        content = content[
            len("```"):
        ]


    if content.endswith(
        "```"
    ):

        content = content[
            :-len("```")
        ]


    return content.strip()


# ============================================================
# VALIDATE FINDINGS
# ============================================================

def validate_findings(
    review: StructuredReview
) -> StructuredReview:

    # ========================================================
    # BUGS
    # ========================================================

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


    # ========================================================
    # ERRORS
    # ========================================================

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


    # ========================================================
    # SECURITY COUNT
    # ========================================================

    if review.security:

        review.security.issues_found = len(
            review.security.issues
        )


    return review


# ============================================================
# NORMALIZE REVIEW
# ============================================================

def normalize_review(
    review: StructuredReview,
    question: str
) -> StructuredReview:

    # ========================================================
    # SUMMARY FALLBACK
    # ========================================================

    if not review.answer_summary.strip():

        bug_count = len(
            review.bugs
        )

        error_count = len(
            review.errors
        )

        security_count = 0

        if review.security:

            security_count = len(
                review.security.issues
            )


        performance_count = 0

        if review.performance:

            performance_count = len(
                review.performance.issues
            )


        quality_count = 0

        if review.code_quality:

            quality_count = (

                len(
                    review.code_quality.observations
                )

                +

                len(
                    review.code_quality.suggestions
                )

            )


        findings = []


        if bug_count:

            findings.append(
                f"{bug_count} bug"
                + (
                    "s"
                    if bug_count != 1
                    else ""
                )
            )


        if error_count:

            findings.append(
                f"{error_count} error"
                + (
                    "s"
                    if error_count != 1
                    else ""
                )
            )


        if security_count:

            findings.append(
                f"{security_count} security issue"
                + (
                    "s"
                    if security_count != 1
                    else ""
                )
            )


        if performance_count:

            findings.append(
                f"{performance_count} performance concern"
                + (
                    "s"
                    if performance_count != 1
                    else ""
                )
            )


        if quality_count:

            findings.append(
                f"{quality_count} code-quality finding"
                + (
                    "s"
                    if quality_count != 1
                    else ""
                )
            )


        if findings:

            review.answer_summary = (
                "The review identified "
                + ", ".join(findings)
                + ". See the detailed findings below."
            )

        else:

            review.answer_summary = (
                "The project was reviewed successfully. "
                "No supported issues were identified "
                "for the requested analysis."
            )


    # ========================================================
    # FINAL VERDICT FALLBACK
    # ========================================================

    if not review.final_verdict.strip():

        security_count = 0

        if review.security:

            security_count = len(
                review.security.issues
            )


        performance_count = 0

        if review.performance:

            performance_count = len(
                review.performance.issues
            )


        quality_count = 0

        if review.code_quality:

            quality_count = (

                len(
                    review.code_quality.observations
                )

                +

                len(
                    review.code_quality.suggestions
                )

            )


        total_findings = (

            len(review.bugs)

            +

            len(review.errors)

            +

            security_count

            +

            performance_count

            +

            quality_count

        )


        if total_findings == 0:

            review.final_verdict = (
                "No supported issues were identified "
                "in the analyzed project."
            )

        else:

            review.final_verdict = (

                f"The review identified "
                f"{total_findings} supported finding"

                +

                (
                    "s"
                    if total_findings != 1
                    else ""
                )

                +

                " across the requested analysis areas. "
                "The highest-severity findings should be "
                "addressed before production use."

            )


    # ========================================================
    # SECURITY COUNT
    # ========================================================

    if review.security:

        review.security.issues_found = len(
            review.security.issues
        )


    # ========================================================
    # METHODS
    # ========================================================

    review.key_methods = list(
        dict.fromkeys(

            method.strip()

            for method in review.key_methods

            if isinstance(
                method,
                str
            )

            and method.strip()

        )
    )


    # ========================================================
    # CLASSES
    # ========================================================

    review.key_classes = list(
        dict.fromkeys(

            item.strip()

            for item in review.key_classes

            if isinstance(
                item,
                str
            )

            and item.strip()

        )
    )


    # ========================================================
    # LIBRARIES
    # ========================================================

    review.libraries = list(
        dict.fromkeys(

            item.strip()

            for item in review.libraries

            if isinstance(
                item,
                str
            )

            and item.strip()

        )
    )


    # ========================================================
    # PERFORMANCE CONSISTENCY
    # ========================================================

    if review.performance:

        performance_text = ""


        for issue in (
            review.performance.issues
        ):

            performance_text += (
                " "
                + (
                    issue.title
                    or ""
                )
            )

            performance_text += (
                " "
                + (
                    issue.description
                    or ""
                )
            )

            performance_text += (
                " "
                + (
                    issue.evidence
                    or ""
                )
            )


        performance_text = (
            performance_text.lower()
        )


        quadratic_indicators = [

            "o(n^2)",

            "o(n²)",

            "quadratic",

            "nested loop",

            "nested loops",

            "quadratic time"

        ]


        quadratic_detected = any(

            indicator
            in performance_text

            for indicator
            in quadratic_indicators

        )


        if quadratic_detected:

            review.performance.time_complexity = (
                "O(n²)"
            )


    # ========================================================
    # CONFIDENCE
    # ========================================================

    confidences = []


    for bug in review.bugs:

        if bug.confidence > 0:

            confidences.append(
                bug.confidence
            )


    for error in review.errors:

        if error.confidence > 0:

            confidences.append(
                error.confidence
            )


    if review.performance:

        for issue in (
            review.performance.issues
        ):

            if issue.confidence > 0:

                confidences.append(
                    issue.confidence
                )


    if confidences:

        review.confidence = round(

            sum(confidences)

            /

            len(confidences)

        )


    elif (

        review.bugs

        or review.errors

        or (
            review.security
            and review.security.issues
        )

        or (
            review.performance
            and review.performance.issues
        )

        or (
            review.code_quality
            and (
                review.code_quality.observations
                or
                review.code_quality.suggestions
            )
        )

    ):

        review.confidence = 80


    else:

        review.confidence = 0


    # ========================================================
    # QUESTION
    # ========================================================

    review.question = question


    return review


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():

    return {

        "success": True,

        "message": (
            "AI Code Review Assistant "
            "Backend Running Successfully"
        ),

        "version": "1.3.0"

    }


# ============================================================
# PROJECT INFORMATION
# ============================================================

@app.get("/project-info")
def project_info():

    metadata = (
        rag_pipeline
        .get_project_metadata()
    )


    if not metadata:

        raise HTTPException(

            status_code=404,

            detail=(
                "No project is currently indexed."
            )

        )


    return {

        "success": True,

        "project": metadata

    }


# ============================================================
# UPLOAD PROJECT
# ============================================================

@app.post("/upload-project")
async def upload_project(
    file: UploadFile = File(...)
):

    try:

        if not file.filename:

            raise HTTPException(

                status_code=400,

                detail=(
                    "Please select a ZIP project."
                )

            )


        if not file.filename.lower().endswith(
            ".zip"
        ):

            raise HTTPException(

                status_code=400,

                detail=(
                    "Only ZIP project files are supported."
                )

            )


        return await (
            upload_service
            .process_zip_upload(
                file
            )
        )


    except HTTPException:

        raise


    except Exception as e:

        print(
            "Upload Project Error:",
            repr(e)
        )


        raise HTTPException(

            status_code=500,

            detail=(
                "Failed to upload project."
            )

        )


    finally:

        try:

            await file.close()

        except Exception:

            pass


# ============================================================
# UPLOAD MULTIPLE SOURCE FILES
# ============================================================

@app.post("/upload-files")
async def upload_files(
    files: List[UploadFile] = File(...)
):

    try:

        if not files:

            raise HTTPException(

                status_code=400,

                detail=(
                    "Please select at least "
                    "one source file."
                )

            )


        return await (
            upload_service
            .process_multiple_files(
                files
            )
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

            detail=(
                "Failed to upload source files."
            )

        )


    finally:

        for file in files:

            try:

                await file.close()

            except Exception:

                pass


# ============================================================
# PASTE CODE
# ============================================================

@app.post("/paste-code")
def paste_code(
    data: PasteCodeRequest
):

    try:

        filename = (
            data.filename.strip()
        )

        code = (
            data.code.strip()
        )


        if not filename:

            raise HTTPException(

                status_code=400,

                detail=(
                    "Filename cannot be empty."
                )

            )


        if not code:

            raise HTTPException(

                status_code=400,

                detail=(
                    "Code cannot be empty."
                )

            )


        return (
            upload_service
            .process_paste_code(
                code=code,
                filename=filename
            )
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

            detail=(
                "Failed to process pasted code."
            )

        )


# ============================================================
# REVIEW PROJECT
# ============================================================

@app.post("/review")
def review_project(
    data: ReviewRequest
):

    try:

        # ====================================================
        # QUESTION
        # ====================================================

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


        # ====================================================
        # VECTOR DATABASE
        # ====================================================

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


        # ====================================================
        # REVIEW TYPES
        # ====================================================

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


        # ====================================================
        # RAG PROMPT
        # ====================================================

        prompt = (

            rag_pipeline
            .generate_prompt(
                query=question
            )

        )


        print(
            "\nPrompt generated successfully."
        )


        print(
            "Prompt Characters:",
            len(prompt)
        )


        print(
            "Estimated Prompt Tokens:",
            len(prompt) // 4
        )


        # ====================================================
        # GROQ STRUCTURED OUTPUT
        # ====================================================

        response = (

            client
            .chat
            .completions
            .create(

                model=(
                    "openai/gpt-oss-20b"
                ),

                temperature=0.1,

                reasoning_effort="low",

                response_format={

                    "type": "json_schema",

                    "json_schema": {

                        "name": (
                            "structured_code_review"
                        ),

                        "strict": True,

                        "schema": (
                            GROQ_REVIEW_SCHEMA
                        )

                    }

                },

                messages=[

                    {

                        "role": "system",

                        "content": (

                            "You are an expert senior "
                            "software engineer performing "
                            "a grounded project-wide code "
                            "review. "

                            "Analyze ONLY the supplied "
                            "project metadata and retrieved "
                            "source code. "

                            "Every finding must be grounded "
                            "in the supplied code. "

                            "Do not invent files, line "
                            "numbers, methods, classes, "
                            "libraries, or vulnerabilities. "

                            "If an analysis category has "
                            "no supported finding, return "
                            "an empty array for that category. "

                            "Return the complete structured "
                            "review required by the supplied "
                            "schema."

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
        # RAW RESPONSE
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
            "\nStructured AI response received."
        )


        # ====================================================
        # CLEAN
        # ====================================================

        cleaned_answer = (

            clean_json_response(
                raw_answer
            )

        )


        # ====================================================
        # PARSE
        # ====================================================

        try:

            review_json = json.loads(
                cleaned_answer
            )


        except json.JSONDecodeError as e:

            print(
                "\nINVALID GROQ JSON"
            )


            print(
                cleaned_answer
            )


            print(
                "\nJSON ERROR:",
                str(e)
            )


            raise HTTPException(

                status_code=502,

                detail=(
                    "The AI model returned "
                    "invalid JSON."
                )

            )


        # ====================================================
        # FORCE TRUSTED APPLICATION FIELDS
        # ====================================================

        review_json[
            "question"
        ] = question


        review_json[
            "review_types"
        ] = sorted(
            list(
                detected_modes
            )
        )


        # ====================================================
        # PYDANTIC VALIDATION
        # ====================================================

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
                    indent=2,
                    ensure_ascii=False
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


        # ====================================================
        # FINDING VALIDATION
        # ====================================================

        validated_review = (

            validate_findings(
                validated_review
            )

        )


        # ====================================================
        # NORMALIZATION
        # ====================================================

        validated_review = (

            normalize_review(

                review=validated_review,

                question=question

            )

        )


        # ====================================================
        # REVIEW MODES
        # ====================================================

        modes = set(
            validated_review.review_types
        )


        full_review = (
            "full_review"
            in modes
        )


        # ====================================================
        # PERFORMANCE
        # ====================================================

        if (

            "performance"
            not in modes

            and not full_review

        ):

            validated_review.performance = None


        # ====================================================
        # SECURITY
        # ====================================================

        if (

            "security"
            not in modes

            and not full_review

        ):

            validated_review.security = None


        # ====================================================
        # CODE QUALITY
        # ====================================================

        if (

            "code_quality"
            not in modes

            and not full_review

        ):

            validated_review.code_quality = None


        # ====================================================
        # EXPECTED OUTPUT
        # ====================================================

        if (

            "output"
            not in modes

            and not full_review

        ):

            validated_review.expected_output = None


        # ====================================================
        # SCORE PROTECTION
        # ====================================================

        score_keywords = [

            "score",

            "rating",

            "rate this",

            "code quality score",

            "project score"

        ]


        score_requested = any(

            keyword
            in question.lower()

            for keyword
            in score_keywords

        )


        if not score_requested:

            validated_review.score = None


        # ====================================================
        # FINAL NORMALIZATION
        # ====================================================

        validated_review = (

            normalize_review(

                review=validated_review,

                question=question

            )

        )


        # ====================================================
        # RESPONSE
        # ====================================================

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


    # ========================================================
    # HTTP EXCEPTIONS
    # ========================================================

    except HTTPException:

        raise


    # ========================================================
    # GROQ / GENERAL ERRORS
    # ========================================================

    except Exception as e:

        error_text = str(e)

        print(
            "\nReview Error:",
            repr(e)
        )


        # ====================================================
        # GROQ STRUCTURED OUTPUT ERROR
        # ====================================================

        if (
            "json_validate_failed"
            in error_text.lower()

            or

            "failed to validate json"
            in error_text.lower()

        ):

            raise HTTPException(

                status_code=502,

                detail=(

                    "The AI model could not "
                    "generate a response matching "
                    "the structured review schema."

                )

            )


        # ====================================================
        # RATE LIMIT
        # ====================================================

        if (

            "429"
            in error_text

            or

            "rate_limit"
            in error_text.lower()

        ):

            raise HTTPException(

                status_code=429,

                detail=(

                    "AI model rate limit reached. "
                    "Please try again shortly."

                )

            )


        # ====================================================
        # AUTHENTICATION
        # ====================================================

        if (

            "401"
            in error_text

            or

            "authentication"
            in error_text.lower()

            or

            "invalid api key"
            in error_text.lower()

        ):

            raise HTTPException(

                status_code=502,

                detail=(

                    "AI provider authentication failed. "
                    "Check GROQ_API_KEY in .env."

                )

            )


        # ====================================================
        # MODEL NOT FOUND
        # ====================================================

        if (

            "model_not_found"
            in error_text.lower()

            or

            "does not exist"
            in error_text.lower()

        ):

            raise HTTPException(

                status_code=502,

                detail=(

                    "The configured Groq model is "
                    "not available to this API key."

                )

            )


        # ====================================================
        # REQUEST TOO LARGE
        # ====================================================

        if (

            "413"
            in error_text

            or

            "request too large"
            in error_text.lower()

        ):

            raise HTTPException(

                status_code=413,

                detail=(

                    "The retrieved code and prompt "
                    "are too large for the current "
                    "AI model limit."

                )

            )


        # ====================================================
        # GENERIC
        # ====================================================

        raise HTTPException(

            status_code=500,

            detail=(
                "Failed to generate "
                "code review."
            )

        )