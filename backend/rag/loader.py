from pathlib import Path
from typing import List, Dict


# ============================================================
# Directories to ignore
# ============================================================

IGNORE_DIRS = {
    "venv",
    ".venv",
    "__pycache__",
    "node_modules",
    ".git",
    ".idea",
    ".vscode",
    "dist",
    "build",
    ".next",
    ".pytest_cache",
    "coverage",
}


# ============================================================
# Supported source-code/document extensions
# ============================================================

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


# ============================================================
# Extension -> Programming Language
# ============================================================

LANGUAGE_MAP = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".java": "Java",
    ".cpp": "C++",
    ".c": "C",
    ".cs": "C#",
    ".go": "Go",
    ".php": "PHP",
    ".rb": "Ruby",
    ".swift": "Swift",
    ".kt": "Kotlin",
    ".html": "HTML",
    ".css": "CSS",
    ".json": "JSON",
    ".xml": "XML",
    ".yml": "YAML",
    ".yaml": "YAML",
    ".md": "Markdown",
}


class ProjectLoader:

    def __init__(self, project_path: str):

        self.project_path = Path(project_path)

        # Project-wide metadata
        self.metadata = {
            "project_name": self.project_path.name,
            "total_files": 0,
            "total_lines": 0,
            "languages": {},
            "files": [],
        }


    # ========================================================
    # Load project files
    # ========================================================

    def load(self) -> List[Dict]:

        documents = []

        # Reset metadata every time load() is called
        self.metadata = {
            "project_name": self.project_path.name,
            "total_files": 0,
            "total_lines": 0,
            "languages": {},
            "files": [],
        }

        # Validate project directory
        if not self.project_path.exists():

            raise FileNotFoundError(
                f"Project path does not exist: {self.project_path}"
            )

        if not self.project_path.is_dir():

            raise ValueError(
                f"Project path is not a directory: {self.project_path}"
            )


        # ----------------------------------------------------
        # Scan project
        # ----------------------------------------------------

        for file in self.project_path.rglob("*"):

            # Skip directories
            if file.is_dir():
                continue


            # Skip ignored directories
            try:

                relative_path = file.relative_to(self.project_path)

            except ValueError:

                relative_path = file


            if any(
                part in IGNORE_DIRS
                for part in relative_path.parts
            ):
                continue


            # Get extension
            extension = file.suffix.lower()


            # Skip unsupported files
            if extension not in SUPPORTED_EXTENSIONS:
                continue


            try:

                # --------------------------------------------
                # Read file
                # --------------------------------------------

                content = file.read_text(
                    encoding="utf-8",
                    errors="ignore"
                )


                # --------------------------------------------
                # Count lines
                # --------------------------------------------

                line_count = len(content.splitlines())


                # --------------------------------------------
                # Detect language
                # --------------------------------------------

                language = LANGUAGE_MAP.get(
                    extension,
                    "Unknown"
                )


                # --------------------------------------------
                # Create document
                # --------------------------------------------

                document = {
                    "path": str(file),
                    "relative_path": str(relative_path),
                    "name": file.name,
                    "extension": extension,
                    "language": language,
                    "line_count": line_count,
                    "content": content,
                }


                documents.append(document)


                # --------------------------------------------
                # Update project metadata
                # --------------------------------------------

                self.metadata["total_files"] += 1

                self.metadata["total_lines"] += line_count


                # Count files per language
                if language not in self.metadata["languages"]:

                    self.metadata["languages"][language] = {
                        "files": 0,
                        "lines": 0,
                    }


                self.metadata["languages"][language]["files"] += 1

                self.metadata["languages"][language]["lines"] += line_count


                # Store file information
                self.metadata["files"].append(
                    {
                        "name": file.name,
                        "path": str(relative_path),
                        "extension": extension,
                        "language": language,
                        "lines": line_count,
                    }
                )


            except Exception as e:

                print(
                    f"Skipped {file}: {e}"
                )


        return documents


    # ========================================================
    # Return project metadata
    # ========================================================

    def get_metadata(self) -> Dict:

        return self.metadata


    # ========================================================
    # Print project summary
    # ========================================================

    def print_summary(self):

        metadata = self.get_metadata()

        print("\n" + "=" * 70)

        print("PROJECT SUMMARY")

        print("=" * 70)

        print(
            f"Project Name : "
            f"{metadata['project_name']}"
        )

        print(
            f"Total Files  : "
            f"{metadata['total_files']}"
        )

        print(
            f"Total Lines  : "
            f"{metadata['total_lines']}"
        )


        print("\nLanguages:")

        if not metadata["languages"]:

            print("No supported source files found.")

        else:

            for language, info in metadata["languages"].items():

                print(
                    f"  {language}: "
                    f"{info['files']} file(s), "
                    f"{info['lines']} lines"
                )


        print("\nFiles:")

        for file in metadata["files"]:

            print(
                f"  {file['path']} "
                f"| {file['language']} "
                f"| {file['lines']} lines"
            )

        print("=" * 70)


# ============================================================
# Test Loader
# ============================================================

if __name__ == "__main__":

    loader = ProjectLoader("../")

    documents = loader.load()

    loader.print_summary()


    print("\nFIRST 5 LOADED FILES\n")

    for document in documents[:5]:

        print("=" * 70)

        print(
            "File       :",
            document["name"]
        )

        print(
            "Path       :",
            document["relative_path"]
        )

        print(
            "Extension  :",
            document["extension"]
        )

        print(
            "Language   :",
            document["language"]
        )

        print(
            "Lines      :",
            document["line_count"]
        )

        print(
            "Characters :",
            len(document["content"])
        )