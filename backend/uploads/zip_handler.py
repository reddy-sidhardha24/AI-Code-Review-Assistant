import shutil
import zipfile
from pathlib import Path

from fastapi import HTTPException, UploadFile


class ZipHandler:

    def __init__(
        self,
        upload_dir: Path,
        extract_dir: Path
    ):
        self.upload_dir = upload_dir
        self.extract_dir = extract_dir

    async def extract_project(
        self,
        file: UploadFile
    ):

        if not file.filename:
            raise HTTPException(
                status_code=400,
                detail="Invalid file."
            )

        if not file.filename.lower().endswith(".zip"):
            raise HTTPException(
                status_code=400,
                detail="Please upload a ZIP file."
            )

        safe_filename = Path(file.filename).name

        zip_path = self.upload_dir / safe_filename

        with open(zip_path, "wb") as buffer:
            shutil.copyfileobj(
                file.file,
                buffer
            )

        if not zipfile.is_zipfile(zip_path):

            zip_path.unlink(
                missing_ok=True
            )

            raise HTTPException(
                status_code=400,
                detail="Uploaded file is not a valid ZIP archive."
            )

        project_name = Path(
            safe_filename
        ).stem

        project_folder = (
            self.extract_dir /
            project_name
        )

        if project_folder.exists():
            shutil.rmtree(project_folder)

        project_folder.mkdir(
            parents=True,
            exist_ok=True
        )

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
                        detail="Unsafe file path detected inside ZIP archive."
                    )

            zip_ref.extractall(
                project_folder
            )

        return {
            "project_name": project_name,
            "project_folder": project_folder,
            "zip_path": zip_path
        }