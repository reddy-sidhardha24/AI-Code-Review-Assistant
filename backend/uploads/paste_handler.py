from pathlib import Path
import uuid


class PasteHandler:

    def __init__(
        self,
        upload_dir: Path
    ):
        self.upload_dir = upload_dir

    # ========================================================
    # SAVE PASTED CODE
    # ========================================================

    def save_code(
        self,
        code: str,
        filename: str
    ):
        """
        Save pasted source code as a NEW standalone project.

        Every paste operation receives a separate project folder.
        """

        # ====================================================
        # VALIDATE INPUT
        # ====================================================

        if not filename or not filename.strip():
            raise ValueError(
                "Filename cannot be empty."
            )

        if not code or not code.strip():
            raise ValueError(
                "Code cannot be empty."
            )

        # ====================================================
        # PASTED CODE DIRECTORY
        # ====================================================

        project_folder = self.upload_dir / f"pasted_code_{uuid.uuid4().hex}"

        # ====================================================
        # CREATE FRESH DIRECTORY
        # ====================================================

        project_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        # ====================================================
        # SANITIZE FILE NAME
        # ====================================================

        safe_filename = Path(
            filename.strip()
        ).name

        if not safe_filename:
            raise ValueError(
                "Invalid filename."
            )

        # ====================================================
        # CREATE FILE
        # ====================================================

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

        # ====================================================
        # LOG
        # ====================================================

        print(
            "\nProcessing pasted code:",
            safe_filename
        )

        print(
            "Created:",
            file_path
        )

        print(
            "Fresh paste project created."
        )

        # ====================================================
        # RETURN
        # ====================================================

        return {
            "project_folder": project_folder,
            "file_name": safe_filename
        }
