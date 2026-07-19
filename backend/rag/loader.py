#Read project files from disk # backend/rag/loader.py

from pathlib import Path
from typing import List, Dict

# Directories to ignore
IGNORE_DIRS = {
    "venv",
    "__pycache__",
    "node_modules",
    ".git",
    ".idea",
    ".vscode",
    "dist",
    "build",
    ".next",
    ".pytest_cache",
}

# File extensions to load
SUPPORTED_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".java",
    ".cpp",
    ".c",
    ".cs",
    ".go",
    ".php",
    ".rb",
    ".swift",
    ".kt",
    ".html",
    ".css",
    ".json",
    ".xml",
    ".yml",
    ".yaml",
    ".md",
}


class ProjectLoader:
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)

    def load(self) -> List[Dict]:
        """
        Returns a list of dictionaries.

        Example:
        [
            {
                "path": ".../app.py",
                "name": "app.py",
                "extension": ".py",
                "content": "...code..."
            }
        ]
        """

        documents = []

        for file in self.project_path.rglob("*"):

            # Skip directories
            if file.is_dir():
                continue

            # Skip ignored folders
            if any(part in IGNORE_DIRS for part in file.parts):
                continue

            # Skip unsupported files
            if file.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue

            try:
                content = file.read_text(
                    encoding="utf-8",
                    errors="ignore"
                )

                documents.append(
                    {
                        "path": str(file),
                        "name": file.name,
                        "extension": file.suffix,
                        "content": content,
                    }
                )

            except Exception as e:
                print(f"Skipped {file}: {e}")

        return documents


if __name__ == "__main__":

    loader = ProjectLoader("../")

    docs = loader.load()

    print(f"\nLoaded {len(docs)} files\n")

    for doc in docs[:5]:
        print("=" * 70)
        print("File :", doc["name"])
        print("Path :", doc["path"])
        print("Type :", doc["extension"])
        print("Characters :", len(doc["content"]))