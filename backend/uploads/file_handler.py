from pathlib import Path
from typing import List

from fastapi import UploadFile, HTTPException


class FileHandler:

    SUPPORTED_EXTENSIONS = {
        ".py",
        ".java",
        ".cpp",
        ".c",
        ".h",
        ".hpp",
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
        ".cs",
        ".go",
        ".php",
        ".rb",
        ".swift",
        ".kt",
        ".rs"
    }

    def __init__(
        self,
        upload_dir: Path
    ):
        self.upload_dir = upload_dir

    async def save_files(
        self,
        files: List[UploadFile]
    ):

        project_folder = self.upload_dir / "temp_project"

        if project_folder.exists():

            for item in project_folder.iterdir():

                if item.is_file():
                    item.unlink()

        else:

            project_folder.mkdir(
                parents=True,
                exist_ok=True
            )

        saved_files = []

        for file in files:

            if not file.filename:

                continue

            extension = Path(
                file.filename
            ).suffix.lower()

            if extension not in self.SUPPORTED_EXTENSIONS:

                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported file type: {extension}"
                )

            file_path = (
                project_folder /
                Path(file.filename).name
            )

            content = await file.read()

            with open(
                file_path,
                "wb"
            ) as f:

                f.write(content)

            saved_files.append(
                file_path.name
            )

        return {

            "project_folder": project_folder,

            "saved_files": saved_files

        }