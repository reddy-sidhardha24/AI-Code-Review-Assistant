from typing import List

from fastapi import UploadFile

from .zip_handler import ZipHandler
from .file_handler import FileHandler
from .paste_handler import PasteHandler


class UploadService:

    def __init__(
        self,
        upload_dir,
        extract_dir,
        rag_pipeline
    ):
        # ZIP Handler
        self.zip_handler = ZipHandler(
            upload_dir,
            extract_dir
        )

        # Multiple Files Handler
        self.file_handler = FileHandler(
            upload_dir
        )

        # Paste Code Handler
        self.paste_handler = PasteHandler(
            upload_dir
        )

        # Shared RAG Pipeline
        self.rag_pipeline = rag_pipeline

    # ============================================================
    # ZIP Upload
    # ============================================================

    async def process_zip_upload(
        self,
        file: UploadFile
    ):

        upload_result = await self.zip_handler.extract_project(
            file
        )

        metadata = self.rag_pipeline.build_vector_database(
            str(upload_result["project_folder"])
        )

        return {
            "success": True,
            "message": "Project uploaded and indexed successfully.",
            "project_name": upload_result["project_name"],
            "metadata": metadata
        }

    # ============================================================
    # Multiple Source Files Upload
    # ============================================================

    async def process_multiple_files(
        self,
        files: List[UploadFile]
    ):

        upload_result = await self.file_handler.save_files(
            files
        )

        metadata = self.rag_pipeline.build_vector_database(
            str(upload_result["project_folder"])
        )

        return {
            "success": True,
            "message": "Source files uploaded and indexed successfully.",
            "project_name": "temp_project",
            "files": upload_result["saved_files"],
            "metadata": metadata
        }

    # ============================================================
    # Paste Code Upload
    # ============================================================

    def process_paste_code(
        self,
        code: str,
        filename: str
    ):

        upload_result = self.paste_handler.save_code(
            code,
            filename
        )

        metadata = self.rag_pipeline.build_vector_database(
            str(upload_result["project_folder"])
        )

        return {
            "success": True,
            "message": "Code uploaded and indexed successfully.",
            "project_name": "pasted_code",
            "file": upload_result["file_name"],
            "metadata": metadata
        }