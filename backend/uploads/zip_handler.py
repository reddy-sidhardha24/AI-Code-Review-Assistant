import shutil
import zipfile
from pathlib import Path

from fastapi import HTTPException, UploadFile


class ZipHandler:

    # Maximum ZIP file size: 50 MB
    MAX_ZIP_SIZE = 50 * 1024 * 1024

    # Maximum number of files inside the ZIP
    MAX_FILE_COUNT = 500

    # Maximum total extracted size: 200 MB
    MAX_EXTRACTED_SIZE = 200 * 1024 * 1024

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

        # ========================================================
        # Save uploaded file with size check
        # ========================================================

        total_bytes = 0

        with open(zip_path, "wb") as buffer:

            while True:

                chunk = await file.read(
                    1024 * 1024
                )

                if not chunk:
                    break

                total_bytes += len(chunk)

                if total_bytes > self.MAX_ZIP_SIZE:

                    buffer.close()

                    zip_path.unlink(
                        missing_ok=True
                    )

                    raise HTTPException(
                        status_code=400,
                        detail=(
                            "ZIP file is too large. "
                            "Maximum size is 50 MB."
                        )
                    )

                buffer.write(chunk)

        # ========================================================
        # Validate ZIP
        # ========================================================

        if not zipfile.is_zipfile(zip_path):

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

        # ========================================================
        # Check for ZIP bombs
        # ========================================================

        try:

            with zipfile.ZipFile(
                zip_path, "r"
            ) as zip_ref:

                members = zip_ref.infolist()

                if len(members) > self.MAX_FILE_COUNT:

                    zip_path.unlink(
                        missing_ok=True
                    )

                    raise HTTPException(
                        status_code=400,
                        detail=(
                            f"ZIP contains too many files "
                            f"({len(members)}). "
                            f"Maximum is {self.MAX_FILE_COUNT}."
                        )
                    )

                total_uncompressed = sum(
                    m.file_size for m in members
                )

                if total_uncompressed > self.MAX_EXTRACTED_SIZE:

                    zip_path.unlink(
                        missing_ok=True
                    )

                    raise HTTPException(
                        status_code=400,
                        detail=(
                            "ZIP contents are too large "
                            "when extracted. "
                            "Maximum extracted size is 200 MB."
                        )
                    )

        except zipfile.BadZipFile:

            zip_path.unlink(
                missing_ok=True
            )

            raise HTTPException(
                status_code=400,
                detail=(
                    "Uploaded file is corrupted "
                    "or not a valid ZIP archive."
                )
            )

        # ========================================================
        # Extract
        # ========================================================

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

                # Skip directories
                if member.is_dir():
                    continue

                target_path = (
                    project_folder /
                    member.filename
                ).resolve()

                # Path traversal protection
                try:

                    target_path.relative_to(
                        extraction_root
                    )

                except ValueError:

                    # Clean up and reject
                    shutil.rmtree(
                        project_folder,
                        ignore_errors=True
                    )

                    zip_path.unlink(
                        missing_ok=True
                    )

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

        # ========================================================
        # Clean up ZIP file
        # ========================================================

        zip_path.unlink(missing_ok=True)

        print(
            f"\nZIP extracted: {project_name}"
        )

        print(
            f"Extracted to: {project_folder}"
        )

        return {
            "project_name": project_name,
            "project_folder": project_folder
        }