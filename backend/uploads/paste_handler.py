from pathlib import Path


class PasteHandler:

    def __init__(
        self,
        upload_dir: Path
    ):
        self.upload_dir = upload_dir

    def save_code(
        self,
        code: str,
        filename: str
    ):

        project_folder = self.upload_dir / "pasted_code"

        project_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        file_path = project_folder / filename

        with open(
            file_path,
            "w",
            encoding="utf-8"
        ) as f:
            f.write(code)

        return {
            "project_folder": project_folder,
            "file_name": filename
        }