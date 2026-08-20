# ============================================================
# AI CODE REVIEW ASSISTANT
# backend/app.py
# ============================================================

import os
import json
from pathlib import Path
from typing import List, Dict, Any

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

from services.upload_service import UploadService

from services.review_service import ReviewService

from services.finding_validator import (
    FindingValidator
)

from models.review_models import (
    ReviewRequest,
    StructuredReview,
    FileAnalyzed
)


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

GROQ_API_KEY = os.getenv(
    "GROQ_API_KEY"
)

if not GROQ_API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY not found in .env"
    )


# ============================================================
# CONFIGURATION
# ============================================================

MODEL_NAME = "openai/gpt-oss-20b"

BASE_DIR = Path(
    __file__
).resolve().parent

UPLOAD_DIR = BASE_DIR / "uploads"

EXTRACT_DIR = BASE_DIR / "extracted"

UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True
)

EXTRACT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# GROQ CLIENT
# ============================================================

client = Groq(
    api_key=GROQ_API_KEY
)


# ============================================================
# RAG PIPELINE
# ============================================================

rag_pipeline = RAGPipeline()


# ============================================================
# SERVICES
# ============================================================

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
# FASTAPI
# ============================================================

app = FastAPI(
    title="AI Code Review Assistant",
    description=(
        "RAG-powered AI code review system "
        "for bugs, security, performance, "
        "and code quality analysis."
    ),
    version="1.6.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"]
)


# ============================================================
# REQUEST MODEL
# ============================================================

class PasteCodeRequest(BaseModel):

    filename: str

    code: str


# ============================================================
# GROQ JSON SCHEMA
# ============================================================

def build_groq_schema(
    model: Any
) -> dict:
    """
    Build a Groq-compatible strict JSON schema from a Pydantic model.

    Groq strict JSON-schema mode requires every property of every
    object to appear in that object's `required` array.

    Pydantic optional fields are therefore kept nullable through their
    existing `anyOf: [<type>, {"type": "null"}]` representation, while
    the field itself is still listed as required.

    This is the key distinction:

        required != non-null

    A field can be required while accepting null.
    """

    raw_schema = model.model_json_schema()
    definitions = raw_schema.get("$defs", {})

    def resolve_reference(value: Any) -> Any:
        if isinstance(value, dict):
            if "$ref" in value:
                reference = value["$ref"]
                prefix = "#/$defs/"

                if reference.startswith(prefix):
                    name = reference[len(prefix):]

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

    resolved_schema = resolve_reference(raw_schema)

    def sanitize(value: Any) -> Any:
        if isinstance(value, list):
            return [
                sanitize(item)
                for item in value
            ]

        if not isinstance(value, dict):
            return value

        # ----------------------------------------------------
        # OBJECT
        # ----------------------------------------------------
        if value.get("type") == "object":
            properties = value.get("properties", {})

            # Groq strict mode requires EVERY object property
            # to appear in `required`.
            #
            # Optional Pydantic fields remain optional in value
            # semantics because their schema still contains null.
            required = [
                key
                for key in properties.keys()
                if key not in {
                    "user_requirements",
                    "corrected_code",
                    }
                ]

            return {
                "type": "object",
                "properties": {
                    key: sanitize(schema_value)
                    for key, schema_value
                    in properties.items()
                },
                "required": required,
                "additionalProperties": False
            }

        # ----------------------------------------------------
        # ARRAY
        # ----------------------------------------------------
        if value.get("type") == "array":
            result = {
                "type": "array"
            }

            if "items" in value:
                result["items"] = sanitize(
                    value["items"]
                )

            return result

        # ----------------------------------------------------
        # ANY OF
        # ----------------------------------------------------
        if "anyOf" in value:
            return {
                "anyOf": [
                    sanitize(item)
                    for item in value["anyOf"]
                ]
            }

        # ----------------------------------------------------
        # ONE OF
        # ----------------------------------------------------
        if "oneOf" in value:
            return {
                "oneOf": [
                    sanitize(item)
                    for item in value["oneOf"]
                ]
            }

        # ----------------------------------------------------
        # ALL OF
        # ----------------------------------------------------
        if "allOf" in value:
            return {
                "allOf": [
                    sanitize(item)
                    for item in value["allOf"]
                ]
            }

        # ----------------------------------------------------
        # ENUM / PRIMITIVE
        # ----------------------------------------------------
        allowed_keys = {
            "type",
            "enum",
            "description",
            "const"
        }

        result = {}

        for key in allowed_keys:
            if key in value:
                result[key] = value[key]

        return result

    return sanitize(resolved_schema)


# ============================================================
# STRUCTURED REVIEW SCHEMA
# ============================================================

GROQ_REVIEW_SCHEMA = build_groq_schema(
    StructuredReview
)


# ============================================================
# DEBUG SCHEMA
# ============================================================

def print_schema_requirements(
    schema: Any,
    path: str = "root"
):
    """
    Print required fields recursively.

    This is useful for verifying that optional fields
    are not accidentally converted to required fields.
    """

    if not isinstance(
        schema,
        dict
    ):
        return

    if schema.get(
        "type"
    ) == "object":

        print(
            f"[SCHEMA] {path} "
            f"required = "
            f"{schema.get('required', [])}"
        )

        properties = schema.get(
            "properties",
            {}
        )

        for name, child in properties.items():

            print_schema_requirements(
                child,
                f"{path}.{name}"
            )

    elif schema.get(
        "type"
    ) == "array":

        if "items" in schema:

            print_schema_requirements(
                schema["items"],
                f"{path}[]"
            )

    elif "anyOf" in schema:

        for index, child in enumerate(
            schema["anyOf"]
        ):

            print_schema_requirements(
                child,
                f"{path}.anyOf[{index}]"
            )


print(
    "\n========== GROQ SCHEMA CHECK =========="
)

print_schema_requirements(
    GROQ_REVIEW_SCHEMA
)

print(
    "========================================\n"
)


# ============================================================
# CLEAN MODEL RESPONSE
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

        content = content[7:]

    elif content.startswith(
        "```"
    ):

        content = content[3:]

    if content.endswith(
        "```"
    ):

        content = content[:-3]

    return content.strip()


# ============================================================
# BUILD TRUSTED FILE LIST
# ============================================================

def build_trusted_files_analyzed(
    retrieved_chunks: List[Dict]
) -> List[FileAnalyzed]:

    files = []

    seen = set()

    for chunk in retrieved_chunks:

        file_name = (
            chunk.get("name")
            or chunk.get("file_name")
            or "Unknown"
        )

        path = (
            chunk.get("relative_path")
            or chunk.get("path")
            or file_name
        )

        language = (
            chunk.get("language")
            or "Unknown"
        )

        identity = (
            str(path)
            .replace("\\", "/")
            .lower()
        )

        if identity in seen:
            continue

        seen.add(identity)

        files.append(
            FileAnalyzed(
                file_name=str(
                    file_name
                ),
                path=str(
                    path
                ),
                language=str(
                    language
                )
            )
        )

    return files


# ============================================================
# BUILD TRUSTED PROJECT METADATA
# ============================================================

def build_trusted_project_info(
    retrieved_chunks: List[Dict],
    existing_metadata: Any
) -> dict:

    metadata = {}

    if isinstance(
        existing_metadata,
        dict
    ):

        metadata = existing_metadata

    trusted_files = (
        build_trusted_files_analyzed(
            retrieved_chunks
        )
    )

    languages = []

    for file_info in trusted_files:

        language = file_info.language

        if (
            language
            and language != "Unknown"
            and language not in languages
        ):

            languages.append(
                language
            )

    project_name = (
        metadata.get(
            "project_name"
        )
        or metadata.get(
            "name"
        )
        or "Current Project"
    )

    total_lines = metadata.get(
        "total_lines",
        0
    )

    try:

        total_lines = int(
            total_lines
        )

    except (
        TypeError,
        ValueError
    ):

        total_lines = 0

    return {
        "name": project_name,

        "languages": languages,

        "total_files": len(
            trusted_files
        ),

        "total_lines": total_lines
    }


# ============================================================
# BASIC FINDING VALIDATION
# ============================================================

def validate_findings(
    review: StructuredReview
) -> StructuredReview:

    # ========================================================
    # BUGS
    # ========================================================

    review.bugs = [
        bug
        for bug in review.bugs
        if (
            bug.file
            and bug.file.strip()
            and bug.evidence
            and bug.evidence.strip()
        )
    ]

    # ========================================================
    # ERRORS
    # ========================================================

    review.errors = [
        error
        for error in review.errors
        if (
            error.file
            and error.file.strip()
        )
    ]

    # ========================================================
    # SECURITY
    # ========================================================

    if review.security:

        review.security.issues_found = (
            len(
                review.security.issues
            )
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
    # SECURITY COUNT
    # ========================================================

    if review.security:

        review.security.issues_found = (
            len(
                review.security.issues
            )
        )

    # ========================================================
    # CONFIDENCE
    # ========================================================

    confidences = []

    # --------------------------------------------------------
    # Bugs
    # --------------------------------------------------------

    for finding in review.bugs:

        if finding.confidence > 0:

            confidences.append(
                finding.confidence
            )

    # --------------------------------------------------------
    # Errors
    # --------------------------------------------------------

    for finding in review.errors:

        if finding.confidence > 0:

            confidences.append(
                finding.confidence
            )

    # --------------------------------------------------------
    # Security
    # --------------------------------------------------------

    if review.security:

        for finding in (
            review.security.issues
        ):

            if (
                finding.confidence
                is not None
                and finding.confidence > 0
            ):

                confidences.append(
                    finding.confidence
                )

    # --------------------------------------------------------
    # Performance
    # --------------------------------------------------------

    if review.performance:

        for finding in (
            review.performance.issues
        ):

            if finding.confidence > 0:

                confidences.append(
                    finding.confidence
                )

    # --------------------------------------------------------
    # Average confidence
    # --------------------------------------------------------

    if confidences:

        review.confidence = round(
            sum(confidences)
            /
            len(confidences)
        )

    else:

        review.confidence = 0

    # ========================================================
    # SUMMARY
    # ========================================================

    total_findings = (
        len(review.bugs)
        +
        len(review.errors)
    )

    if review.security:

        total_findings += len(
            review.security.issues
        )

    if review.performance:

        total_findings += len(
            review.performance.issues
        )

    if review.code_quality:

        total_findings += (
            len(
                review.code_quality.observations
            )
            +
            len(
                review.code_quality.suggestions
            )
        )

    if not review.answer_summary:

        if total_findings == 0:

            review.answer_summary = (
                "The project was reviewed "
                "successfully. No supported "
                "issues were identified for "
                "the requested analysis."
            )

        else:

            review.answer_summary = (
                "The review identified "
                f"{total_findings} supported "
                "finding"
                + (
                    "s"
                    if total_findings != 1
                    else ""
                )
                + " across the requested "
                "analysis areas. See the "
                "detailed findings below."
            )

    # ========================================================
    # FINAL VERDICT
    # ========================================================

    if not review.final_verdict:

        if total_findings == 0:

            review.final_verdict = (
                "No supported issues were "
                "identified in the analyzed "
                "project."
            )

        else:

            review.final_verdict = (
                "The review identified "
                f"{total_findings} supported "
                "finding"
                + (
                    "s"
                    if total_findings != 1
                    else ""
                )
                + " across the requested "
                "analysis areas. The findings "
                "should be reviewed before "
                "production use."
            )

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

        "version": "1.6.0",

        "model": MODEL_NAME
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():

    vector_ready = False

    try:

        vector_ready = (
            rag_pipeline
            .vector_database_exists()
        )

    except Exception:

        vector_ready = False

    return {
        "success": True,

        "backend": "online",

        "rag_vector_database": (
            vector_ready
        ),

        "model": MODEL_NAME
    }


# ============================================================
# PROJECT INFO
# ============================================================

@app.get("/project-info")
def project_info():

    try:

        metadata = (
            rag_pipeline
            .get_project_metadata()
        )

        if not metadata:

            raise HTTPException(
                status_code=404,
                detail=(
                    "No project is currently "
                    "indexed."
                )
            )

        return {
            "success": True,
            "project": metadata
        }

    except HTTPException:
        raise

    except Exception as e:

        print(
            "Project Info Error:",
            repr(e)
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to retrieve "
                "project information."
            )
        )


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
                    "Please select a ZIP "
                    "project file."
                )
            )

        if not file.filename.lower().endswith(
            ".zip"
        ):

            raise HTTPException(
                status_code=400,
                detail=(
                    "Only ZIP project files "
                    "are supported."
                )
            )

        print(
            "\nLoading project..."
        )

        result = await (
            upload_service
            .process_zip_upload(
                file
            )
        )

        return result

    except HTTPException:
        raise

    except Exception as e:

        print(
            "Upload Project Error:",
            repr(e)
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    finally:

        try:
            await file.close()
        except Exception:
            pass


# ============================================================
# UPLOAD MULTIPLE FILES
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

        result = await (
            upload_service
            .process_multiple_files(
                files
            )
        )

        return result

    except HTTPException:
        raise

    except Exception as e:

        print(
            "Upload Files Error:",
            repr(e)
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
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

        filename = data.filename.strip()

        code = data.code

        if not filename:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Filename cannot be empty."
                )
            )

        if not code.strip():

            raise HTTPException(
                status_code=400,
                detail=(
                    "Code cannot be empty."
                )
            )

        print(
            "\nProcessing pasted code:",
            filename
        )

        result = (
            upload_service
            .process_paste_code(
                code=code,
                filename=filename
            )
        )

        return result

    except HTTPException:
        raise

    except Exception as e:

        print(
            "Paste Code Error:",
            repr(e)
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
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

        question = data.question.strip()

        if not question:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Review question "
                    "cannot be empty."
                )
            )

        # ====================================================
        # VECTOR DATABASE CHECK
        # ====================================================

        try:

            vector_exists = (
                rag_pipeline
                .vector_database_exists()
            )

        except AttributeError:

            vector_exists = True

        if not vector_exists:

            raise HTTPException(
                status_code=400,
                detail=(
                    "No project is currently "
                    "indexed. Upload or paste "
                    "code first."
                )
            )

        # ====================================================
        # REVIEW TYPE DETECTION
        # ====================================================

        try:

            detected_modes = (
                rag_pipeline
                .prompt_builder
                .detect_review_modes(
                    question
                )
            )

        except AttributeError:

            detected_modes = {
                "general"
            }

        print(
            "\nDetected Review Types:",
            detected_modes
        )

        # ====================================================
        # RETRIEVAL
        # ====================================================

        print(
            "\nRetrieving relevant code..."
        )

        try:

            retrieval = (
                rag_pipeline
                .retrieve_context(
                    query=question
                )
            )

        except AttributeError:

            retrieval = (
                rag_pipeline
                .retrieve(
                    question
                )
            )

        # ====================================================
        # NORMALIZE RETRIEVAL RESULT
        # ====================================================

        if isinstance(
            retrieval,
            dict
        ):

            retrieved_chunks = (
                retrieval.get(
                    "chunks",
                    []
                )
            )

            query_type = (
                retrieval.get(
                    "query_type",
                    "targeted"
                )
            )

        elif isinstance(
            retrieval,
            list
        ):

            retrieved_chunks = retrieval

            query_type = "targeted"

        else:

            retrieved_chunks = []

            query_type = "unknown"

        print(
            "\nReview Query Type:",
            query_type
        )

        print(
            "Retrieved Chunks:",
            len(
                retrieved_chunks
            )
        )

        # ====================================================
        # TRUSTED FILES
        # ====================================================

        trusted_files = (
            build_trusted_files_analyzed(
                retrieved_chunks
            )
        )

        print(
            "\n"
            "========== TRUSTED CURRENT FILES =========="
        )

        for file_info in trusted_files:

            print(
                file_info.file_name,
                "|",
                file_info.path,
                "|",
                file_info.language
            )

        print(
            "Trusted File Count:",
            len(trusted_files)
        )

        print(
            "===========================================\n"
        )

        if not retrieved_chunks:

            raise HTTPException(
                status_code=502,
                detail=(
                    "No relevant source code "
                    "was retrieved for this review."
                )
            )

        # ====================================================
        # PROJECT METADATA
        # ====================================================

        try:

            project_metadata = (
                rag_pipeline
                .get_project_metadata()
            )

        except AttributeError:

            project_metadata = {}

        # ====================================================
        # BUILD PROMPT
        # ====================================================

        print(
            "Generating review prompt..."
        )

        try:

            prompt = (
                rag_pipeline
                .prompt_builder
                .build_prompt(
                    query=question,
                    retrieved_chunks=(
                        retrieved_chunks
                    ),
                    project_metadata=(
                        project_metadata
                    )
                )
            )

        except AttributeError:

            prompt_parts = [
                "Perform a deep code review.",

                "\nUSER REVIEW QUESTION:\n"
                + question,

                "\nIMPORTANT RULES:",

                "\n- Analyze ONLY the supplied code.",

                "\n- Do not invent findings.",

                "\n- Every finding must have "
                "source evidence.",

                "\n- Report exact file names.",

                "\n- Report accurate line numbers.",

                "\n- Security findings must "
                "include evidence.",

                "\n\nSOURCE CODE:"
            ]

            for index, chunk in enumerate(
                retrieved_chunks,
                start=1
            ):

                file_name = chunk.get(
                    "name",
                    "Unknown"
                )

                content = (
                    chunk.get(
                        "numbered_content"
                    )
                    or
                    chunk.get(
                        "content",
                        ""
                    )
                )

                prompt_parts.append(
                    f"\n\n===== FILE {index}: "
                    f"{file_name} =====\n"
                )

                prompt_parts.append(
                    str(content)
                )

            prompt = "".join(
                prompt_parts
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
        # GROQ
        # ====================================================

        print(
            "\nSending review to Groq..."
        )

        response = (
            client
            .chat
            .completions
            .create(

                model=MODEL_NAME,

                temperature=0.1,

                reasoning_effort="low",

                response_format={
                    "type": "json_schema",

                    "json_schema": {

                        "name":
                            "structured_code_review",

                        "strict":
                            True,

                        "schema":
                            GROQ_REVIEW_SCHEMA
                    }
                },

                messages=[

                    {
                        "role": "system",

                        "content": (
                            "You are a senior "
                            "software engineer and "
                            "security reviewer.\n\n"

                            "Perform a grounded code "
                            "review using ONLY the "
                            "source code supplied "
                            "in the user message.\n\n"

                            "Do not use previous "
                            "reviews or memory.\n\n"

                            "Do not invent files, "
                            "line numbers, code, "
                            "methods, classes, "
                            "libraries, or "
                            "vulnerabilities.\n\n"

                            "Every finding must be "
                            "supported by actual "
                            "source code.\n\n"

                            "For BUGS report runtime "
                            "errors, logical errors, "
                            "boundary errors, "
                            "incorrect algorithms, "
                            "and control-flow "
                            "problems.\n\n"

                            "For SECURITY report "
                            "only vulnerabilities "
                            "actually supported "
                            "by the source.\n\n"

                            "For PERFORMANCE report "
                            "actual algorithmic "
                            "or resource problems "
                            "supported by code.\n\n"

                            "For CODE QUALITY report "
                            "maintainability and "
                            "readability issues "
                            "supported by code.\n\n"

                            "Do not report a finding "
                            "merely because a pattern "
                            "looks suspicious.\n\n"

                            "Use exact evidence from "
                            "the supplied source "
                            "whenever available.\n\n"

                            "Be precise rather than "
                            "verbose."
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
        # MODEL RESPONSE
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
                    "The AI model returned "
                    "an empty response."
                )
            )

        print(
            "\nStructured AI response received."
        )

        # ====================================================
        # CLEAN RESPONSE
        # ====================================================

        cleaned_answer = (
            clean_json_response(
                raw_answer
            )
        )

        # ====================================================
        # PARSE JSON
        # ====================================================

        try:

            review_json = json.loads(
                cleaned_answer
            )

        except json.JSONDecodeError as e:

            print(
                "\n"
                "========== INVALID AI JSON =========="
            )

            print(
                cleaned_answer
            )

            print(
                "\nJSON ERROR:",
                str(e)
            )

            print(
                "=====================================\n"
            )

            raise HTTPException(
                status_code=502,
                detail=(
                    "The AI model returned "
                    "invalid JSON."
                )
            )

        # ====================================================
        # TRUSTED FILE OVERRIDE
        # ====================================================

        review_json[
            "files_analyzed"
        ] = [
            file_info.model_dump()
            for file_info
            in trusted_files
        ]

        # ====================================================
        # TRUSTED PROJECT OVERRIDE
        # ====================================================

        review_json[
            "project"
        ] = build_trusted_project_info(
            retrieved_chunks,
            project_metadata
        )

        # ====================================================
        # TRUSTED QUESTION
        # ====================================================

        review_json[
            "question"
        ] = question

        # ====================================================
        # TRUSTED REVIEW TYPES
        # ====================================================

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
                "\n"
                "========== REVIEW VALIDATION ERROR =========="
            )

            print(e)

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

            print(
                "=============================================\n"
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
        # BASIC VALIDATION
        # ====================================================

        validated_review = (
            validate_findings(
                validated_review
            )
        )

        # ====================================================
        # EVIDENCE VALIDATION
        # ====================================================

        print(
            "\nStarting evidence validation..."
        )

        finding_validator = FindingValidator(
            retrieved_chunks=retrieved_chunks
        )

        validated_review = (
            finding_validator
            .validate_review(
                validated_review
            )
        )

        print(
            "Evidence validation completed."
        )

        # ====================================================
        # NORMALIZE
        # ====================================================

        validated_review = (
            normalize_review(
                review=validated_review,
                question=question
            )
        )

        # ====================================================
        # FINAL TRUSTED FILE OVERRIDE
        # ====================================================

        validated_review.files_analyzed = (
            trusted_files
        )

        # ====================================================
        # FINAL COUNTS
        # ====================================================

        print(
            "\n"
            "========== FINAL REVIEW =========="
        )

        print(
            "Files:",
            len(
                validated_review.files_analyzed
            )
        )

        print(
            "Bugs:",
            len(
                validated_review.bugs
            )
        )

        print(
            "Errors:",
            len(
                validated_review.errors
            )
        )

        print(
            "Security:",
            (
                len(
                    validated_review
                    .security
                    .issues
                )
                if validated_review.security
                else 0
            )
        )

        print(
            "Performance:",
            (
                len(
                    validated_review
                    .performance
                    .issues
                )
                if validated_review.performance
                else 0
            )
        )

        print(
            "Confidence:",
            validated_review.confidence
        )

        print(
            "=================================\n"
        )

        # ====================================================
        # RESPONSE
        # ====================================================

        return {
            "success": True,

            "question": (
                validated_review.question
            ),

            "review_types": (
                validated_review.review_types
            ),

            "review": (
                validated_review.model_dump()
            )
        }

    # ========================================================
    # HTTP EXCEPTION
    # ========================================================

    except HTTPException:
        raise

    # ========================================================
    # GROQ / GENERAL ERROR
    # ========================================================

    except Exception as e:

        error_text = str(e)

        print(
            "\nReview Error:",
            repr(e)
        )

        # ----------------------------------------------------
        # MODEL NOT FOUND
        # ----------------------------------------------------

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
                    f"Configured model "
                    f"'{MODEL_NAME}' is "
                    "not available."
                )
            )

        # ----------------------------------------------------
        # JSON VALIDATION
        # ----------------------------------------------------

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
                    "generate a response "
                    "matching the required "
                    "structured review schema."
                )
            )

        # ----------------------------------------------------
        # RATE LIMIT
        # ----------------------------------------------------

        if (
            "rate_limit"
            in error_text.lower()

            or
            "429"
            in error_text
        ):

            raise HTTPException(
                status_code=429,
                detail=(
                    "AI model rate limit "
                    "reached. Please try "
                    "again shortly."
                )
            )

        # ----------------------------------------------------
        # AUTHENTICATION
        # ----------------------------------------------------

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
                    "Groq authentication "
                    "failed. Check "
                    "GROQ_API_KEY in .env."
                )
            )

        # ----------------------------------------------------
        # REQUEST TOO LARGE
        # ----------------------------------------------------

        if (
            "413"
            in error_text

            or
            "request too large"
            in error_text.lower()

            or
            "context length"
            in error_text.lower()
        ):

            raise HTTPException(
                status_code=413,
                detail=(
                    "The retrieved code "
                    "and review prompt "
                    "are too large for "
                    "the configured model."
                )
            )

        # ----------------------------------------------------
        # GENERIC
        # ----------------------------------------------------

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to generate "
                "code review."
            )
        )