# ============================================================
# AI CODE REVIEW ASSISTANT
# backend/services/security_service.py
# ============================================================

import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Tuple, List, Optional
from fastapi import HTTPException, UploadFile


@lru_cache(maxsize=4)
def _clerk_jwks_client(jwks_url: str):
    import jwt

    return jwt.PyJWKClient(jwks_url, timeout=5)


def verify_clerk_token(token: str) -> dict:
    """Verify a Clerk session JWT using the configured trusted issuer and JWKS."""
    import jwt

    jwks_url = os.getenv("CLERK_JWKS_URL", "").strip()
    issuer = os.getenv("CLERK_ISSUER", "").strip()
    if not jwks_url or not issuer:
        raise HTTPException(
            status_code=503,
            detail="Clerk authentication is not configured on the server.",
        )
    if not jwks_url.startswith("https://") or not issuer.startswith("https://"):
        raise HTTPException(
            status_code=503,
            detail="Clerk JWKS URL and issuer must use HTTPS.",
        )

    try:
        key = _clerk_jwks_client(jwks_url).get_signing_key_from_jwt(token).key
        audience = os.getenv("CLERK_JWT_AUDIENCE", "").strip()
        options = {"verify_aud": bool(audience)}
        return jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            issuer=issuer,
            audience=audience or None,
            options=options,
            leeway=5,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired authentication token.") from exc

# Allowed code, documentation, and archive extensions
ALLOWED_EXTENSIONS = {
    # Archives
    ".zip",
    # Python
    ".py", ".pyw",
    # JavaScript / TypeScript / Web
    ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".html", ".htm", ".css", ".scss", ".sass", ".less",
    # Systems / Compiled
    ".c", ".cpp", ".cc", ".cxx", ".h", ".hpp", ".cs", ".go", ".rs", ".java", ".kt", ".swift", ".scala",
    # Scripting
    ".php", ".rb", ".pl", ".lua", ".r", ".dart", ".sh", ".bash",
    # Data / Config / Docs
    ".json", ".yaml", ".yml", ".xml", ".sql", ".md", ".markdown", ".txt", ".csv", ".toml", ".ini", ".env.example",
    # Office / Documents
    ".pdf", ".docx"
}

# Dangerous / executable extensions strictly prohibited
FORBIDDEN_EXTENSIONS = {
    ".exe", ".dll", ".so", ".dylib", ".bin", ".iso", ".img",
    ".bat", ".cmd", ".vbs", ".vbe", ".js.exe", ".wsf", ".wsh",
    ".msi", ".msp", ".scr", ".pif", ".hta", ".cpl", ".msc",
    ".com", ".reg", ".ps1", ".jar"
}

# Max file size limits in bytes
MAX_ZIP_SIZE = 50 * 1024 * 1024       # 50 MB
MAX_SINGLE_FILE_SIZE = 10 * 1024 * 1024 # 10 MB


def sanitize_filename(filename: str) -> str:
    """
    Strips directory separators and potentially dangerous characters from a filename.
    """
    clean = os.path.basename(filename)
    # Remove null bytes and path traversal patterns
    clean = clean.replace("\x00", "").replace("..", "")
    clean = re.sub(r'[^a-zA-Z0-9._\-+ ]', '_', clean)
    return clean or "uploaded_file"


def validate_file_extension(filename: str, allow_zip: bool = True) -> Tuple[bool, str]:
    """
    Validates that a file's extension is within the allowed safe list.
    """
    ext = Path(filename).suffix.lower()

    if not ext:
        return False, "File has no extension. Please upload source code files with recognized extensions."

    if ext in FORBIDDEN_EXTENSIONS:
        return False, f"Uploading executable or binary files ({ext}) is strictly prohibited for security reasons."

    if not allow_zip and ext == ".zip":
        return False, "ZIP archives not permitted here. Please upload individual source files."

    if ext not in ALLOWED_EXTENSIONS:
        return False, f"Unsupported file type ({ext}). Allowed types include source code (.py, .js, .ts, .java, .cpp, etc.), documents (.md, .txt, .pdf, .docx), and .zip archives."

    return True, ""


def validate_zip_safe_extraction(zip_file_path: Path, target_directory: Path) -> bool:
    """
    Guards against Zip Slip vulnerabilities (extracting files outside target directory).
    """
    import zipfile
    target_dir_resolved = target_directory.resolve()

    with zipfile.ZipFile(str(zip_file_path), "r") as archive:
        for member in archive.infolist():
            member_path = (target_dir_resolved / member.filename).resolve()
            try:
                # If member_path is not relative to target_dir_resolved, it is a Zip Slip attempt
                member_path.relative_to(target_dir_resolved)
            except ValueError:
                return False
    return True


async def validate_uploaded_file(file: UploadFile, is_zip: bool = False) -> None:
    """
    Performs complete security validation on an uploaded file:
    - Verifies filename & extension
    - Validates file size
    - Re-winds file pointer for subsequent processing
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is missing or invalid.")

    # Validate extension
    is_valid, err_msg = validate_file_extension(file.filename, allow_zip=is_zip)
    if not is_valid:
        raise HTTPException(status_code=400, detail=err_msg)

    # Validate size
    max_size = MAX_ZIP_SIZE if is_zip else MAX_SINGLE_FILE_SIZE
    content = await file.read()
    size = len(content)
    await file.seek(0) # reset pointer

    if size == 0:
        raise HTTPException(status_code=400, detail=f"Uploaded file '{file.filename}' is empty.")

    if size > max_size:
        limit_mb = max_size // (1024 * 1024)
        raise HTTPException(
            status_code=413,
            detail=f"File '{file.filename}' exceeds the maximum allowed size of {limit_mb}MB."
        )
