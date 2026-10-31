# ============================================================
# AI CODE REVIEW ASSISTANT
# backend/app.py
# ============================================================

import os
import json
import re
import hashlib
import threading
import time

from pathlib import Path
from typing import List, Any, Dict, Optional
import uuid

from dotenv import load_dotenv

from fastapi import (
    FastAPI,
    HTTPException,
    UploadFile,
    File,
    Request,
    Response
)
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from fastapi.middleware.cors import CORSMiddleware

from pydantic import (
    BaseModel,
    ValidationError
)
from langchain_core.output_parsers import PydanticOutputParser

from groq import Groq
import requests

from rag.pipeline import RAGPipeline

from uploads.upload_service import UploadService

from services.review_service import ReviewService
from services.email_service import email_service
from services.llm_service import LLMService
from services.github_app_service import GitHubAppService
from services.report_service import ReportService
from services.code_correction_service import CodeCorrectionService
from services.multi_agent_service import MultiAgentService

from models.review_models import (
    ReviewRequest,
    StructuredReview,
    FileAnalyzed,
    DetectedIssue,
    SendEmailRequest,
    SecurityInfo,
    SecurityFinding,
    PerformanceInfo,
    PerformanceIssue
)

from db.database import init_db
from db import crud
from services.security_service import (
    validate_uploaded_file,
    validate_file_extension,
    sanitize_filename,
    verify_clerk_token,
)



# Load .env from backend folder and current working directory
backend_env = Path(__file__).resolve().parent / ".env"
if backend_env.exists():
    load_dotenv(dotenv_path=backend_env)
load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY", "")
APP_ENV = os.getenv("APP_ENV", "production").strip().lower()

if not API_KEY:
    print("WARNING: GROQ_API_KEY not found in environment or .env file.")


# ============================================================
# GROQ CLIENT
# ============================================================

client = Groq(api_key=API_KEY or "gsk_placeholder")


# ============================================================
# DIRECTORIES
# ============================================================

BACKEND_ROOT = Path(__file__).resolve().parent
UPLOAD_DIR = BACKEND_ROOT / "uploads"

UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True
)


EXTRACT_DIR = BACKEND_ROOT / "extracted"

EXTRACT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

USER_DATA_DIR = BACKEND_ROOT / "data" / "users"


llm_service = LLMService(fallback_groq_key=API_KEY)
github_app_service = GitHubAppService()
report_service = ReportService()
code_correction_service = CodeCorrectionService()
multi_agent_service = MultiAgentService(llm_service)

_user_runtimes: Dict[str, Dict[str, Any]] = {}
_user_runtimes_lock = threading.Lock()
_review_cancellations: Dict[str, Dict[str, Any]] = {}
_review_cancellations_lock = threading.Lock()


def get_user_runtime(user_id: str) -> Dict[str, Any]:
    """Return an isolated upload, vector-index, and review runtime for a user."""
    with _user_runtimes_lock:
        runtime = _user_runtimes.get(user_id)
        if runtime is not None:
            return runtime

        user_key = hashlib.sha256(user_id.encode("utf-8")).hexdigest()
        data_root = USER_DATA_DIR / user_key
        user_extract_dir = EXTRACT_DIR / "users" / user_key
        pipeline = RAGPipeline(storage_dir=str(data_root / "vector_db"))
        runtime = {
            "rag_pipeline": pipeline,
            "upload_service": UploadService(
                upload_dir=data_root / "uploads",
                extract_dir=user_extract_dir,
                rag_pipeline=pipeline,
            ),
            "review_service": ReviewService(rag_pipeline=pipeline, groq_client=client),
            "extract_dir": user_extract_dir,
        }
        _user_runtimes[user_id] = runtime
        return runtime


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="AI Code Review Assistant",
    version="1.4.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.getenv(
            "CORS_ALLOWED_ORIGINS",
            "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000,http://127.0.0.1:8000",
        ).split(",")
        if origin.strip()
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
# GITHUB REQUEST
# ============================================================

class GithubRequest(BaseModel):

    repo_url: str


# ============================================================
# GROQ STRICT JSON SCHEMA
# ============================================================

def build_groq_schema(
    model: Any
) -> dict:
    """
    Convert Pydantic schema into Groq-compatible
    strict JSON schema.
    """

    raw_schema = model.model_json_schema()

    definitions = raw_schema.get(
        "$defs",
        {}
    )

    # ========================================================
    # RESOLVE REFERENCES
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
    # SANITIZE
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

            # Filter out backend-computed properties such as detected_issues and best_practices
            filtered_properties = {
                k: v for k, v in properties.items()
                if k not in ["detected_issues", "best_practices"]
            }

            result["properties"] = {
                key: sanitize(
                    property_schema
                )
                for key, property_schema
                in filtered_properties.items()
            }

            result["required"] = list(
                filtered_properties.keys()
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
        # UNION
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
# BUILD SCHEMA
# ============================================================

GROQ_REVIEW_SCHEMA = build_groq_schema(
    StructuredReview
)
review_output_parser = PydanticOutputParser(pydantic_object=StructuredReview)

# ============================================================
# CLEAN JSON
# ============================================================

def clean_json_response(
    content: str
) -> str:
    if not content:
        return "{}"

    content = content.strip()

    # Extract JSON inside markdown code blocks if present
    if "```json" in content:
        parts = content.split("```json")
        if len(parts) > 1:
            content = parts[1].split("```")[0]
    elif "```" in content:
        parts = content.split("```")
        if len(parts) > 1:
            content = parts[1].split("```")[0]

    content = content.strip()
    s_idx = content.find("{")
    e_idx = content.rfind("}")
    if s_idx != -1 and e_idx != -1 and e_idx > s_idx:
        content = content[s_idx:e_idx + 1]

    # Remove trailing commas before closing braces/brackets
    content = re.sub(r',\s*([}\]])', r'\1', content)
    return content.strip()



# ============================================================
# BUILD TRUSTED FILE LIST
# ============================================================

def build_trusted_files_analyzed(
    retrieved_chunks: List[Dict]
) -> List[FileAnalyzed]:
    """
    IMPORTANT:

    files_analyzed must NEVER come from the LLM.

    It is derived exclusively from the chunks that were
    actually retrieved for THIS review.

    This prevents stale filenames from previous projects
    appearing in the final response.
    """

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
            str(path).lower()
        )

        if identity in seen:

            continue

        seen.add(
            identity
        )

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
# BUILD TRUSTED PROJECT INFO
# ============================================================

def build_trusted_project_info(
    retrieved_chunks: List[Dict],
    existing_project: Any
):
    """
    Project information should preferably come from the
    current indexed project metadata.

    The LLM should not be trusted to invent project statistics.
    """

    metadata = {}

    if isinstance(
        existing_project,
        dict
    ):

        metadata = existing_project

    # --------------------------------------------------------
    # Files represented by CURRENT retrieval
    # --------------------------------------------------------

    trusted_files = (
        build_trusted_files_analyzed(
            retrieved_chunks
        )
    )

    # --------------------------------------------------------
    # Language fallback
    # --------------------------------------------------------

    languages = []

    for file in trusted_files:

        if (
            file.language
            and file.language != "Unknown"
            and file.language not in languages
        ):

            languages.append(
                file.language
            )

    metadata_languages = metadata.get(
        "languages",
        []
    )

    if isinstance(
        metadata_languages,
        dict
    ):

        metadata_languages = list(
            metadata_languages.keys()
        )

    if not languages:

        languages = (
            metadata_languages
            if isinstance(
                metadata_languages,
                list
            )
            else []
        )

    # --------------------------------------------------------
    # Project name
    # --------------------------------------------------------

    project_name = (
        metadata.get(
            "project_name"
        )
        or metadata.get(
            "name"
        )
        or "Current Project"
    )

    # --------------------------------------------------------
    # Total lines
    # --------------------------------------------------------

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
# NORMALIZE & SANITIZE RAW REVIEW JSON
# ============================================================

def is_dummy_finding(item: dict) -> bool:
    if not isinstance(item, dict):
        return True
    title = str(item.get("title") or item.get("bug_id") or item.get("error_id") or "").strip().lower()
    desc = str(item.get("description") or "").strip().lower()
    file_val = str(item.get("file") or item.get("file_name") or "").strip().lower()
    dummy_titles = {"title", "bug id", "error id", "problem identification", "name", "bug title", "method 1", "requirement 1"}
    dummy_files = {"file name", "file", "path/to/file", "filename", "path"}
    if title in dummy_titles or file_val in dummy_files:
        return True
    if desc in ("description", "desc", "what is broken", "explanation", "observations", "suggestions"):
        return True
    return False


def sanitize_raw_review_json(review_json: dict, default_file: str = "app.py") -> dict:
    if not isinstance(review_json, dict):
        return {}

    # 1. Clean BUGS
    clean_bugs = []
    for b in review_json.get("bugs", []):
        if not isinstance(b, dict) or is_dummy_finding(b):
            continue
        title = str(b.get("title") or b.get("bug_id") or "Bug Identified").strip()
        fpath = str(b.get("file") or b.get("file_name") or default_file).strip()
        line = b.get("line") or b.get("line_number")
        try:
            line = int(line) if line is not None else None
        except Exception:
            line = None
        
        b_type = str(b.get("type", "confirmed")).lower()
        if b_type not in ("confirmed", "conditional", "possible_risk"):
            b_type = "confirmed"
            
        b_sev = str(b.get("severity", "medium")).lower()
        if b_sev not in ("critical", "high", "medium", "low"):
            b_sev = "medium"

        evidence = str(b.get("evidence") or b.get("before_code") or b.get("description") or "Code defect identified.").strip()
        desc = str(b.get("description") or b.get("explanation") or title).strip()
        impact = str(b.get("impact") or desc or "Potential logic defect.").strip()
        fix = str(b.get("fix") or b.get("suggested_solution") or b.get("after_code") or "Refactor code to handle edge case.").strip()
        
        conf = b.get("confidence")
        try:
            conf = int(conf) if conf is not None else 85
        except Exception:
            conf = 85

        clean_bugs.append({
            "title": title,
            "type": b_type,
            "severity": b_sev,
            "file": fpath,
            "line": line,
            "line_range": str(b.get("line_range")) if b.get("line_range") else None,
            "evidence": evidence,
            "description": desc,
            "explanation": str(b.get("explanation") or desc),
            "impact": impact,
            "fix": fix,
            "suggested_solution": str(b.get("suggested_solution") or fix),
            "before_code": b.get("before_code"),
            "after_code": b.get("after_code"),
            "corrected_code": b.get("corrected_code") or b.get("after_code"),
            "reason_for_correction": b.get("reason_for_correction") or "Fixes logic issue and prevents errors.",
            "confidence": conf
        })
    review_json["bugs"] = clean_bugs

    # 2. Clean ERRORS
    clean_errors = []
    for e in review_json.get("errors", []):
        if not isinstance(e, dict) or is_dummy_finding(e):
            continue
        title = str(e.get("title") or e.get("error_id") or "Runtime Error").strip()
        fpath = str(e.get("file") or e.get("file_name") or default_file).strip()
        line = e.get("line") or e.get("line_number")
        try:
            line = int(line) if line is not None else None
        except Exception:
            line = None

        e_sev = str(e.get("severity", "high")).lower()
        if e_sev not in ("critical", "high", "medium", "low"):
            e_sev = "high"

        evidence = str(e.get("evidence") or e.get("before_code") or e.get("description") or "Runtime exception identified.").strip()
        desc = str(e.get("description") or title).strip()
        impact = str(e.get("impact") or "Potential runtime crash.").strip()
        fix = str(e.get("fix") or e.get("suggested_solution") or "Add validation or error handling.").strip()

        conf = e.get("confidence")
        try:
            conf = int(conf) if conf is not None else 85
        except Exception:
            conf = 85

        clean_errors.append({
            "type": str(e.get("type") or "RuntimeError"),
            "title": title,
            "file": fpath,
            "line": line,
            "line_range": str(e.get("line_range")) if e.get("line_range") else None,
            "evidence": evidence,
            "description": desc,
            "explanation": str(e.get("explanation") or desc),
            "severity": e_sev,
            "impact": impact,
            "fix": fix,
            "suggested_solution": str(e.get("suggested_solution") or fix),
            "before_code": e.get("before_code"),
            "after_code": e.get("after_code"),
            "corrected_code": e.get("corrected_code") or e.get("after_code"),
            "reason_for_correction": e.get("reason_for_correction") or "Prevents runtime crash.",
            "confidence": conf
        })
    review_json["errors"] = clean_errors

    # 3. Clean SECURITY
    if isinstance(review_json.get("security"), dict):
        raw_sec = review_json["security"]
        raw_issues = raw_sec.get("issues")
        if not isinstance(raw_issues, list):
            raw_issues = []
        clean_sec = []
        for s in raw_issues:
            if not isinstance(s, dict) or is_dummy_finding(s):
                continue
            title = str(s.get("title") or "Security Vulnerability").strip()
            fpath = str(s.get("file") or s.get("file_name") or default_file).strip()
            line = s.get("line") or s.get("line_number")
            try:
                line = int(line) if line is not None else None
            except Exception:
                line = None
            s_sev = str(s.get("severity", "high")).lower()
            if s_sev not in ("critical", "high", "medium", "low"):
                s_sev = "high"
            conf = s.get("confidence")
            try:
                conf = int(conf) if conf is not None else 85
            except Exception:
                conf = 85
            clean_sec.append({
                "title": title,
                "description": str(s.get("description") or title),
                "explanation": str(s.get("explanation") or s.get("description") or title),
                "file": fpath,
                "line": line,
                "line_range": str(s.get("line_range")) if s.get("line_range") else None,
                "severity": s_sev,
                "evidence": str(s.get("evidence") or s.get("before_code") or "Security vulnerability detected."),
                "impact": str(s.get("impact") or "Potential security exposure."),
                "suggestion": str(s.get("suggestion") or s.get("fix") or "Apply secure coding pattern."),
                "suggested_solution": str(s.get("suggested_solution") or s.get("fix") or "Apply secure coding pattern."),
                "before_code": s.get("before_code"),
                "after_code": s.get("after_code"),
                "corrected_code": s.get("corrected_code") or s.get("after_code"),
                "reason_for_correction": s.get("reason_for_correction") or "Mitigates security vulnerability.",
                "confidence": conf
            })
        review_json["security"] = {
            "issues_found": len(clean_sec),
            "issues": clean_sec
        }
    else:
        review_json["security"] = {"issues_found": 0, "issues": []}

    # 4. Clean PERFORMANCE
    if isinstance(review_json.get("performance"), dict):
        raw_perf = review_json["performance"]
        raw_issues = raw_perf.get("issues")
        if not isinstance(raw_issues, list):
            raw_issues = []
        clean_perf = []
        for p in raw_issues:
            if not isinstance(p, dict) or is_dummy_finding(p):
                continue
            title = str(p.get("title") or "Performance Bottleneck").strip()
            fpath = str(p.get("file") or p.get("file_name") or default_file).strip()
            line = p.get("line") or p.get("line_number")
            try:
                line = int(line) if line is not None else None
            except Exception:
                line = None
            p_sev = str(p.get("severity", "medium")).lower()
            if p_sev not in ("critical", "high", "medium", "low"):
                p_sev = "medium"
            conf = p.get("confidence")
            try:
                conf = int(conf) if conf is not None else 85
            except Exception:
                conf = 85
            clean_perf.append({
                "title": title,
                "description": str(p.get("description") or title),
                "explanation": str(p.get("explanation") or p.get("description") or title),
                "file": fpath,
                "line": line,
                "line_range": str(p.get("line_range")) if p.get("line_range") else None,
                "severity": p_sev,
                "evidence": str(p.get("evidence") or p.get("before_code") or "Performance bottleneck detected."),
                "impact": str(p.get("impact") or "Increased latency or resource usage."),
                "suggestion": str(p.get("suggestion") or p.get("fix") or "Optimize algorithm or data structure."),
                "suggested_solution": str(p.get("suggested_solution") or p.get("fix") or "Optimize algorithm or data structure."),
                "before_code": p.get("before_code"),
                "after_code": p.get("after_code"),
                "corrected_code": p.get("corrected_code") or p.get("after_code"),
                "reason_for_correction": p.get("reason_for_correction") or "Improves execution efficiency.",
                "confidence": conf
            })
        tc = str(raw_perf.get("time_complexity") or "Evaluated")
        sc = str(raw_perf.get("space_complexity") or "Evaluated")
        review_json["performance"] = {
            "time_complexity": tc,
            "space_complexity": sc,
            "issues": clean_perf
        }
    else:
        review_json["performance"] = {"time_complexity": "Evaluated", "space_complexity": "Evaluated", "issues": []}

    # 5. Clean CODE QUALITY
    if isinstance(review_json.get("code_quality"), dict):
        cq = review_json["code_quality"]
        obs = cq.get("observations", [])
        sug = cq.get("suggestions", [])
        if not isinstance(obs, list):
            obs = [{"title": "Code Quality Note", "description": str(obs), "severity": "low"}] if obs else []
        if not isinstance(sug, list):
            sug = [{"title": "Code Quality Note", "description": str(sug), "severity": "low"}] if sug else []
        clean_obs = []
        for o in obs:
            if isinstance(o, dict) and not is_dummy_finding(o):
                clean_obs.append({
                    "title": str(o.get("title") or "Code Quality Note"),
                    "description": str(o.get("description") or o.get("title") or "Quality observation"),
                    "severity": str(o.get("severity", "low")).lower() if str(o.get("severity", "low")).lower() in ("critical", "high", "medium", "low") else "low",
                    "file": o.get("file"),
                    "line": o.get("line")
                })
        clean_sug = []
        for s in sug:
            if isinstance(s, dict) and not is_dummy_finding(s):
                clean_sug.append({
                    "title": str(s.get("title") or "Code Quality Note"),
                    "description": str(s.get("description") or s.get("title") or "Quality suggestion"),
                    "severity": str(s.get("severity", "low")).lower() if str(s.get("severity", "low")).lower() in ("critical", "high", "medium", "low") else "low",
                    "file": s.get("file"),
                    "line": s.get("line")
                })
        review_json["code_quality"] = {"observations": clean_obs, "suggestions": clean_sug}
    else:
        review_json["code_quality"] = {"observations": [], "suggestions": []}

    # 6. Clean CONFIDENCE & SCORE
    conf = review_json.get("confidence")
    try:
        review_json["confidence"] = int(conf) if conf is not None else 85
    except Exception:
        review_json["confidence"] = 85

    score = review_json.get("score")
    if isinstance(score, str):
        try:
            clean_s = "".join(c for c in score.split("/")[0] if c.isdigit() or c == ".")
            review_json["score"] = float(clean_s) if clean_s else None
        except Exception:
            review_json["score"] = None

    # 7. Required lists
    for k in ("key_methods", "key_classes", "libraries", "user_requirements", "review_types", "corrected_code"):
        if not isinstance(review_json.get(k), list):
            review_json[k] = []

    if not review_json.get("answer_summary") or review_json.get("answer_summary") in ("Answer Summary", "Answer summary"):
        review_json["answer_summary"] = "Code review audit completed with grounded analysis across reliability, security, and performance."
    if not review_json.get("final_verdict") or review_json.get("final_verdict") in ("Final Verdict", "Final verdict"):
        review_json["final_verdict"] = "Analysis complete. Review findings above for recommended corrections."

    return review_json


# ============================================================
# VALIDATE FINDINGS
# ============================================================

def validate_findings(
    review: StructuredReview
) -> StructuredReview:
    default_file = review.files_analyzed[0].file_name if review.files_analyzed else "source_code"

    # ========================================================
    # BUGS
    # ========================================================
    verified_bugs = []
    for bug in review.bugs:
        if not getattr(bug, "evidence", None) or not str(bug.evidence).strip():
            bug.evidence = getattr(bug, "before_code", None) or getattr(bug, "description", None) or getattr(bug, "explanation", None) or getattr(bug, "title", "Identified in source")
        if not getattr(bug, "file", None) or not str(bug.file).strip():
            bug.file = default_file
        if not getattr(bug, "impact", None) or not str(bug.impact).strip():
            bug.impact = getattr(bug, "description", "May affect application execution or reliability.")
        if not getattr(bug, "fix", None) or not str(bug.fix).strip():
            bug.fix = getattr(bug, "suggested_solution", None) or getattr(bug, "after_code", "Apply suggested correction.")
        verified_bugs.append(bug)
    review.bugs = verified_bugs

    # ========================================================
    # ERRORS
    # ========================================================
    verified_errors = []
    for error in review.errors:
        if not getattr(error, "evidence", None) or not str(error.evidence).strip():
            error.evidence = getattr(error, "before_code", None) or getattr(error, "description", None) or getattr(error, "explanation", None) or getattr(error, "title", "Identified in source")
        if not getattr(error, "file", None) or not str(error.file).strip():
            error.file = default_file
        if not getattr(error, "impact", None) or not str(error.impact).strip():
            error.impact = getattr(error, "description", "Execution runtime error potential.")
        if not getattr(error, "fix", None) or not str(error.fix).strip():
            error.fix = getattr(error, "suggested_solution", None) or getattr(error, "after_code", "Correct syntax or logic error.")
        verified_errors.append(error)
    review.errors = verified_errors

    # ========================================================
    # SECURITY
    # ========================================================
    if review.security:
        for s in review.security.issues:
            if not getattr(s, "file", None) or not str(s.file).strip():
                s.file = default_file
        review.security.issues_found = len(review.security.issues)

    # ========================================================
    # PERFORMANCE & CODE QUALITY FILES
    # ========================================================
    if review.performance:
        for p in review.performance.issues:
            if not getattr(p, "file", None) or not str(p.file).strip():
                p.file = default_file

    if review.code_quality:
        for obs in review.code_quality.observations:
            if not getattr(obs, "file", None) or not str(getattr(obs, "file", "")).strip():
                obs.file = default_file
        for sug in review.code_quality.suggestions:
            if not getattr(sug, "file", None) or not str(getattr(sug, "file", "")).strip():
                sug.file = default_file

    return review


# ============================================================
# NORMALIZE REVIEW
# ============================================================

def normalize_review(
    review: StructuredReview,
    question: str,
    category: Optional[str] = None
) -> StructuredReview:

    # ========================================================
    # SUMMARY
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
                +
                (
                    "s"
                    if bug_count != 1
                    else ""
                )
            )

        if error_count:

            findings.append(
                f"{error_count} error"
                +
                (
                    "s"
                    if error_count != 1
                    else ""
                )
            )

        if security_count:

            findings.append(
                f"{security_count} security issue"
                +
                (
                    "s"
                    if security_count != 1
                    else ""
                )
            )

        if performance_count:

            findings.append(
                f"{performance_count} performance concern"
                +
                (
                    "s"
                    if performance_count != 1
                    else ""
                )
            )

        if quality_count:

            findings.append(
                f"{quality_count} code-quality finding"
                +
                (
                    "s"
                    if quality_count != 1
                    else ""
                )
            )

        if findings:

            review.answer_summary = (
                "The review identified "
                +
                ", ".join(
                    findings
                )
                +
                ". See the detailed findings below."
            )

        else:

            review.answer_summary = (
                "The project was reviewed successfully. "
                "No supported issues were identified "
                "for the requested analysis."
            )

    # ========================================================
    # FINAL VERDICT
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
    # PERFORMANCE
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

        if any(
            indicator
            in performance_text
            for indicator
            in quadratic_indicators
        ):

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

    # --------------------------------------------------------
    # Use finding confidence when findings contain confidence
    # --------------------------------------------------------

    if confidences:

        review.confidence = round(
            sum(
                confidences
            )
            /
            len(
                confidences
            )
        )

    # --------------------------------------------------------
    # Findings exist but individual confidence was not supplied
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Clean review
    # --------------------------------------------------------
    # No findings does NOT mean zero confidence.
    # It means the model found no issues in the analyzed source.
    # --------------------------------------------------------

    else:

        review.confidence = 95
    # ========================================================
    # 8-POINT SOLUTION & CODE CORRECTION NORMALIZATION
    # ========================================================
    detected_list = []

    def _normalize_item(item, category: str, default_sev: str):
        # 1. Problem Identification
        current_title = getattr(item, "title", "") or ""
        if not current_title.strip():
            desc_text = getattr(item, "description", "") or ""
            item.title = desc_text.split(".")[0] if desc_text else f"Detected {category} issue"

        # 2. File & Line
        current_file = getattr(item, "file", None)
        if not current_file or not str(current_file).strip():
            item.file = "main.py"

        # 3. Explanation
        exp = getattr(item, "explanation", None) or getattr(item, "description", None) or ""
        desc = getattr(item, "description", None) or exp or ""
        item.explanation = exp or desc
        item.description = desc or exp

        # 4. Severity
        sev = getattr(item, "severity", None)
        if sev not in ["critical", "high", "medium", "low"]:
            item.severity = default_sev

        # 5. Suggested Solution
        sol = (
            getattr(item, "suggested_solution", None)
            or getattr(item, "fix", None)
            or getattr(item, "suggestion", None)
            or "Apply recommended security and code quality practices to resolve this issue."
        )
        item.suggested_solution = sol
        if hasattr(item, "fix"):
            item.fix = getattr(item, "fix", None) or sol
        if hasattr(item, "suggestion"):
            item.suggestion = getattr(item, "suggestion", None) or sol

        # 6 & 7. Before and After Code
        before = getattr(item, "before_code", None) or getattr(item, "evidence", None) or ""
        after = getattr(item, "after_code", None) or getattr(item, "corrected_code", None) or ""

        item.before_code = before
        if hasattr(item, "evidence"):
            item.evidence = getattr(item, "evidence", None) or before
        item.after_code = after
        item.corrected_code = after or getattr(item, "corrected_code", None)

        # 8. Reason for Correction
        reason = getattr(item, "reason_for_correction", None)
        if not reason or not str(reason).strip():
            imp = getattr(item, "impact", None)
            if imp and str(imp).strip():
                item.reason_for_correction = f"Prevents {str(imp).lower()} and ensures adherence to production quality standards."
            else:
                item.reason_for_correction = f"Improves reliability, security, and maintainability by resolving the {item.severity}-severity {category} flaw."

        return DetectedIssue(
            title=item.title,
            category=category,
            file=item.file,
            line=getattr(item, "line", None),
            line_range=getattr(item, "line_range", None),
            description=item.description,
            explanation=item.explanation,
            severity=item.severity,
            suggested_solution=item.suggested_solution,
            before_code=item.before_code,
            after_code=item.after_code,
            corrected_code=item.corrected_code,
            reason_for_correction=item.reason_for_correction,
            impact=getattr(item, "impact", None),
            confidence=getattr(item, "confidence", None)
        )

    for b in review.bugs:
        detected_list.append(_normalize_item(b, "bug", "high"))

    for e in review.errors:
        detected_list.append(_normalize_item(e, "error", "high"))

    if review.security:
        for s in review.security.issues:
            detected_list.append(_normalize_item(s, "security", "medium"))

    if review.performance:
        for p in review.performance.issues:
            detected_list.append(_normalize_item(p, "performance", "medium"))

    if review.code_quality:
        for o in review.code_quality.observations:
            detected_list.append(_normalize_item(o, "code_quality", "low"))
        for sq in review.code_quality.suggestions:
            detected_list.append(_normalize_item(sq, "code_quality", "low"))

    # Also absorb any detected_issues provided directly
    if getattr(review, "detected_issues", None) and not detected_list:
        for item in review.detected_issues:
            cat = getattr(item, "category", "general") or "general"
            sev = getattr(item, "severity", "medium") or "medium"
            norm = _normalize_item(item, cat, sev)
            detected_list.append(norm)

            if cat == "security":
                if not review.security:
                    review.security = SecurityInfo(issues_found=0, issues=[])
                review.security.issues.append(
                    SecurityFinding(
                        title=norm.title,
                        description=norm.description,
                        explanation=norm.explanation,
                        file=norm.file,
                        line=norm.line,
                        line_range=norm.line_range,
                        severity=norm.severity,
                        suggested_solution=norm.suggested_solution,
                        before_code=norm.before_code,
                        after_code=norm.after_code,
                        corrected_code=norm.corrected_code,
                        reason_for_correction=norm.reason_for_correction,
                        confidence=norm.confidence or 80
                    )
                )
                review.security.issues_found = len(review.security.issues)
            elif cat == "performance":
                if not review.performance:
                    review.performance = PerformanceInfo(time_complexity="O(1)", space_complexity="O(1)", issues=[])
                review.performance.issues.append(
                    PerformanceIssue(
                        title=norm.title,
                        description=norm.description,
                        explanation=norm.explanation,
                        file=norm.file,
                        line=norm.line,
                        line_range=norm.line_range,
                        severity=norm.severity,
                        suggested_solution=norm.suggested_solution,
                        before_code=norm.before_code,
                        after_code=norm.after_code,
                        corrected_code=norm.corrected_code,
                        reason_for_correction=norm.reason_for_correction,
                        confidence=norm.confidence or 80
                    )
                )

    review.detected_issues = detected_list

    # ========================================================
    # DYNAMIC GROUNDED SCORE & BEST PRACTICES (FULL REVIEW)
    # ========================================================

    is_full_review = (
        category == "full_review"
        or "full_review" in (review.review_types or [])
        or any("full" in q for q in [question.lower()])
        or any("complete" in q for q in [question.lower()])
    )

    if is_full_review:
        # Calculate dynamic grounded score based on actual issue severity
        crit_count = sum(1 for d in detected_list if d.severity == "critical")
        high_count = sum(1 for d in detected_list if d.severity == "high")
        med_count = sum(1 for d in detected_list if d.severity == "medium")
        low_count = sum(1 for d in detected_list if d.severity == "low")

        # Rigorous penalty formula: Critical (-25), High (-15), Medium (-8), Low (-3)
        total_penalty = (crit_count * 25) + (high_count * 15) + (med_count * 8) + (low_count * 3)
        calculated_score = max(5.0, min(100.0, 100.0 - total_penalty))

        if len(detected_list) == 0:
            review.score = 100.0
        else:
            review.score = round(calculated_score, 1)

        # Best Practices excluded per requirements
        review.best_practices = None
    else:
        # For category-specific reviews (Bugs, Security, Performance, Code Quality),
        # calculate accurate domain health score based on detected category findings
        cat_crit = sum(1 for d in detected_list if d.severity == "critical")
        cat_high = sum(1 for d in detected_list if d.severity == "high")
        cat_med = sum(1 for d in detected_list if d.severity == "medium")
        cat_low = sum(1 for d in detected_list if d.severity == "low")
        cat_penalty = (cat_crit * 25) + (cat_high * 15) + (cat_med * 8) + (cat_low * 3)
        cat_calculated = max(5.0, min(100.0, 100.0 - cat_penalty))

        if len(detected_list) == 0:
            review.score = 100.0
        else:
            review.score = round(cat_calculated, 1)

        review.best_practices = None

        if category in ("bugs", "bug"):
            review.security = None
            review.performance = None
            review.code_quality = None
        elif category in ("security", "sec"):
            review.bugs = []
            review.errors = []
            review.performance = None
            review.code_quality = None
        elif category in ("performance", "perf"):
            review.bugs = []
            review.errors = []
            review.security = None
            review.code_quality = None
        elif category in ("code_quality", "quality"):
            review.bugs = []
            review.errors = []
            review.security = None
            review.performance = None

    # ========================================================
    # QUESTION
    # ========================================================

    review.question = question

    return review



# ============================================================
# FRONTEND STATIC ASSETS & HOME
# ============================================================

FRONTEND_BUILD_DIR = Path(__file__).resolve().parent.parent / "frontend" / "build"
if not FRONTEND_BUILD_DIR.exists():
    FRONTEND_BUILD_DIR = Path(__file__).resolve().parent / "static"

if FRONTEND_BUILD_DIR.exists() and (FRONTEND_BUILD_DIR / "static").exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_BUILD_DIR / "static")), name="static")


# Initialize SQLite database on load
try:
    init_db()
except Exception as _e:
    print(f"[DB] Database initialization notice: {repr(_e)}")


# ============================================================
# USER AUTHENTICATION / IDENTITY EXTRACTION HELPER
# ============================================================

def get_request_user(request: Request) -> Dict[str, str]:
    """
    Resolve identity from a verified Clerk JWT. Header-based identity is only
    accepted by the explicitly local development server.
    """
    auth_header = request.headers.get("Authorization", "").strip()
    if APP_ENV == "development":
        # Local header auth supports the developer sign-in UI only. Never use
        # this mode for a deployed server; Docker explicitly selects production.
        user_id = request.headers.get("X-User-Id", "").strip()
        user_email = request.headers.get("X-User-Email", "").strip()
        user_name = request.headers.get("X-User-Name", "").strip()
        if not user_id:
            raise HTTPException(status_code=401, detail="Authentication required.")
    elif auth_header:
        scheme, _, token = auth_header.partition(" ")
        if scheme.lower() != "bearer" or not token.strip():
            raise HTTPException(status_code=401, detail="A valid Bearer token is required.")
        claims = verify_clerk_token(token.strip())
        user_id = str(claims.get("sub") or "").strip()
        if not user_id:
            raise HTTPException(status_code=401, detail="Authentication token has no user identity.")
        user_email = str(claims.get("email") or request.headers.get("X-User-Email", "")).strip()
        user_name = str(claims.get("name") or request.headers.get("X-User-Name", "")).strip()
    else:
        raise HTTPException(status_code=401, detail="Authentication required.")

    # Ensure user exists in users table so foreign keys always resolve
    try:
        crud.upsert_user(
            user_id=user_id,
            email=user_email or f"{user_id}@local.app",
            full_name=user_name
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Could not load the authenticated user.") from exc

    return {
        "id": user_id,
        "email": user_email,
        "name": user_name
    }


# ============================================================
# API MODELS FOR USER, THEME, REVIEWS
# ============================================================

class UserSyncRequest(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = ""
    image_url: Optional[str] = ""


class ThemeRequest(BaseModel):
    theme: str


# ============================================================
# USER & AUTH DATABASE ENDPOINTS
# ============================================================

@app.post("/api/users/sync")
def sync_user(data: UserSyncRequest, request: Request):
    """
    Upserts user record into SQLite when a user signs in via Clerk.
    """
    try:
        if APP_ENV == "development" and not request.headers.get("X-User-Id"):
            # Keep unauthenticated profile creation available to the local
            # integration harness only; production always requires a verified JWT.
            pass
        else:
            identity = get_request_user(request)
            if identity["id"] != data.id:
                raise HTTPException(status_code=403, detail="Cannot sync a different user's profile.")
        user = crud.upsert_user(
            user_id=data.id,
            email=data.email,
            full_name=data.full_name,
            image_url=data.image_url
        )
        return {"success": True, "user": user}
    except HTTPException:
        raise
    except Exception as e:
        print("User Sync Error:", repr(e))
        raise HTTPException(status_code=500, detail="Failed to sync user data")


@app.get("/api/users/me")
def get_current_user_profile(request: Request):
    """
    Returns profile information for the authenticated user from SQLite.
    """
    u = get_request_user(request)
    if not u["id"]:
        raise HTTPException(status_code=401, detail="Authentication required")
    user = crud.get_user(u["id"])
    if not user:
        user = crud.upsert_user(u["id"], u["email"] or f"{u['id']}@user.local", u["name"])
    return {"success": True, "user": user}


# ============================================================
# THEME PREFERENCE ENDPOINTS
# ============================================================

@app.get("/api/user/theme")
def get_theme(request: Request):
    """
    Retrieves the user's saved theme preference from SQLite (default 'dark').
    """
    u = get_request_user(request)
    if not u["id"]:
        return {"theme": "dark"}
    theme = crud.get_user_theme(u["id"])
    return {"theme": theme}


@app.put("/api/user/theme")
def update_theme(data: ThemeRequest, request: Request):
    """
    Persists user's selected theme preference in SQLite.
    """
    u = get_request_user(request)
    if not u["id"]:
        return {"success": True, "theme": data.theme, "note": "Guest theme"}
    crud.update_user_theme(u["id"], data.theme)
    return {"success": True, "theme": data.theme}


# ============================================================
# REVIEW HISTORY DATABASE ENDPOINTS
# ============================================================

@app.get("/api/reviews")
def get_user_reviews_endpoint(request: Request):
    """
    Returns list of code reviews belonging exclusively to the authenticated user.
    """
    u = get_request_user(request)
    if not u["id"]:
        raise HTTPException(status_code=401, detail="Authentication required to view review history")
    reviews = crud.get_user_reviews(u["id"])
    return {"success": True, "reviews": reviews}


@app.get("/api/reviews/{review_id}")
def get_single_review_endpoint(review_id: str, request: Request):
    """
    Returns full details and AI results of a specific review if owned by user.
    """
    u = get_request_user(request)
    if not u["id"]:
        raise HTTPException(status_code=401, detail="Authentication required")
    review = crud.get_review_by_id(review_id, u["id"])
    if not review:
        raise HTTPException(status_code=404, detail="Review not found or unauthorized")
    return {"success": True, "review": review}


@app.delete("/api/reviews/{review_id}")
def delete_single_review_endpoint(review_id: str, request: Request):
    """
    Deletes a single review record owned by the authenticated user.
    """
    u = get_request_user(request)
    if not u["id"]:
        raise HTTPException(status_code=401, detail="Authentication required")
    deleted = crud.delete_review(review_id, u["id"])
    if not deleted:
        raise HTTPException(status_code=404, detail="Review not found or unauthorized")
    return {"success": True, "message": "Review deleted successfully"}


@app.delete("/api/reviews")
def clear_all_reviews_endpoint(request: Request):
    """
    Clears all review records owned by the authenticated user.
    """
    u = get_request_user(request)
    if not u["id"]:
        raise HTTPException(status_code=401, detail="Authentication required")
    count = crud.delete_all_reviews(u["id"])
    return {"success": True, "deleted_count": count}


# ============================================================
# UPLOADED FILES DATABASE ENDPOINTS
# ============================================================

@app.get("/api/files")
def get_user_files_endpoint(request: Request):
    """
    Returns list of uploaded files belonging to the authenticated user.
    """
    u = get_request_user(request)
    if not u["id"]:
        raise HTTPException(status_code=401, detail="Authentication required to view files")
    files = crud.get_user_files(u["id"])
    return {"success": True, "files": files}


@app.delete("/api/files/{file_id}")
def delete_user_file_endpoint(file_id: str, request: Request):
    """
    Deletes an uploaded file entry owned by the authenticated user.
    """
    u = get_request_user(request)
    if not u["id"]:
        raise HTTPException(status_code=401, detail="Authentication required")
    deleted = crud.delete_uploaded_file(file_id, u["id"])
    if not deleted:
        raise HTTPException(status_code=404, detail="File record not found or unauthorized")
    return {"success": True, "message": "File record deleted successfully"}


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "message": "AI Code Review Assistant API is running",
        "version": "1.4.0"
    }


@app.get("/")
def home():
    index_file = FRONTEND_BUILD_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file, headers={"Cache-Control": "no-cache, no-store, must-revalidate"})

    return {
        "success": True,
        "message": (
            "AI Code Review Assistant "
            "Backend Running Successfully"
        ),
        "version": "1.4.0"
    }


# ============================================================
# PROJECT INFORMATION
# ============================================================

@app.get("/project-info")
def project_info(request: Request):

    user = get_request_user(request)
    rag_pipeline = get_user_runtime(user["id"])["rag_pipeline"]

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
    request: Request,
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
                    "Only ZIP project files "
                    "are supported."
                )
            )

        u = get_request_user(request)
        runtime = get_user_runtime(u["id"])

        # Security check: validate file size, type, and safety
        await validate_uploaded_file(file, is_zip=True)

        res = await (
            runtime["upload_service"]
            .process_zip_upload(
                file
            )
        )

        try:
            project_folder = Path(res["project_folder"])
            fsize = sum(path.stat().st_size for path in project_folder.rglob("*") if path.is_file())
            crud.create_uploaded_file(
                file_id=str(uuid.uuid4()),
                user_id=u["id"],
                file_name=sanitize_filename(file.filename),
                file_path=str(project_folder),
                file_size=fsize,
                file_type="zip"
            )
            print(f"[DB] Uploaded ZIP tracked in SQLite for user {u['id']}")
        except Exception as db_err:
            print(f"[DB] Error recording ZIP upload: {repr(db_err)}")

        return res

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
    request: Request,
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

        u = get_request_user(request)
        runtime = get_user_runtime(u["id"])

        # Security check: validate each source file
        for f in files:
            await validate_uploaded_file(f, is_zip=False)

        res = await (
            runtime["upload_service"]
            .process_multiple_files(
                files
            )
        )

        try:
            project_folder = Path(res["project_folder"])
            for f in files:
                clean_name = sanitize_filename(f.filename)
                saved_path = project_folder / Path(f.filename).name
                crud.create_uploaded_file(
                    file_id=str(uuid.uuid4()),
                    user_id=u["id"],
                    file_name=clean_name,
                    file_path=str(saved_path),
                    file_size=saved_path.stat().st_size if saved_path.is_file() else 0,
                    file_type=Path(clean_name).suffix or "code"
                )
            print(f"[DB] Uploaded {len(files)} files tracked in SQLite for user {u['id']}")
        except Exception as db_err:
            print(f"[DB] Error recording uploaded files: {repr(db_err)}")

        return res

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
    data: PasteCodeRequest,
    request: Request
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

        if len(code.encode("utf-8")) > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=413,
                detail="Pasted code exceeds the 10 MB limit.",
            )

        u = get_request_user(request)
        runtime = get_user_runtime(u["id"])

        # Security check on pasted file extension
        is_valid, err_msg = validate_file_extension(filename, allow_zip=False)
        if not is_valid:
            raise HTTPException(status_code=400, detail=err_msg)

        result = (
            runtime["upload_service"]
            .process_paste_code(
            code=code,
            filename=filename
            )
        )    

        try:
            clean_name = sanitize_filename(filename)
            saved_path = Path(result["project_folder"]) / Path(filename).name
            crud.create_uploaded_file(
                file_id=str(uuid.uuid4()),
                user_id=u["id"],
                file_name=clean_name,
                file_path=str(saved_path),
                file_size=len(code.encode("utf-8")),
                file_type=Path(clean_name).suffix or "code"
            )
            print(f"[DB] Pasted code tracked in SQLite for user {u['id']}")
        except Exception as db_err:
            print(f"[DB] Error recording pasted code: {repr(db_err)}")
        print(
            "\n========== AFTER PASTE INDEX =========="
            )
        print(
            "Indexed Files:",
            runtime["rag_pipeline"].get_indexed_files()
            )
        print(
            "Indexed File Count:",
            len(
                runtime["rag_pipeline"].get_indexed_files()
                )
            )
        print(
            "Indexed Chunks:",
            runtime["rag_pipeline"].vector_store.size()
            )
        print(
            "=======================================\n"
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
            detail=(
                "Failed to process pasted code."
            )
        )


# ============================================================
# UPLOAD GITHUB REPOSITORY
# ============================================================

@app.post("/upload-github")
async def upload_github(
    data: GithubRequest,
    request: Request,
):

    try:

        user = get_request_user(request)
        runtime = get_user_runtime(user["id"])

        repo_url = data.repo_url.strip()

        if not repo_url:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Repository URL "
                    "cannot be empty."
                )
            )

        return await (
            runtime["upload_service"]
            .process_github_repo(
                repo_url
            )
        )

    except HTTPException:

        raise

    except Exception as e:

        print(
            "Upload GitHub Error:",
            repr(e)
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to download "
                "GitHub repository."
            )
        )


# ============================================================
# REVIEW PROJECT
# ============================================================

@app.post("/review")
def review_project(
    data: ReviewRequest,
    request: Request
):
    review_request_id = request.headers.get("X-Review-Request-Id") or str(uuid.uuid4())
    cancellation_event: Optional[threading.Event] = None
    cancellation_registry_key: Optional[str] = None
    try:
        user = get_request_user(request)
        cancellation_registry_key = f"{user['id']}:{review_request_id}"
        with _review_cancellations_lock:
            now = time.monotonic()
            for key, entry in list(_review_cancellations.items()):
                if entry.get("expires_at", now + 1) <= now:
                    _review_cancellations.pop(key, None)
            pending_cancel = _review_cancellations.get(cancellation_registry_key)
            if pending_cancel and pending_cancel.get("user_id") == user["id"]:
                cancellation_event = pending_cancel["event"]
                pending_cancel.pop("expires_at", None)
            else:
                cancellation_event = threading.Event()
                _review_cancellations[cancellation_registry_key] = {
                    "user_id": user["id"],
                    "event": cancellation_event,
                }

        def ensure_review_not_cancelled():
            if cancellation_event and cancellation_event.is_set():
                raise HTTPException(status_code=409, detail="Analysis was stopped.")

        ensure_review_not_cancelled()
        runtime = get_user_runtime(user["id"])
        rag_pipeline = runtime["rag_pipeline"]

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
        # REVIEW TYPES & CATEGORY
        # ====================================================

        req_category = getattr(data, "category", None)

        detected_modes = (
            rag_pipeline
            .prompt_builder
            .detect_review_modes(
                question,
                category=req_category
            )
        )

        print(
            "\nRequested Category:",
            req_category,
            "| Detected Review Types:",
            detected_modes
        )


        # ====================================================
        # RETRIEVE FIRST
        # ====================================================

        print(
            "\nRetrieving relevant code..."
        )
        
        print(
            "\n========== REVIEW VECTOR STATE =========="
        )

        print(
            "Indexed Files:",
            rag_pipeline.get_indexed_files()
            )

        print(
            "Indexed File Count:",
            len(
                rag_pipeline.get_indexed_files()
            )
        )

        print(
            "Indexed Chunks:",
            rag_pipeline.vector_store.size()
        )

        print(
            "=========================================\n"
        )

        retrieval = (
            rag_pipeline
            .retrieve_context(
                query=question
            )
        )
        ensure_review_not_cancelled()

        retrieved_chunks = (
            retrieval.get(
                "chunks",
                []
            )
        )

        query_type = retrieval.get(
            "query_type",
            "targeted"
        )

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
            "\n========== TRUSTED CURRENT FILES =========="
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

        # ====================================================
        # NO RETRIEVED CODE
        # ====================================================

        if not retrieved_chunks:

            raise HTTPException(
                status_code=502,
                detail=(
                    "No relevant source code "
                    "was retrieved for this review."
                )
            )

        # ====================================================
        # GENERATE PROMPT FROM SAME RETRIEVAL
        # ====================================================

        prompt = (
            rag_pipeline
            .prompt_builder
            .build_prompt(
                query=question,
                retrieved_chunks=retrieved_chunks,
                project_metadata=(
                    rag_pipeline
                    .get_project_metadata()
                ),
                category=req_category
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
        # GROQ
        # ====================================================
        print("\n========== PROMPT DEBUG ==========")
        print("Prompt characters:", len(prompt))
        print("Prompt preview:")
        print(prompt[:3000])
        print("==================================")

        ensure_review_not_cancelled()
        active_cfg = crud.get_user_single_agent_config(user["id"])
        user_prefs = crud.get_user_preferences(user["id"])
        is_multi = (user_prefs.get("agent_mode") == "multi")

        system_review_instructions = (
            "You are a senior software engineer performing a grounded code review.\n"
            "Analyze ONLY the source code provided in the user prompt.\n\n"
            "CRITICAL ROOT JSON FORMAT:\n"
            "You MUST return the complete Structured Review JSON object at the root, containing ALL required keys:\n"
            "project, question, user_requirements, review_types, answer_summary, files_analyzed, "
            "key_methods, key_classes, libraries, bugs, errors, performance, security, code_quality, "
            "corrected_code, expected_output, score, confidence, final_verdict.\n"
            "DO NOT output an individual finding object as the root JSON. Place each finding inside its category array "
            "(bugs, errors, security.issues, performance.issues, or code_quality.suggestions).\n\n"
            "EIGHT-POINT SOLUTION SPECIFICATION (MANDATORY FOR EVERY ISSUE):\n"
            "For EVERY detected issue across bugs, errors, security, performance, and code quality, you MUST provide:\n"
            "1. title: Problem Identification\n"
            "2. file, line, line_range: Exact File and Line Number\n"
            "3. explanation & description: Why the code is problematic\n"
            "4. severity: 'critical', 'high', 'medium', or 'low'\n"
            "5. suggested_solution & fix: How the issue can be fixed\n"
            "6. after_code & finding-level corrected_code: Corrected version of the code snippet\n"
            "7. before_code: Problematic snippet from the original source\n"
            "8. reason_for_correction: Why the corrected code is safer, better, or more efficient\n\n"
            "For security issues, hardcoded passwords, tokens, or printed secrets MUST be reported under security.issues with high or critical severity.\n"
            "For the top-level corrected_code array, include one object per corrected source file using its exact original project-relative file_name and the COMPLETE corrected contents of that entire file. Preserve all unaffected code. Never put a finding snippet, patch, or synthetic corrected_ filename in this array. If a complete corrected file cannot be produced, omit that file from the array; keep the precise patch only in the finding's after_code field.\n"
            "Keep your response accurate, grounded, and matching the complete schema."
        )
        system_review_instructions += (
            "\n\nUse these LangChain Pydantic output-format instructions exactly:\n"
            + review_output_parser.get_format_instructions()
        )

        try:
            if is_multi and len(retrieved_chunks) > 0:
                print("[Review] Invoking MULTI-AGENT collaborative review...")
                raw_answer = json.dumps(multi_agent_service.run_multi_agent_review(
                    config=active_cfg,
                    code_context=prompt,
                    question=question,
                    json_schema=GROQ_REVIEW_SCHEMA,
                    config_pool=crud.get_user_multi_agent_configs(user["id"]),
                    cancellation_event=cancellation_event,
                ))
            else:
                prov_name = active_cfg.get("provider", "Groq") if active_cfg else "Default Groq"
                print(f"[Review] Invoking SINGLE-AGENT review using provider: {prov_name}...")
                raw_answer = llm_service.call(
                    config=active_cfg,
                    system_prompt=system_review_instructions,
                    user_prompt=prompt,
                    json_schema=None,
                    use_json_mode=False,
                )
        except Exception as llm_err:
            ensure_review_not_cancelled()
            print(f"[Review] Primary LLM call notice ({llm_err}). Falling back to resilient cloud Groq...")
            try:
                raw_answer = llm_service._call_fallback_groq(
                    system_prompt=system_review_instructions,
                    user_prompt=prompt,
                    json_schema=None,
                    use_json_mode=False,
                )
            except Exception as fb_err:
                print(f"[Review] Fallback also failed ({fb_err}). Initializing structured grounded review...")
                raw_answer = "{}"

        ensure_review_not_cancelled()

        if not raw_answer:
            raw_answer = "{}"

        print("\nStructured AI response received.")

        # ====================================================
        # CLEAN & PARSE (WITH RESILIENT RECOVERY)
        # ====================================================
        cleaned_answer = clean_json_response(raw_answer)

        review_json = None
        try:
            review_json = json.loads(cleaned_answer)
        except Exception:
            for suffix in ["}", "\"]}", "]}", "\"}]}", "\"}}", "\"]}}", "}]}}", "\"}]}}", "}]}"] + [s + "}" for s in ["", "]", "}", "\"]", "\"}"]]:
                try:
                    cand = json.loads(cleaned_answer + suffix)
                    if isinstance(cand, dict):
                        review_json = cand
                        break
                except Exception:
                    continue

        if not isinstance(review_json, dict):
            try:
                # Give LangChain's Pydantic parser one chance to recover a
                # valid structured response (including a fenced JSON object).
                review_json = review_output_parser.parse(raw_answer).model_dump()
            except Exception as parser_error:
                raise HTTPException(
                    status_code=502,
                    detail=(
                        "The AI model did not return a valid structured review. "
                        "Please retry or choose another configured model."
                    ),
                ) from parser_error

        # ====================================================
        # CRITICAL SECURITY / ACCURACY FIX
        # ====================================================
        #
        # NEVER TRUST LLM FILE LIST.
        #
        # The backend owns this field.
        #
        # ====================================================

        review_json[
            "files_analyzed"
        ] = [
            file_info.model_dump()
            for file_info
            in trusted_files
        ]

        # ====================================================
        # TRUSTED PROJECT INFORMATION
        # ====================================================

        review_json[
            "project"
        ] = build_trusted_project_info(
            retrieved_chunks,
            rag_pipeline
            .get_project_metadata()
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
        # SANITIZE & NORMALIZE REVIEW JSON
        # ====================================================

        def_file = trusted_files[0].file_name if trusted_files else "app.py"
        review_json = sanitize_raw_review_json(review_json, default_file=def_file)

        # ====================================================
        # PYDANTIC VALIDATION (WITH GRACEFUL FALLBACK)
        # ====================================================

        try:
            validated_review = review_output_parser.parse(
                json.dumps(review_json, ensure_ascii=False)
            )
        except Exception as parser_error:
            print("\n[Review] LangChain Pydantic parser warning; retrying native Pydantic validation:", parser_error)
            try:
                validated_review = StructuredReview.model_validate(review_json)
            except ValidationError as validation_error:
                print("\n[Review] Critical Validation Error:", validation_error)
                raise HTTPException(
                    status_code=502,
                    detail="The AI review output could not be formatted into a structured audit."
                ) from validation_error

        # ====================================================
        # FINDING VALIDATION & GROUNDED SCORING
        # ====================================================

        validated_review = (
            validate_findings(
                validated_review
            )
        )

        # ====================================================
        # RESOLVE EFFECTIVE CATEGORY & STRICT CATEGORY ISOLATION
        # ====================================================

        resolved_category = req_category
        if not resolved_category:
            q_lower = question.lower()
            if any(w in q_lower for w in ["full review", "complete review", "entire project", "project-wide", "whole project"]):
                resolved_category = "full_review"
            elif any(w in q_lower for w in ["security", "vulnerab"]):
                resolved_category = "security"
            elif any(w in q_lower for w in ["performance", "bottleneck", "complexity"]):
                resolved_category = "performance"
            elif any(w in q_lower for w in ["quality", "clean code", "maintainab", "readab"]):
                resolved_category = "code_quality"
            elif any(w in q_lower for w in ["bug", "error"]):
                resolved_category = "bugs"
            else:
                resolved_category = "full_review"

        resolved_category = resolved_category.lower().strip()

        # Strict isolation (preserving calculated domain health score):
        if resolved_category in ("bugs", "bug"):
            validated_review.security = None
            validated_review.performance = None
            validated_review.code_quality = None
            validated_review.best_practices = None
            validated_review.review_types = ["bug_review", "error_review"]
        elif resolved_category in ("security", "sec"):
            validated_review.bugs = []
            validated_review.errors = []
            validated_review.performance = None
            validated_review.code_quality = None
            validated_review.best_practices = None
            validated_review.review_types = ["security"]
        elif resolved_category in ("performance", "perf"):
            validated_review.bugs = []
            validated_review.errors = []
            validated_review.security = None
            validated_review.code_quality = None
            validated_review.best_practices = None
            validated_review.review_types = ["performance"]
        elif resolved_category in ("code_quality", "quality"):
            validated_review.bugs = []
            validated_review.errors = []
            validated_review.security = None
            validated_review.performance = None
            validated_review.best_practices = None
            validated_review.review_types = ["code_quality"]
        else:  # full_review
            resolved_category = "full_review"
            validated_review.best_practices = None
            validated_review.review_types = [
                "full_review",
                "bug_review",
                "error_review",
                "security",
                "performance",
                "code_quality"
            ]

        # ====================================================
        # NORMALIZE (WITH CATEGORY AWARENESS)
        # ====================================================

        validated_review = (
            normalize_review(
                review=validated_review,
                question=question,
                category=resolved_category
            )
        )


        # ====================================================
        # FINAL FILE OVERRIDE
        # ====================================================
        #
        # Even after normalization, force the authoritative
        # current retrieval files one final time.
        #
        # ====================================================

        validated_review.files_analyzed = (
            trusted_files
        )

        # ====================================================
        # FINAL DEBUG
        # ====================================================

        print(
            "\n========== FINAL REVIEW FILES =========="
        )

        for file_info in (
            validated_review.files_analyzed
        ):

            print(
                file_info.file_name,
                "|",
                file_info.path
            )

        print(
            "Final File Count:",
            len(
                validated_review.files_analyzed
            )
        )

        print(
            "========================================\n"
        )

        # ====================================================
        # RESPONSE & SQLITE PERSISTENCE
        # ====================================================

        u = user
        review_id = str(uuid.uuid4())
        ensure_review_not_cancelled()

        if u["id"]:
            try:
                proj_name = (
                    validated_review.project.name
                    if validated_review.project and validated_review.project.name
                    else "Code Review"
                )
                proj_langs = (
                    ", ".join(validated_review.project.languages)
                    if validated_review.project and validated_review.project.languages
                    else "Source"
                )
                bugs_cnt = len(validated_review.bugs) if validated_review.bugs else 0
                sec_cnt = validated_review.security.issues_found if validated_review.security else 0
                perf_cnt = len(validated_review.performance.issues) if (validated_review.performance and validated_review.performance.issues) else 0
                qual_cnt = 0
                if validated_review.code_quality:
                    qual_cnt = len(validated_review.code_quality.observations or []) + len(validated_review.code_quality.suggestions or [])
                total_issues = bugs_cnt + sec_cnt + perf_cnt + qual_cnt

                review_dict = validated_review.model_dump()
                review_dict["agent_mode"] = "multi" if is_multi else "single"
                review_dict["audited_by"] = {
                    "id": u["id"],
                    "name": u.get("name") or (u.get("email", "").split("@")[0] if u.get("email") else "Developer"),
                    "email": u.get("email")
                }

                crud.create_review(
                    review_id=review_id,
                    user_id=u["id"],
                    project_name=proj_name,
                    language=proj_langs,
                    question=question,
                    score=getattr(validated_review, "score", None),
                    confidence=getattr(validated_review, "confidence", None),
                    issue_count=total_issues,
                    bugs_count=bugs_cnt,
                    security_count=sec_cnt,
                    performance_count=perf_cnt,
                    quality_count=qual_cnt,
                    raw_review=review_dict
                )
                print(f"[DB] Review saved to SQLite for user {u['id']}: {review_id} (mode: {'multi' if is_multi else 'single'})")
            except Exception as db_err:
                print(f"[DB] Error saving review to SQLite: {repr(db_err)}")
        else:
            review_dict = validated_review.model_dump()
            review_dict["agent_mode"] = "multi" if is_multi else "single"
            review_dict["audited_by"] = {
                "id": u.get("id"),
                "name": u.get("name") or "Developer",
                "email": u.get("email")
            }

        return {
            "success": True,
            "id": review_id,
            "category": resolved_category,
            "question": question,
            "agent_mode": "multi" if is_multi else "single",
            "audited_by": review_dict.get("audited_by"),
            "review_types": (
                validated_review
                .review_types
            ),
            "review": review_dict
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
                    "generate a response matching "
                    "the structured review schema."
                )
            )

        # ----------------------------------------------------
        # RATE LIMIT
        # ----------------------------------------------------

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
                    "AI provider authentication failed. "
                    "Check GROQ_API_KEY in .env."
                )
            )

        # ----------------------------------------------------
        # MODEL
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
                    "The configured Groq model is "
                    "not available to this API key."
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
        ):

            raise HTTPException(
                status_code=413,
                detail=(
                    "The retrieved code and prompt "
                    "are too large for the current "
                    "AI model limit."
                )
            )

        if (
            "out of memory" in error_text.lower()
            or "out-of-memory" in error_text.lower()
            or "allocate buffer" in error_text.lower()
        ):
            raise HTTPException(
                status_code=500,
                detail=error_text if len(error_text) < 200 else "Ollama ran out of memory. Try switching to a lighter model (like llama3.2:3b) in Configuration ⚙️."
            )

        # ----------------------------------------------------
        # GENERIC
        # ----------------------------------------------------

        clean_detail = error_text.strip() if error_text else "Failed to generate code review."
        if len(clean_detail) > 250:
            clean_detail = clean_detail[:250] + "..."

        raise HTTPException(
            status_code=500,
            detail=clean_detail
        )

    finally:
        if cancellation_event:
            with _review_cancellations_lock:
                registered = _review_cancellations.get(cancellation_registry_key)
                if registered and registered.get("event") is cancellation_event:
                    _review_cancellations.pop(cancellation_registry_key, None)


class CancelReviewRequest(BaseModel):
    request_id: str


@app.post("/review/cancel")
def cancel_review(payload: CancelReviewRequest, request: Request):
    user = get_request_user(request)
    registry_key = f"{user['id']}:{payload.request_id}"
    with _review_cancellations_lock:
        active = _review_cancellations.get(registry_key)
        if active:
            active["event"].set()
        else:
            # Remember a short-lived early cancellation in case it races the review request.
            event = threading.Event()
            event.set()
            _review_cancellations[registry_key] = {
                "user_id": user["id"],
                "event": event,
                "expires_at": time.monotonic() + 120,
            }
    return {"success": True, "cancelled": True}


# ============================================================
# SMTP CONFIGURATION & TEST ENDPOINTS
# ============================================================

# ============================================================
# LLM CONFIGURATION & PREFERENCES ENDPOINTS
# ============================================================

class LLMConfigItemRequest(BaseModel):
    id: Optional[str] = None
    config_name: str
    provider: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model_name: str
    temperature: float = 0.1
    max_tokens: int = 4096
    is_active: bool = False


class UserPreferencesRequest(BaseModel):
    theme: Optional[str] = None
    agent_mode: Optional[str] = None
    email_api_url: Optional[str] = None


class MultiAgentModelsRequest(BaseModel):
    config_ids: List[str]


class SingleAgentModelRequest(BaseModel):
    config_id: str


class TestLLMConfigRequest(BaseModel):
    provider: str
    model_name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None


@app.get("/api/config/llm")
def list_llm_configs(request: Request):
    user = get_request_user(request)
    configs = crud.list_user_llm_configs(user["id"])
    return {"success": True, "configs": configs}


@app.get("/api/config/multi-agent-models")
def list_multi_agent_models(request: Request):
    user = get_request_user(request)
    return {"success": True, "config_ids": crud.get_user_multi_agent_config_ids(user["id"])}


@app.put("/api/config/multi-agent-models")
def update_multi_agent_models(payload: MultiAgentModelsRequest, request: Request):
    user = get_request_user(request)
    if not crud.set_user_multi_agent_config_ids(user["id"], payload.config_ids):
        raise HTTPException(status_code=400, detail="One or more selected models are unavailable.")
    return {"success": True, "config_ids": crud.get_user_multi_agent_config_ids(user["id"])}


@app.get("/api/config/single-agent-model")
def get_single_agent_model(request: Request):
    user = get_request_user(request)
    return {"success": True, "config_id": crud.get_user_single_agent_config_id(user["id"])}


@app.put("/api/config/single-agent-model")
def update_single_agent_model(payload: SingleAgentModelRequest, request: Request):
    user = get_request_user(request)
    if not crud.set_user_single_agent_config_id(user["id"], payload.config_id):
        raise HTTPException(status_code=400, detail="The selected model is unavailable.")
    return {"success": True, "config_id": payload.config_id}


@app.post("/api/config/llm")
def save_user_llm_config(payload: LLMConfigItemRequest, request: Request):
    user = get_request_user(request)
    import uuid
    config_id = payload.id or f"cfg_{uuid.uuid4().hex[:12]}"
    saved = crud.save_llm_config(
        config_id=config_id,
        user_id=user["id"],
        config_name=payload.config_name.strip(),
        provider=payload.provider.strip(),
        api_key=payload.api_key.strip() if payload.api_key else None,
        base_url=payload.base_url.strip() if payload.base_url else None,
        model_name=payload.model_name.strip(),
        temperature=payload.temperature,
        max_tokens=payload.max_tokens,
        is_active=payload.is_active
    )
    return {"success": True, "config": saved}


@app.post("/api/config/llm/{config_id}/activate")
def activate_user_llm_config(config_id: str, request: Request):
    user = get_request_user(request)
    ok = crud.set_active_llm_config(config_id, user["id"])
    return {"success": ok}


@app.delete("/api/config/llm/{config_id}")
def delete_user_llm_config(config_id: str, request: Request):
    user = get_request_user(request)
    ok = crud.delete_llm_config(config_id, user["id"])
    return {"success": ok}


@app.post("/api/config/llm/test")
def test_llm_config(payload: TestLLMConfigRequest, request: Request):
    get_request_user(request)
    ok, msg = llm_service.test_connection(
        provider=payload.provider,
        model_name=payload.model_name,
        api_key=payload.api_key,
        base_url=payload.base_url
    )
    return {"success": ok, "message": msg}


@app.get("/api/config/preferences")
def get_preferences(request: Request):
    user = get_request_user(request)
    prefs = crud.get_user_preferences(user["id"])
    return {"success": True, "preferences": prefs}


@app.put("/api/config/preferences")
def update_preferences(payload: UserPreferencesRequest, request: Request):
    user = get_request_user(request)
    updated = crud.upsert_user_preferences(
        user_id=user["id"],
        theme=payload.theme,
        agent_mode=payload.agent_mode,
        email_api_url=payload.email_api_url
    )
    return {"success": True, "preferences": updated}


@app.get("/api/ollama/models")
def list_ollama_models(request: Request, base_url: str = "http://localhost:11434"):
    get_request_user(request)
    clean_url = base_url.rstrip("/")
    try:
        res = requests.get(f"{clean_url}/api/tags", timeout=5)
        if res.status_code == 200:
            models = res.json().get("models", [])
            return {
                "success": True,
                "models": [{"name": m.get("name"), "size": m.get("size")} for m in models]
            }
        return {"success": False, "models": [], "error": f"HTTP {res.status_code}"}
    except Exception as e:
        return {"success": False, "models": [], "error": str(e)}


# ============================================================
# CONTACT FORM ENDPOINT (via Hosted Email API)
# ============================================================

class ContactRequest(BaseModel):
    name: str
    email: str
    subject: str
    message: str


@app.post("/api/contact")
def submit_contact_form(payload: ContactRequest):
    result = email_service.send_contact_message(
        from_name=payload.name.strip(),
        from_email=payload.email.strip(),
        subject=payload.subject.strip(),
        message=payload.message.strip()
    )
    return result


# ============================================================
# GITHUB APP INTEGRATION ENDPOINTS
# ============================================================

class GitHubConnectRequest(BaseModel):
    username: str
    token: str
    installation_id: Optional[str] = None


class GitHubPushFixRequest(BaseModel):
    owner: str
    repo: str
    base_branch: str = "main"
    corrected_files: List[Dict[str, str]]
    pr_title: Optional[str] = None
    pr_body: Optional[str] = None


def get_effective_github_token(conn: Optional[Dict[str, Any]]) -> str:
    if not conn:
        return ""
    if conn.get("installation_id") and github_app_service.find_private_key():
        try:
            return github_app_service.get_installation_access_token(str(conn["installation_id"]))
        except Exception as e:
            print("[GitHub] Installation token refresh error:", e)
    return conn.get("oauth_token", "")


class RefineFixRequest(BaseModel):
    file_name: str
    before_code: str
    current_fix: str
    instruction: str


@app.post("/api/review/refine-fix")
def refine_code_fix_endpoint(payload: RefineFixRequest, request: Request):
    """
    Jules-style interactive fix refinement. Allows the user to ask the AI to modify
    a proposed correction before accepting and pushing it to GitHub.
    """
    user = get_request_user(request)
    cfg = crud.get_user_single_agent_config(user["id"])

    system_prompt = (
        "You are an expert AI software engineer modifying a proposed code correction.\n"
        "The user will provide the original code snippet, the currently proposed fix, and a specific refinement instruction.\n"
        "Your task: revise the code correction to satisfy the user instruction while maintaining correctness and security.\n"
        "Output ONLY valid JSON with keys: corrected_code (string with the revised code) and explanation (string with brief note of changes).\n"
        "Do not wrap in markdown fences."
    )

    user_prompt = (
        f"File: {payload.file_name}\n"
        f"Original Code:\n{payload.before_code}\n\n"
        f"Current Proposed Fix:\n{payload.current_fix}\n\n"
        f"User Refinement Instruction:\n{payload.instruction}\n\n"
        f"Please generate the revised corrected code now as JSON."
    )

    try:
        raw = llm_service.call(cfg, system_prompt, user_prompt, None)
        clean = raw.strip()
        if clean.startswith("```"):
            lines = clean.split("\n")
            clean = "\n".join(lines[1:-1] if lines[-1].strip().startswith("```") else lines[1:])
        data = json.loads(clean.strip())
        return {
            "success": True,
            "corrected_code": data.get("corrected_code", payload.current_fix),
            "explanation": data.get("explanation", "Refined with user instruction.")
        }
    except Exception as e:
        print("[RefineFix] Notice:", e)
        return {
            "success": True,
            "corrected_code": payload.current_fix,
            "explanation": f"Notice: Refinement error: {e}"
        }


@app.get("/api/github/status")
def get_github_status(request: Request, response: Response):
    user = get_request_user(request)
    conn = crud.get_github_connection(user["id"])
    has_pem = bool(github_app_service.find_private_key())
    install_url = f"https://github.com/apps/{GitHubAppService.APP_NAME}/installations/new?state={user['id']}"

    # Set cookie so browser redirect back from GitHub App installation retains user context
    response.set_cookie(
        key="pending_github_user_id", value=user["id"], max_age=3600,
        samesite="lax", httponly=True, secure=APP_ENV != "development",
    )

    detected_installations = []
    if has_pem:
        try:
            jwt_token = github_app_service.generate_jwt()
            res = requests.get(
                f"{github_app_service.BASE_API}/app/installations",
                headers={"Authorization": f"Bearer {jwt_token}", "Accept": "application/vnd.github+json"},
                timeout=8
            )
            if res.status_code == 200:
                for inst in res.json():
                    detected_installations.append({
                        "id": str(inst.get("id")),
                        "account": inst.get("account", {}).get("login"),
                    })
        except Exception as e:
            print("[GitHub] Installation lookup error:", e)

    # Validate existing connection: only clear if detected_installations is non-empty and verified missing
    if conn and conn.get("installation_id") and has_pem and len(detected_installations) > 0:
        valid_ids = {str(inst["id"]) for inst in detected_installations}
        if str(conn.get("installation_id")) not in valid_ids:
            crud.delete_github_connection(user["id"])
            conn = None

    # AUTO-SYNC: If user is not yet connected in SQLite, attempt smart normalized matching
    if not conn and detected_installations:
        user_email = (user.get("email") or "").lower().strip()
        user_email_prefix = user_email.split("@")[0] if user_email else ""
        norm_email_prefix = "".join(c for c in user_email_prefix if c.isalnum())
        user_name = (user.get("name") or "").lower().strip()
        name_parts = ["".join(c for c in p if c.isalnum()) for p in user_name.replace("-", " ").replace("_", " ").split() if len(p) >= 3]
        header_gh = (request.headers.get("x-user-github-username") or "").lower().strip().lstrip("@")
        norm_header_gh = "".join(c for c in header_gh if c.isalnum())

        matched_inst = None
        for inst in detected_installations:
            acct = (inst.get("account") or "").lower().strip()
            norm_acct = "".join(c for c in acct if c.isalnum())
            # 1. Header GH username match (from Clerk external accounts or profile)
            if norm_header_gh and (norm_acct == norm_header_gh or norm_header_gh in norm_acct):
                matched_inst = inst
                break
            # 2. Normalized email prefix match (e.g. technova.cseai matches technovacseai)
            if norm_email_prefix and norm_email_prefix not in ("default", "localuser") and (norm_acct == norm_email_prefix or norm_acct in norm_email_prefix or norm_email_prefix in norm_acct):
                matched_inst = inst
                break
            # 3. Name tokens match (e.g. "sidhardha" or "reddy" in "reddy-sidhardha24")
            if name_parts and any(p in norm_acct for p in name_parts):
                matched_inst = inst
                break

        # If an installation matches this authenticated user, link it
        if matched_inst:
            crud.save_github_connection(
                user_id=user["id"],
                github_username=matched_inst["account"],
                oauth_token="",
                installation_id=str(matched_inst["id"])
            )
            conn = crud.get_github_connection(user["id"])

    # PRIVACY: Return ONLY the current user's connection status. NEVER expose other users' installations.
    if conn and conn.get("github_username"):
        return {
            "connected": True,
            "username": conn.get("github_username"),
            "installation_id": conn.get("installation_id"),
            "connected_at": conn.get("connected_at"),
            "has_pem": has_pem,
            "install_url": install_url,
            "app_name": GitHubAppService.APP_NAME,
            "client_id": GitHubAppService.CLIENT_ID
        }

    return {
        "connected": False,
        "username": None,
        "installation_id": None,
        "has_pem": has_pem,
        "install_url": install_url,
        "app_name": GitHubAppService.APP_NAME,
        "client_id": GitHubAppService.CLIENT_ID
    }


@app.get("/api/github/auth-url")
def get_github_auth_url(request: Request, response: Response):
    user = get_request_user(request)
    response.set_cookie(
        key="pending_github_user_id", value=user["id"], max_age=3600,
        samesite="lax", httponly=True, secure=APP_ENV != "development",
    )
    return {
        "install_url": f"https://github.com/apps/{GitHubAppService.APP_NAME}/installations/new?state={user['id']}",
        "app_url": f"https://github.com/apps/{GitHubAppService.APP_NAME}",
        "client_id": GitHubAppService.CLIENT_ID
    }


@app.get("/api/github/callback")
def github_installation_callback(
    installation_id: Optional[str] = None,
    setup_action: Optional[str] = None,
    state: Optional[str] = None,
    request: Request = None
):
    """
    Handles GitHub App post-installation redirect from GitHub.
    Receives installation_id and state/cookie (user_id), resolves the account login,
    and binds the installation specifically to that user.
    """
    from fastapi.responses import RedirectResponse

    cookie_user_id = request.cookies.get("pending_github_user_id") if request else None
    if not cookie_user_id or not state or state != cookie_user_id:
        return RedirectResponse(url="/configuration?github_error=invalid_installation_state")

    user_id = cookie_user_id
    if not installation_id:
        response = RedirectResponse(url="/configuration?github_error=missing_installation_id")
        response.delete_cookie("pending_github_user_id")
        return response

    account_login = "User"
    try:
        jwt_token = github_app_service.generate_jwt()
        res = requests.get(
            f"{github_app_service.BASE_API}/app/installations/{installation_id}",
            headers={"Authorization": f"Bearer {jwt_token}", "Accept": "application/vnd.github+json"},
            timeout=10
        )
        if res.status_code != 200:
            raise HTTPException(status_code=400, detail="GitHub installation could not be verified.")
        inst_data = res.json()
        account_login = inst_data.get("account", {}).get("login", "User")
    except Exception as e:
        print("[GitHub] Callback installation lookup error:", e)
        response = RedirectResponse(url="/configuration?github_error=installation_verification_failed")
        response.delete_cookie("pending_github_user_id")
        return response

    crud.save_github_connection(
        user_id=user_id,
        github_username=account_login,
        oauth_token="",
        installation_id=str(installation_id)
    )

    # Pass installation_id in redirect so frontend can bind to the browser's logged-in session
    redirect_resp = RedirectResponse(url=f"/configuration?installation_id={installation_id}&github_connected=1&account={account_login}")
    redirect_resp.delete_cookie("pending_github_user_id")
    return redirect_resp


@app.post("/api/github/connect-app")
def connect_via_github_app(request: Request, payload: Optional[Dict[str, Any]] = None):
    """
    Connect via GitHub App:
    Supports:
    1. Direct linking via github_username (e.g. {"github_username": "reddy-sidhardha24"})
    2. Direct linking via installation_id (e.g. {"installation_id": "170625746"})
    3. Smart auto-detection across active GitHub installations
    """
    user = get_request_user(request)
    cookie_uid = request.cookies.get("pending_github_user_id")
    target_uid = cookie_uid if (cookie_uid and user["id"] == "default_user") else user["id"]

    if not github_app_service.find_private_key():
        raise HTTPException(status_code=400, detail="GitHub App private key (.pem) not found on backend.")

    payload = payload or {}
    inst_id = payload.get("installation_id")
    target_username = (
        payload.get("github_username")
        or payload.get("username")
        or request.headers.get("x-user-github-username")
        or ""
    ).strip().lstrip("@")

    jwt_token = github_app_service.generate_jwt()

    # 1. If inst_id was explicitly provided (e.g. from callback or direct ID), verify and bind directly
    if inst_id:
        try:
            res = requests.get(
                f"{github_app_service.BASE_API}/app/installations/{inst_id}",
                headers={"Authorization": f"Bearer {jwt_token}", "Accept": "application/vnd.github+json"},
                timeout=10
            )
            if res.status_code == 200:
                resolved_username = res.json().get("account", {}).get("login", "User")
                crud.save_github_connection(
                    user_id=target_uid,
                    github_username=resolved_username,
                    oauth_token="",
                    installation_id=str(inst_id)
                )
                return {
                    "success": True,
                    "username": resolved_username,
                    "installation_id": str(inst_id),
                    "message": f"Successfully connected as @{resolved_username}!"
                }
            else:
                raise HTTPException(status_code=400, detail="Could not verify GitHub App installation with GitHub API.")
        except HTTPException:
            raise
        except Exception as err:
            raise HTTPException(status_code=500, detail=f"Failed to verify installation {inst_id}: {str(err)}")

    # 2. If target_username was provided, match against active GitHub App installations
    clean_target = target_username.rstrip("/").split("/")[-1].replace("@", "").strip().lower()
    if clean_target and clean_target != "user":
        try:
            res = requests.get(
                f"{github_app_service.BASE_API}/app/installations",
                headers={"Authorization": f"Bearer {jwt_token}", "Accept": "application/vnd.github+json"},
                timeout=10
            )
            if res.status_code == 200:
                insts = res.json()
                matched = None
                norm_target = "".join(c for c in clean_target if c.isalnum())
                for itm in insts:
                    login = (itm.get("account", {}).get("login") or "").lower()
                    norm_login = "".join(c for c in login if c.isalnum())
                    if norm_login == norm_target or login == clean_target or clean_target in login or login in clean_target:
                        matched = itm
                        break
                if matched:
                    inst_id = str(matched["id"])
                    resolved_username = matched.get("account", {}).get("login", clean_target)
                    crud.save_github_connection(
                        user_id=target_uid,
                        github_username=resolved_username,
                        oauth_token="",
                        installation_id=inst_id
                    )
                    return {
                        "success": True,
                        "username": resolved_username,
                        "installation_id": inst_id,
                        "message": f"Successfully linked GitHub account @{resolved_username}!"
                    }
                else:
                    raise HTTPException(
                        status_code=404,
                        detail=f"No GitHub App installation found for @{clean_target}. Please make sure you have installed the GitHub App on your GitHub account first."
                    )
        except HTTPException:
            raise
        except Exception as e:
            print("[GitHub] Username lookup error:", e)
            raise HTTPException(status_code=500, detail=f"Failed to verify GitHub installation for @{clean_target}: {str(e)}")

    # 3. Auto-detection fallback: search installations on GitHub
    try:
        res = requests.get(
            f"{github_app_service.BASE_API}/app/installations",
            headers={"Authorization": f"Bearer {jwt_token}", "Accept": "application/vnd.github+json"},
            timeout=10
        )
        if res.status_code == 200 and res.json():
            insts = res.json()
            user_email = (user.get("email") or "").lower().strip()
            user_prefix = user_email.split("@")[0] if user_email else ""
            user_name = (user.get("name") or "").lower().strip()
            name_parts = [p for p in user_name.replace("-", " ").replace("_", " ").split() if len(p) >= 3]

            matched = None
            for itm in insts:
                acct = (itm.get("account", {}).get("login") or "").lower().strip()
                # Email prefix match
                if user_prefix and user_prefix not in ("default", "localuser") and (acct == user_prefix or acct in user_prefix or user_prefix in acct):
                    matched = itm
                    break
                # Name tokens match (e.g. "sidhardha" or "reddy" in "reddy-sidhardha24")
                if name_parts and any(p in acct for p in name_parts):
                    matched = itm
                    break

            if matched:
                inst_id = str(matched["id"])
                resolved_username = matched.get("account", {}).get("login", "User")
                crud.save_github_connection(
                    user_id=target_uid,
                    github_username=resolved_username,
                    oauth_token="",
                    installation_id=inst_id
                )
                return {
                    "success": True,
                    "username": resolved_username,
                    "installation_id": inst_id,
                    "message": f"Successfully auto-detected and linked @{resolved_username}!"
                }
    except Exception as e:
        print("[GitHub] Auto-detection error:", e)

    raise HTTPException(
        status_code=400,
        detail="Please enter your GitHub username or click 'Install GitHub App' to authorize."
    )


@app.post("/api/github/connect")
def connect_github_account(payload: GitHubConnectRequest, request: Request):
    user = get_request_user(request)
    crud.save_github_connection(
        user_id=user["id"],
        github_username=payload.username.strip(),
        oauth_token=payload.token.strip(),
        installation_id=payload.installation_id
    )
    return {"success": True, "message": "GitHub account successfully linked."}


@app.post("/api/github/disconnect")
def disconnect_github_account(request: Request):
    user = get_request_user(request)
    crud.delete_github_connection(user["id"])
    return {"success": True, "message": "GitHub account disconnected."}


@app.get("/api/github/repos")
def list_github_repositories(request: Request):
    user = get_request_user(request)
    conn = crud.get_github_connection(user["id"])
    token = get_effective_github_token(conn)
    if not token:
        raise HTTPException(status_code=400, detail="GitHub account not connected.")

    repos = github_app_service.list_accessible_repositories(
        auth_token=token,
        installation_id=conn.get("installation_id") if conn else None
    )
    return {"success": True, "repositories": repos}


@app.get("/api/github/repos/{owner}/{repo}/branches")
def list_repo_branches(owner: str, repo: str, request: Request):
    user = get_request_user(request)
    cookie_uid = request.cookies.get("pending_github_user_id")
    target_uid = cookie_uid if (cookie_uid and user["id"] == "default_user") else user["id"]
    conn = crud.get_github_connection(target_uid)
    if not conn and owner:
        conn = crud.get_github_connection_by_username(owner)
    token = get_effective_github_token(conn)
    branches = github_app_service.get_repo_branches(auth_token=token, owner=owner, repo=repo)
    return {"success": True, "branches": branches}


@app.post("/api/github/push-fix")
def push_github_fix(payload: GitHubPushFixRequest, request: Request):
    user = get_request_user(request)
    cookie_uid = request.cookies.get("pending_github_user_id")
    target_uid = cookie_uid if (cookie_uid and user["id"] == "default_user") else user["id"]
    conn = crud.get_github_connection(target_uid)

    repo_name = (payload.repo or "project").strip()
    owner_name = (payload.owner or "").strip()
    if "/" in repo_name:
        parts = repo_name.split("/")
        if not owner_name or owner_name == "default_user":
            owner_name = parts[0].strip()
        repo_name = parts[-1].strip()

    if not conn and owner_name:
        conn = crud.get_github_connection_by_username(owner_name)
    token = get_effective_github_token(conn)
    if not token:
        raise HTTPException(status_code=400, detail="GitHub account not connected. Please connect your GitHub account in Configuration or Upload tab.")

    try:
        pr_result = github_app_service.push_review_fixes_and_open_pr(
            auth_token=token,
            owner=owner_name,
            repo=repo_name,
            base_branch=payload.base_branch,
            corrected_files=payload.corrected_files,
            pr_title=payload.pr_title,
            pr_body=payload.pr_body
        )
        return pr_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




# ============================================================
# EMAIL DELIVERY ENDPOINTS (HOSTED EMAIL API)
# ============================================================

@app.get("/api/smtp-config")
def get_smtp_config(request: Request):
    get_request_user(request)
    return email_service.get_config_status()


@app.post("/api/send-email")
def send_review_email_endpoint(payload: SendEmailRequest, request: Request):
    get_request_user(request)
    try:
        email = payload.email.strip()
        if not email or "@" not in email:
            raise HTTPException(status_code=400, detail="Invalid client email address format.")

        review_data = payload.review_data or {}
        report_markdown = payload.report_markdown
        category = payload.category or "full_review"

        # Generate PDF report for attachment
        pdf_bytes = None
        try:
            pdf_bytes = report_service.generate_pdf(review_data, category=category)
        except Exception as pdf_err:
            print(f"[PDF] Notice: Optional PDF attachment rendering skipped: {pdf_err}")

        result = email_service.send_review_email(
            recipient_email=email,
            review_data=review_data,
            category=category,
            report_markdown=report_markdown,
            pdf_bytes=pdf_bytes
        )

        return result
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API Email Error]: {repr(e)}")
        return {"success": False, "message": f"Delivery error: {str(e)}"}


# ============================================================
# REPORT & CORRECTED CODE DOWNLOAD ENDPOINTS (PDF, MD, HTML, ZIP)
# ============================================================

class DownloadReportRequest(BaseModel):
    review_data: Dict[str, Any]
    category: str = "full_review"
    format: str = "markdown"  # "pdf" | "markdown" | "html"


@app.post("/api/download-report")
def download_review_report_endpoint(payload: DownloadReportRequest, request: Request):
    get_request_user(request)
    from fastapi.responses import Response
    fmt = payload.format.lower().strip()
    category = payload.category or "full_review"
    review_data = payload.review_data or {}
    project_name = (review_data.get("project") or {}).get("name") or "Code_Review"
    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in project_name)

    if fmt == "pdf":
        pdf_bytes = report_service.generate_pdf(review_data, category=category)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{safe_name}_Audit_Report.pdf"'}
        )
    elif fmt == "html":
        html_content = report_service.generate_html(review_data, category=category)
        return Response(
            content=html_content,
            media_type="text/html",
            headers={"Content-Disposition": f'attachment; filename="{safe_name}_Audit_Report.html"'}
        )
    else:
        # Default Markdown
        md_content = report_service.generate_markdown(review_data, category=category)
        return Response(
            content=md_content,
            media_type="text/markdown",
            headers={"Content-Disposition": f'attachment; filename="{safe_name}_Audit_Report.md"'}
        )


def generate_complete_corrected_files(source_dir: Path, review_data: Dict[str, Any], user_id: str) -> None:
    """Ask the selected review model for whole-file corrections before ZIP packaging."""
    root = source_dir.resolve()
    existing_outputs = code_correction_service.extract_full_file_correction_map(review_data)
    complete_by_path: Dict[str, str] = {}

    for requested_path, code in existing_outputs.items():
        source_file = code_correction_service._resolve_project_file(root, requested_path)
        try:
            rel_path = source_file.relative_to(root).as_posix()
        except ValueError:
            continue
        complete_by_path[rel_path] = code

    findings_by_path: Dict[str, List[Dict[str, Any]]] = {}
    for finding in code_correction_service._iter_findings(review_data):
        if not (finding.get("after_code") or finding.get("corrected_code")):
            continue
        requested_path = code_correction_service._safe_relative_path(finding.get("file"))
        if not requested_path:
            continue
        source_file = code_correction_service._resolve_project_file(root, requested_path)
        if not source_file.is_file():
            continue
        rel_path = source_file.relative_to(root).as_posix()
        if rel_path not in complete_by_path:
            findings_by_path.setdefault(rel_path, []).append(finding)

    if not findings_by_path:
        review_data["corrected_code"] = [
            {"file_name": name, "code": code}
            for name, code in complete_by_path.items()
        ]
        review_data["_complete_file_corrections"] = True
        return

    model_config = crud.get_user_single_agent_config(user_id)
    complete_file_prompt = (
        "You are repairing one existing source file based on grounded code review findings. "
        'Return JSON only, in the exact shape {"code": "<complete corrected file>"}. '
        "The code value MUST contain the entire file from its first line to its last line, not a diff, "
        "snippet, replacement function, or excerpt. Apply all listed fixes, preserve every unrelated "
        "declaration and behavior, and retain the original file's language and structure. Do not add a "
        "corrected_ filename or markdown fences. If the findings are inconsistent, make the smallest "
        "safe correction that addresses them while preserving the rest of the file."
    )

    for rel_path, findings in findings_by_path.items():
        source_file = root / rel_path
        try:
            source_text = source_file.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise HTTPException(
                status_code=422,
                detail=f"Could not read the complete source file {Path(rel_path).name} for correction.",
            ) from exc

        fix_context = []
        for finding in findings:
            fix_context.append({
                "title": finding.get("title"),
                "severity": finding.get("severity"),
                "line": finding.get("line"),
                "description": finding.get("description") or finding.get("explanation"),
                "suggested_solution": finding.get("suggested_solution") or finding.get("fix"),
                "before_code": finding.get("before_code"),
                "after_code": finding.get("after_code") or finding.get("corrected_code"),
                "reason_for_correction": finding.get("reason_for_correction"),
            })

        user_prompt = (
            f"Original project-relative file path: {rel_path}\n\n"
            f"Review findings and proposed changes:\n{json.dumps(fix_context, ensure_ascii=False, indent=2)}\n\n"
            "Complete original source file (preserve all unaffected lines):\n"
            f"<source_file>\n{source_text}\n</source_file>"
        )

        try:
            raw_output = llm_service.call(
                config=model_config,
                system_prompt=complete_file_prompt,
                user_prompt=user_prompt,
                json_schema=None,
            )
            parsed_output = json.loads(clean_json_response(raw_output))
            full_code = parsed_output.get("code") or parsed_output.get("corrected_code")
        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Could not generate a complete corrected file for {Path(rel_path).name}: {exc}",
            ) from exc

        if not isinstance(full_code, str) or not full_code.strip():
            raise HTTPException(
                status_code=502,
                detail=f"The model did not return complete corrected contents for {Path(rel_path).name}.",
            )
        complete_by_path[rel_path] = full_code

    # Replace synthetic snippets with complete file contents before the service
    # copies and edits the original project tree.
    review_data["corrected_code"] = [
        {"file_name": name, "code": code}
        for name, code in complete_by_path.items()
    ]
    review_data["_complete_file_corrections"] = True


@app.post("/api/download-corrected-project")
def download_corrected_project_zip(payload: Dict[str, Any], request: Request):
    user = get_request_user(request)
    user_key = hashlib.sha256(user["id"].encode("utf-8")).hexdigest()
    user_extract_dir = EXTRACT_DIR / "users" / user_key
    user_upload_dir = USER_DATA_DIR / user_key / "uploads"
    user_extract_dir.mkdir(parents=True, exist_ok=True)
    from fastapi.responses import Response
    review_data = payload.get("review_data") or {}

    project_name = (
        payload.get("project_name")
        or payload.get("projectName")
        or (review_data.get("project") or {}).get("name")
        or review_data.get("project_name")
        or ""
    ).strip()

    target_dir = None
    if project_name:
        extraction_root = user_extract_dir.resolve()
        exact_path = (extraction_root / project_name).resolve()
        try:
            exact_path.relative_to(extraction_root)
            is_safe_path = exact_path != extraction_root
        except ValueError:
            is_safe_path = False
        if is_safe_path and exact_path.is_dir():
            target_dir = exact_path
        else:
            clean_pname = Path(project_name).stem.lower()
            for item in user_extract_dir.iterdir():
                if not item.is_symlink() and item.is_dir() and (
                    item.name.lower() == clean_pname
                    or item.name.lower() == project_name.lower()
                    or item.name.lower().startswith(clean_pname + "_")
                ):
                    target_dir = item
                    break

    # If still not found, check files_analyzed to locate the specific project directory
    if not target_dir:
        files_analyzed = review_data.get("files_analyzed") or []
        for project_root in (user_extract_dir, user_upload_dir):
            if not project_root.is_dir():
                continue
            for item in files_analyzed:
                fname = item if isinstance(item, str) else (item.get("file_name") or item.get("path") or "")
                if fname:
                    base_fname = Path(fname).name
                    for d in project_root.iterdir():
                        if not d.is_symlink() and d.is_dir() and ((d / fname).exists() or any(d.rglob(base_fname))):
                            target_dir = d
                            break
                if target_dir:
                    break
            if target_dir:
                break

    if target_dir is None and user_upload_dir.is_dir():
        project_name_lower = Path(project_name).stem.lower()
        upload_projects = [p for p in user_upload_dir.iterdir() if p.is_dir() and not p.is_symlink()]
        if len(upload_projects) == 1:
            target_dir = upload_projects[0]
        elif project_name_lower:
            target_dir = next(
                (p for p in upload_projects if p.name.lower().startswith(project_name_lower)),
                None,
            )

    if target_dir is None:
        raise HTTPException(status_code=404, detail="The reviewed project could not be found in your workspace.")

    source_dir = str(target_dir)

    generate_complete_corrected_files(Path(source_dir), review_data, user["id"])

    try:
        zip_bytes = code_correction_service.build_full_project_zip(
            source_dir=source_dir,
            review_data=review_data
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in (project_name or "Project"))
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{safe_name}_Corrected_Full.zip"'}
    )


@app.post("/api/download-corrected-files")
def download_corrected_files_only_zip(payload: Dict[str, Any], request: Request):
    get_request_user(request)
    from fastapi.responses import Response
    review_data = payload.get("review_data") or {}

    zip_bytes = code_correction_service.build_corrected_only_zip(review_data=review_data)

    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="Corrected_Files_Only.zip"'}
    )


@app.post("/api/download-code")
def download_corrected_code_endpoint(payload: Dict[str, Any], request: Request):
    get_request_user(request)
    from fastapi.responses import Response
    review_data = payload.get("review_data") or {}
    code_content = email_service.generate_corrected_code_content(review_data)

    return Response(
        content=code_content,
        media_type="text/plain",
        headers={"Content-Disposition": 'attachment; filename="Corrected_Code.txt"'}
    )


# ============================================================
# SPA CLIENT-SIDE FALLBACK ROUTE
# ============================================================

@app.get("/{full_path:path}", include_in_schema=False)

async def serve_spa(full_path: str):
    target = FRONTEND_BUILD_DIR / full_path
    if full_path and target.exists() and target.is_file():
        return FileResponse(target)

    index_file = FRONTEND_BUILD_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file, headers={"Cache-Control": "no-cache, no-store, must-revalidate"})

    raise HTTPException(status_code=404, detail="Page not found")
