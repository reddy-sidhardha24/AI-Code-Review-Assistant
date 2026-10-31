# ============================================================
# AI CODE REVIEW ASSISTANT
# backend/services/code_correction_service.py
# Full Corrected Project and Corrected Files ZIP Generator
# ============================================================

import os
import io
import shutil
import zipfile
import tempfile
from pathlib import Path
from pathlib import PurePosixPath
from typing import Dict, Any, Optional


class CodeCorrectionService:
    """
    Applies AI-generated code corrections to project directories and builds:
    1. Complete corrected project ZIP
    2. Corrected files only ZIP
    """

    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent.parent

    def build_full_project_zip(
        self,
        source_dir: str,
        review_data: Dict[str, Any]
    ) -> bytes:
        """
        Creates a temporary copy of the source project, overwrites all files
        that had error fixes applied, and zips the entire project directory.
        """
        src_path = Path(source_dir).resolve()
        allowed_roots = [
            (self.base_dir / "extracted").resolve(),
            (self.base_dir / "data" / "users").resolve(),
        ]
        if not any(self._is_within(src_path, root) for root in allowed_roots):
            raise ValueError("Source directory must be inside application project storage.")

        if not src_path.is_dir() or src_path.is_symlink():
            raise ValueError("Source directory must be an existing project directory.")

        allowed_root = next(root for root in allowed_roots if self._is_within(src_path, root))
        try:
            src_path.relative_to(allowed_root)
        except ValueError as exc:  # defensive; _is_within already checked this
            raise ValueError("Source directory must be inside the extracted project area.") from exc
        zip_buffer = io.BytesIO()

        # Safeguard: Never package the entire root extraction directory
        is_project_collection = (
            src_path == allowed_root
            or (src_path.parent.name == "users" and src_path.parent.parent == allowed_root)
        )
        if is_project_collection:
            project_name = (
                (review_data.get("project") or {}).get("name")
                or review_data.get("project_name")
                or ""
            ).strip()

            target_sub = None
            if project_name:
                p_exact = (src_path / project_name).resolve()
                try:
                    p_exact.relative_to(src_path.resolve())
                    is_safe_child = p_exact != src_path.resolve()
                except ValueError:
                    is_safe_child = False
                if is_safe_child and p_exact.is_dir():
                    target_sub = p_exact
                else:
                    clean_name = Path(project_name).stem.lower()
                    for item in src_path.iterdir():
                        if not item.is_symlink() and item.is_dir() and (
                            item.name.lower() == clean_name
                            or item.name.lower() == project_name.lower()
                            or item.name.lower().startswith(clean_name + "_")
                        ):
                            target_sub = item
                            break

            if not target_sub:
                files_analyzed = review_data.get("files_analyzed") or []
                for item in files_analyzed:
                    fname = item if isinstance(item, str) else (item.get("file_name") or item.get("path") or "")
                    if fname:
                        base_fname = Path(fname).name
                        for d in src_path.iterdir():
                            if d.is_dir() and ((d / fname).exists() or any(d.rglob(base_fname))):
                                target_sub = d
                                break
                    if target_sub:
                        break

            if target_sub:
                src_path = target_sub

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_project = Path(tmp_dir) / (src_path.name or "project")

            if src_path.exists() and src_path.is_dir() and src_path.name.lower() not in ("extracted", "uploads"):
                # Copy entire project ignoring git and virtualenvs
                shutil.copytree(
                    src_path,
                    tmp_project,
                    ignore=lambda directory, names: [
                        name for name in names
                        if name in {".git", "__pycache__", "node_modules", "venv", ".venv"}
                        or (Path(directory) / name).is_symlink()
                    ]
                )
            else:
                tmp_project.mkdir(parents=True, exist_ok=True)
                # Copy only files that belong to this review
                files_analyzed = review_data.get("files_analyzed") or []
                for item in files_analyzed:
                    fname = item if isinstance(item, str) else (item.get("file_name") or item.get("path") or "")
                    if fname:
                        candidate = src_path / fname
                        if candidate.exists() and candidate.is_file():
                            dest = tmp_project / Path(fname).name
                            dest.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(candidate, dest)

            # Apply corrections to the copied project
            self._apply_corrections_to_dir(tmp_project, review_data)

            # Zip the entire corrected project directory
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(tmp_project):
                    for file in files:
                        full_fpath = Path(root) / file
                        arcname = full_fpath.relative_to(tmp_project)
                        zipf.write(full_fpath, arcname=str(arcname))

        return zip_buffer.getvalue()

    @staticmethod
    def _is_within(path: Path, root: Path) -> bool:
        try:
            path.relative_to(root)
            return True
        except ValueError:
            return False

    def build_corrected_only_zip(
        self,
        review_data: Dict[str, Any]
    ) -> bytes:
        """
        Builds a ZIP archive containing ONLY the files and snippets that were
        modified/corrected by the AI reviewer.
        """
        zip_buffer = io.BytesIO()
        corrected_files = self._extract_corrected_file_map(review_data)

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
            if corrected_files:
                for rel_path, content in corrected_files.items():
                    zipf.writestr(rel_path, content.encode("utf-8"))
            else:
                zipf.writestr("README.txt", "No code corrections were required for this project.")

        return zip_buffer.getvalue()

    def _extract_corrected_file_map(self, review_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Extracts a dictionary of { relative_path: corrected_code_content }.
        """
        file_map: Dict[str, str] = {}

        # 1. Check explicit corrected_code list
        for item in review_data.get("corrected_code") or []:
            if isinstance(item, dict):
                fname = item.get("file_name") or item.get("path") or "corrected_file.py"
                code = item.get("code") or ""
                safe_name = self._safe_relative_path(fname)
                if safe_name and code.strip():
                    file_map[safe_name] = code

        # 2. Check detected findings with after_code or corrected_code
        for key in ["bugs", "errors", "detected_issues"]:
            for finding in review_data.get(key) or []:
                if isinstance(finding, dict):
                    fpath = finding.get("file") or "fixed_code.py"
                    after = finding.get("after_code") or finding.get("corrected_code")
                    safe_name = self._safe_relative_path(fpath)
                    if after and after.strip() and safe_name and safe_name not in file_map:
                        file_map[safe_name] = after.strip()

        return file_map

    @staticmethod
    def _safe_relative_path(value: Any) -> Optional[str]:
        """Normalize a project-relative path and reject traversal/absolute paths."""
        raw = str(value or "").replace("\\", "/")
        path = PurePosixPath(raw)
        if not raw or path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
            return None
        if path.parts and ":" in path.parts[0]:
            return None
        return path.as_posix()

    def _apply_corrections_to_dir(self, target_dir: Path, review_data: Dict[str, Any]):
        """Replace original project files with complete corrected file contents."""
        root = target_dir.resolve()

        # Explicit model-generated complete files replace their originals.
        # Backend-synthesized "Refactored Code with Applied Fixes" entries are
        # only collections of snippets, so never treat them as whole files.
        full_file_map = self.extract_full_file_correction_map(review_data)

        for rel_path, code in full_file_map.items():
            dest_file = self._resolve_project_file(root, rel_path)
            self._write_project_file(root, dest_file, code)

    def extract_full_file_correction_map(self, review_data: Dict[str, Any]) -> Dict[str, str]:
        """Return only complete corrected files, excluding synthetic/snippet entries."""
        full_file_map: Dict[str, str] = {}
        generated_files_are_complete = bool(review_data.get("_complete_file_corrections"))
        for item in review_data.get("corrected_code") or []:
            if not isinstance(item, dict):
                continue
            rel_path = self._safe_relative_path(item.get("file_name") or item.get("path"))
            code = item.get("code")
            if not rel_path or not isinstance(code, str) or not code.strip():
                continue
            if "Refactored Code with Applied Fixes:" in code[:500]:
                continue
            if not generated_files_are_complete and self._is_finding_snippet(review_data, rel_path, code):
                continue
            full_file_map[rel_path] = code
        return full_file_map

    @staticmethod
    def _iter_findings(review_data: Dict[str, Any]):
        for key in ("bugs", "errors", "detected_issues"):
            values = review_data.get(key) or []
            if isinstance(values, list):
                for finding in values:
                    if isinstance(finding, dict):
                        yield finding
        for key in ("security", "performance", "code_quality"):
            section = review_data.get(key)
            if not isinstance(section, dict):
                continue
            for value in section.values():
                if isinstance(value, list):
                    for finding in value:
                        if isinstance(finding, dict):
                            yield finding

    def _is_finding_snippet(self, review_data: Dict[str, Any], rel_path: str, code: str) -> bool:
        """Reject a top-level correction that merely repeats a finding snippet."""
        expected_name = self._canonical_source_name(Path(rel_path).name)
        normalized_code = code.strip()
        for finding in self._iter_findings(review_data):
            finding_path = self._safe_relative_path(finding.get("file"))
            if not finding_path or self._canonical_source_name(Path(finding_path).name) != expected_name:
                continue
            snippet = finding.get("after_code") or finding.get("corrected_code")
            if isinstance(snippet, str) and snippet.strip() == normalized_code:
                return True
        return False

    @staticmethod
    def _canonical_source_name(name: str) -> str:
        lowered = name.lower()
        for prefix in ("corrected_", "fixed_", "updated_"):
            if lowered.startswith(prefix):
                return lowered[len(prefix):]
        return lowered

    def _resolve_project_file(self, root: Path, rel_path: str) -> Path:
        candidate = (root / rel_path).resolve()
        try:
            candidate.relative_to(root)
        except ValueError as exc:
            raise ValueError("Correction path is outside the project.") from exc
        if candidate.is_file() and not candidate.is_symlink():
            return candidate

        name = Path(rel_path).name
        same_name = [
            path.resolve() for path in root.rglob(name)
            if path.is_file() and not path.is_symlink()
        ]
        if len(same_name) == 1:
            return same_name[0]

        # Map common AI labels such as corrected_example.java back to the
        # existing example.java, but only when that match is unambiguous.
        lower_name = name.lower()
        for prefix in ("corrected_", "fixed_", "updated_"):
            if lower_name.startswith(prefix):
                original_name = name[len(prefix):]
                matches = [
                    path.resolve() for path in root.rglob(original_name)
                    if path.is_file() and not path.is_symlink()
                ]
                if len(matches) == 1:
                    return matches[0]
                break
        return candidate

    @staticmethod
    def _write_project_file(root: Path, dest_file: Path, code: str):
        dest_file = dest_file.resolve()
        try:
            dest_file.relative_to(root)
        except ValueError as exc:
            raise ValueError("Correction path is outside the project.") from exc
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            dest_file.write_text(code, encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise ValueError(f"Could not write corrected project file {dest_file.name}.") from exc


code_correction_service = CodeCorrectionService()

