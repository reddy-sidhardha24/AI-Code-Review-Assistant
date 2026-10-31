from pathlib import Path
from typing import List

from fastapi import UploadFile, HTTPException


class FileHandler:

    # ============================================================
    # Supported extensions — matches the RAG loader
    # ============================================================

    SUPPORTED_EXTENSIONS = {
        # Python
        ".py",

        # JavaScript / TypeScript
        ".js", ".jsx", ".ts", ".tsx",

        # Java
        ".java",

        # C / C++
        ".c", ".h", ".cpp", ".cc", ".cxx", ".hpp",

        # C#
        ".cs",

        # Go
        ".go",

        # Rust
        ".rs",

        # PHP
        ".php",

        # Ruby
        ".rb",

        # Swift
        ".swift",

        # Kotlin
        ".kt", ".kts",

        # Dart
        ".dart",

        # Scala
        ".scala",

        # Shell
        ".sh", ".bash",

        # SQL
        ".sql",

        # Web
        ".html", ".htm", ".css", ".scss", ".sass",

        # Vue
        ".vue",

        # Data / Config
        ".json", ".xml", ".yml", ".yaml",

        # Markdown
        ".md",
    }

    # Keep in sync with the API-level source-file limit.
    MAX_FILE_SIZE = 10 * 1024 * 1024

    # Maximum number of files
    MAX_FILE_COUNT = 50

    def __init__(
        self,
        upload_dir: Path
    ):
        self.upload_dir = upload_dir

    async def save_files(
        self,
        files: List[UploadFile]
    ):

        # ========================================================
        # Validate file count
        # ========================================================

        if len(files) > self.MAX_FILE_COUNT:

            raise HTTPException(
                status_code=400,
                detail=(
                    f"Too many files selected "
                    f"({len(files)}). "
                    f"Maximum is {self.MAX_FILE_COUNT}."
                )
            )

        # ========================================================
        # Use a unique project folder so uploads never erase prior submissions.
        # ========================================================

        import uuid
        project_folder = self.upload_dir / f"temp_project_{uuid.uuid4().hex}"

        project_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        # ========================================================
        # Save each file
        # ========================================================

        saved_files = []
        skipped_files = []
        seen_names = set()

        for file in files:

            if not file.filename:
                skipped_files.append(
                    "unnamed file"
                )
                continue

            # --------------------------------------------------
            # Extension check
            # --------------------------------------------------

            extension = Path(
                file.filename
            ).suffix.lower()

            if extension not in self.SUPPORTED_EXTENSIONS:

                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Unsupported file type: "
                        f"{file.filename} "
                        f"({extension})"
                    )
                )

            # --------------------------------------------------
            # Read content
            # --------------------------------------------------

            content = await file.read()

            # --------------------------------------------------
            # Size check
            # --------------------------------------------------

            if len(content) > self.MAX_FILE_SIZE:

                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"File too large: "
                        f"{file.filename} "
                        f"({len(content) / 1024 / 1024:.1f} MB). "
                        f"Maximum is 10 MB per file."
                    )
                )

            # --------------------------------------------------
            # Save
            # --------------------------------------------------

            safe_name = Path(
                file.filename
            ).name

            if safe_name.casefold() in seen_names:
                raise HTTPException(
                    status_code=400,
                    detail=f"Duplicate filename in this upload: {safe_name}",
                )
            seen_names.add(safe_name.casefold())

            file_path = (
                project_folder / safe_name
            )

            with open(
                file_path, "wb"
            ) as f:
                f.write(content)

            saved_files.append(safe_name)

        # ========================================================
        # Validate at least one file saved
        # ========================================================

        if not saved_files:

            raise HTTPException(
                status_code=400,
                detail=(
                    "No valid source files were "
                    "found in the upload."
                )
            )

        # ========================================================
        # Log
        # ========================================================

        print(
            f"\nSaved {len(saved_files)} "
            f"source files to {project_folder}"
        )

        if skipped_files:

            print(
                f"Skipped {len(skipped_files)} "
                f"files: {skipped_files}"
            )

        return {
            "project_folder": project_folder,
            "saved_files": saved_files,
            "skipped_count": len(skipped_files)
        }
