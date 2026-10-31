# ============================================================
# services/upload_service.py
# ============================================================

import os
import shutil
import zipfile
import uuid
from pathlib import Path
from typing import List

from fastapi import UploadFile


class UploadService:
    """
    Handles:
    1. ZIP project uploads
    2. Multiple source-file uploads
    3. Pasted source code

    After storing the source files, the shared RAG pipeline
    indexes the project.
    """

    def __init__(
        self,
        upload_dir,
        extract_dir,
        rag_pipeline
    ):

        self.upload_dir = Path(
            upload_dir
        )

        self.extract_dir = Path(
            extract_dir
        )

        self.rag_pipeline = (
            rag_pipeline
        )

        self.upload_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        self.extract_dir.mkdir(
            parents=True,
            exist_ok=True
        )

    # ========================================================
    # SUPPORTED SOURCE FILES
    # ========================================================

    SUPPORTED_EXTENSIONS = {
        ".py",
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
        ".java",
        ".c",
        ".h",
        ".cpp",
        ".cc",
        ".cxx",
        ".cs",
        ".go",
        ".rs",
        ".php",
        ".rb",
        ".swift",
        ".kt",
        ".kts",
        ".dart",
        ".scala",
        ".sh",
        ".bash",
        ".sql",
        ".html",
        ".htm",
        ".css",
        ".scss",
        ".sass",
        ".vue",
        ".xml",
        ".json",
        ".yaml",
        ".yml",
        ".md"
    }

    MAX_ARCHIVE_ENTRIES = 5000
    MAX_ARCHIVE_FILE_SIZE = 10 * 1024 * 1024
    MAX_ARCHIVE_TOTAL_SIZE = 500 * 1024 * 1024

    # ========================================================
    # HELPER: SAFE ZIP PATH
    # ========================================================

    def _safe_extract_path(
        self,
        base_directory: Path,
        member_name: str
    ) -> Path:

        """
        Prevent ZIP path traversal such as:

            ../../malicious.py
        """

        base_directory = (
            base_directory
            .resolve()
        )

        target = (
            base_directory
            / member_name
        ).resolve()

        try:

            target.relative_to(
                base_directory
            )

        except ValueError:

            raise ValueError(
                "Unsafe ZIP entry detected: "
                f"{member_name}"
            )

        return target

    # ========================================================
    # HELPER: CHECK SOURCE FILES
    # ========================================================

    def _find_source_files(
        self,
        project_directory: Path
    ):

        source_files = []

        for path in project_directory.rglob("*"):

            if not path.is_file():

                continue

            if path.suffix.lower() in (
                self.SUPPORTED_EXTENSIONS
            ):

                source_files.append(
                    path
                )

        return source_files

    # ========================================================
    # ZIP PROJECT UPLOAD
    # ========================================================

    async def process_zip_upload(
        self,
        file: UploadFile
    ):

        if not file.filename:

            raise ValueError(
                "Uploaded ZIP filename is missing."
            )

        original_name = (
            Path(
                file.filename
            ).name
        )

        if not original_name.lower().endswith(
            ".zip"
        ):

            raise ValueError(
                "Only ZIP project files are supported."
            )

        project_name = Path(
            original_name
        ).stem

        upload_id = uuid.uuid4().hex
        zip_path = self.upload_dir / f"{upload_id}.zip"

        # Use a per-upload folder so two users uploading archives with the
        # same filename cannot delete or overwrite one another's extracted data.
        project_folder = self.extract_dir / f"{project_name}_{upload_id}"

        project_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        # ----------------------------------------------------
        # Save ZIP
        # ----------------------------------------------------

        with open(
            zip_path,
            "wb"
        ) as output_file:

            while True:

                chunk = await file.read(
                    1024 * 1024
                )

                if not chunk:

                    break

                output_file.write(
                    chunk
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

            raise ValueError(
                "Uploaded file is not a valid ZIP archive."
            )

        # ----------------------------------------------------
        # Extract safely
        # ----------------------------------------------------

        with zipfile.ZipFile(
            zip_path,
            "r"
        ) as archive:

            members = archive.infolist()
            if len(members) > self.MAX_ARCHIVE_ENTRIES:
                zip_path.unlink(missing_ok=True)
                raise ValueError(
                    f"ZIP contains too many entries (maximum {self.MAX_ARCHIVE_ENTRIES})."
                )

            declared_total_size = 0
            for member in members:
                if member.is_dir():
                    continue
                if member.file_size > self.MAX_ARCHIVE_FILE_SIZE:
                    zip_path.unlink(missing_ok=True)
                    raise ValueError(
                        f"ZIP entry exceeds the {self.MAX_ARCHIVE_FILE_SIZE // (1024 * 1024)} MB per-file limit."
                    )
                declared_total_size += member.file_size
            if declared_total_size > self.MAX_ARCHIVE_TOTAL_SIZE:
                zip_path.unlink(missing_ok=True)
                raise ValueError("ZIP expands beyond the 500 MB project limit.")

            extracted_total_size = 0
            for member in members:

                # Ignore directories
                if member.is_dir():

                    continue

                target_path = (
                    self._safe_extract_path(
                        project_folder,
                        member.filename
                    )
                )

                target_path.parent.mkdir(
                    parents=True,
                    exist_ok=True
                )

                with archive.open(
                    member,
                    "r"
                ) as source:

                    with open(
                        target_path,
                        "wb"
                    ) as target:
                        while True:
                            chunk = source.read(1024 * 1024)
                            if not chunk:
                                break
                            extracted_total_size += len(chunk)
                            if extracted_total_size > self.MAX_ARCHIVE_TOTAL_SIZE:
                                raise ValueError("ZIP expands beyond the 500 MB project limit.")
                            target.write(chunk)

        # ----------------------------------------------------
        # Remove uploaded ZIP after extraction
        # ----------------------------------------------------

        zip_path.unlink(
            missing_ok=True
        )

        # ----------------------------------------------------
        # Find source files
        # ----------------------------------------------------

        source_files = (
            self._find_source_files(
                project_folder
            )
        )

        if not source_files:

            raise ValueError(
                "No supported source-code files "
                "were found inside the uploaded project."
            )

        print(
            f"Found {len(source_files)} "
            "supported source files."
        )

        # ----------------------------------------------------
        # Build RAG database
        # ----------------------------------------------------

        metadata = (
            self.rag_pipeline
            .build_vector_database(
                str(
                    project_folder
                )
            )
        )

        return {
            "success": True,

            "message": (
                "Project uploaded and "
                "indexed successfully."
            ),

            "project_name": (
                project_name
            ),

            "project_folder": (
                project_folder
            ),

            "files": [
                str(
                    path.relative_to(
                        project_folder
                    )
                )

                for path in source_files
            ],

            "metadata": metadata
        }

    # ========================================================
    # MULTIPLE SOURCE FILES
    # ========================================================

    async def process_multiple_files(
        self,
        files: List[UploadFile]
    ):

        if not files:

            raise ValueError(
                "No files were provided."
            )

        project_name = "uploaded_files"
        project_folder = self.upload_dir / f"{project_name}_{uuid.uuid4().hex}"

        project_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        saved_files = []

        for file in files:

            if not file.filename:

                continue

            filename = Path(
                file.filename
            ).name

            extension = (
                Path(
                    filename
                ).suffix.lower()
            )

            if extension not in (
                self.SUPPORTED_EXTENSIONS
            ):

                continue

            target_path = (
                project_folder
                / filename
            )

            with open(
                target_path,
                "wb"
            ) as output_file:

                while True:

                    chunk = await file.read(
                        1024 * 1024
                    )

                    if not chunk:

                        break

                    output_file.write(
                        chunk
                    )

            saved_files.append(
                filename
            )

        if not saved_files:

            raise ValueError(
                "No supported source-code files "
                "were uploaded."
            )

        # ----------------------------------------------------
        # RAG indexing
        # ----------------------------------------------------

        metadata = (
            self.rag_pipeline
            .build_vector_database(
                str(
                    project_folder
                )
            )
        )

        return {
            "success": True,

            "message": (
                "Source files uploaded and "
                "indexed successfully."
            ),

            "project_name": project_name,

            "project_folder": (
                project_folder
            ),

            "saved_files": (
                saved_files
            ),

            "metadata": metadata
        }

    # ========================================================
    # PASTE CODE
    # ========================================================

    def process_paste_code(
        self,
        code: str,
        filename: str
    ):
        """
        Store pasted source code as a new standalone project.

        Every paste operation gets its own directory so concurrent or
        different users' submissions cannot overwrite each other.
        """

        # ========================================================
        # VALIDATE INPUT
        # ========================================================

        if not filename:
            raise ValueError(
                "Filename cannot be empty."
            )

        if not code or not code.strip():
            raise ValueError(
                "Code cannot be empty."
            )

        # ========================================================
        # PASTED CODE PROJECT DIRECTORY
        # ========================================================

        project_folder = self.upload_dir / f"pasted_code_{uuid.uuid4().hex}"

        # ========================================================
        # CREATE FRESH PROJECT DIRECTORY
        # ========================================================

        project_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        # ========================================================
        # CREATE NEW SOURCE FILE
        # ========================================================

        safe_filename = Path(
            filename
        ).name

        file_path = (
            project_folder / safe_filename
        )

        with open(
            file_path,
            "w",
            encoding="utf-8"
        ) as file:

            file.write(
                code
            )

        print(
            "\nProcessing pasted code:",
            safe_filename
        )

        print(
            "Created:",
            file_path
        )

        # ========================================================
        # BUILD NEW RAG INDEX
        # ========================================================

        print(
            "\nBuilding fresh RAG index for pasted code..."
        )

        result = (
            self.rag_pipeline
            .build_vector_database(
                str(project_folder)
            )
        )

        # ========================================================
        # RETURN RESULT
        # ========================================================

        return {
            "success": True,
            "message": (
                "Pasted code processed successfully."
            ),
            "filename": safe_filename,
            "project_path": str(
                project_folder
            ),
            "rag": result
        }
