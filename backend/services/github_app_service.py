# ============================================================
# AI CODE REVIEW ASSISTANT
# backend/services/github_app_service.py
# Full GitHub App Integration: Pull, Fix, Branch, Push & Pull Request
# ============================================================

import os
import time
import base64
import requests
import jwt
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import quote


class GitHubAppService:
    """
    Manages GitHub App authentication, repository inspection, file retrieval,
    branch creation, committing corrected files, and opening Pull Requests.
    """

    APP_ID = "5218343"
    CLIENT_ID = "Iv23lilooFY7ZcuIZtSp"
    APP_NAME = "code-review-assistant-project"
    BASE_API = "https://api.github.com"

    def __init__(self):
        self.backend_dir = Path(__file__).resolve().parent.parent
        self.root_dir = self.backend_dir.parent

    def find_private_key(self) -> Optional[str]:
        """
        Locates the GitHub App private key PEM file across common project locations.
        """
        # Check environment variable first
        env_key = os.getenv("GITHUB_APP_PRIVATE_KEY")
        if env_key and "-----BEGIN" in env_key:
            return env_key

        candidate_paths = [
            self.backend_dir / "github-app-private-key.pem",
            self.root_dir / "github-app-private-key.pem",
            self.backend_dir / "private-key.pem",
            self.root_dir / "private-key.pem",
        ]

        for p in candidate_paths:
            if p.exists() and p.is_file():
                try:
                    content = p.read_text(encoding="utf-8").strip()
                    if "-----BEGIN" in content:
                        return content
                except Exception:
                    pass

        # Glob for any .pem file in backend or root (excluding virtual environments)
        for d in [self.backend_dir, self.root_dir]:
            for pem_file in d.glob("*.pem"):
                if "venv" not in str(pem_file) and "cacert" not in str(pem_file).lower():
                    try:
                        content = pem_file.read_text(encoding="utf-8").strip()
                        if "-----BEGIN" in content:
                            return content
                    except Exception:
                        pass

        return None

    def generate_jwt(self) -> str:
        """
        Generates a signed RS256 JWT valid for 9 minutes using the GitHub App Private Key.
        """
        key_content = self.find_private_key()
        if not key_content:
            raise FileNotFoundError(
                "GitHub App Private Key (.pem file) was not found in backend/ or root directory. "
                "Please place your downloaded GitHub App private key (.pem file) in the project."
            )

        now = int(time.time())
        payload = {
            "iat": now - 60,       # 1 minute clock skew
            "exp": now + (9 * 60), # 9 minutes
            "iss": self.APP_ID
        }

        token = jwt.encode(payload, key_content, algorithm="RS256")
        return token if isinstance(token, str) else token.decode("utf-8")

    def get_installation_access_token(self, installation_id: str) -> str:
        """
        Exchanges GitHub App installation ID for a short-lived scoped installation access token.
        """
        app_jwt = self.generate_jwt()
        headers = {
            "Authorization": f"Bearer {app_jwt}",
            "Accept": "application/vnd.github+json"
        }
        url = f"{self.BASE_API}/app/installations/{installation_id}/access_tokens"
        res = requests.post(url, headers=headers, timeout=20)
        if res.status_code != 201:
            raise RuntimeError(f"Failed to generate installation token ({res.status_code}): {res.text}")
        return res.json().get("token")

    def list_accessible_repositories(self, auth_token: str, installation_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Lists repositories accessible to this user/installation.
        Supports both installation access tokens and user OAuth tokens.
        """
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Accept": "application/vnd.github+json"
        }

        # Try user repos endpoint first
        res = requests.get(f"{self.BASE_API}/user/repos?per_page=100&sort=updated", headers=headers, timeout=20)
        if res.status_code == 200:
            repos = res.json()
            return [
                {
                    "id": r["id"],
                    "name": r["name"],
                    "full_name": r["full_name"],
                    "owner": r["owner"]["login"],
                    "default_branch": r.get("default_branch", "main"),
                    "private": r.get("private", False),
                    "html_url": r["html_url"],
                    "description": r.get("description", "")
                }
                for r in repos
            ]

        # If token was an installation token, try installation repos
        res_inst = requests.get(f"{self.BASE_API}/installation/repositories?per_page=100", headers=headers, timeout=20)
        if res_inst.status_code == 200:
            data = res_inst.json()
            return [
                {
                    "id": r["id"],
                    "name": r["name"],
                    "full_name": r["full_name"],
                    "owner": r["owner"]["login"],
                    "default_branch": r.get("default_branch", "main"),
                    "private": r.get("private", False),
                    "html_url": r["html_url"],
                    "description": r.get("description", "")
                }
                for r in data.get("repositories", [])
            ]

        return []

    def get_repo_branches(self, auth_token: str, owner: str, repo: str) -> List[str]:
        """
        Lists branch names for the given repository.
        """
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Accept": "application/vnd.github+json"
        }
        res = requests.get(f"{self.BASE_API}/repos/{owner}/{repo}/branches", headers=headers, timeout=15)
        if res.status_code == 200:
            return [b["name"] for b in res.json()]
        return ["main", "master"]

    def create_branch(self, auth_token: str, owner: str, repo: str, base_branch: str, new_branch_name: str) -> Tuple[bool, str]:
        """
        Creates a new git branch off the latest commit of base_branch.
        Dynamically auto-resolves repository default branch if requested branch doesn't exist (e.g. master vs main).
        """
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Accept": "application/vnd.github+json"
        }
        effective_base = (base_branch or "main").strip()
        ref_res = requests.get(f"{self.BASE_API}/repos/{owner}/{repo}/git/ref/heads/{effective_base}", headers=headers, timeout=15)

        if ref_res.status_code != 200:
            print(f"[GitHub] Base branch '{effective_base}' not found ({ref_res.status_code}). Resolving repository default branch...")

            # Fetch repository metadata to determine actual default branch
            repo_res = requests.get(f"{self.BASE_API}/repos/{owner}/{repo}", headers=headers, timeout=15)
            detected_default = None
            if repo_res.status_code == 200:
                detected_default = repo_res.json().get("default_branch")

            candidate_branches = []
            if detected_default:
                candidate_branches.append(detected_default)
            candidate_branches.extend(["main", "master", "develop", "dev"])

            found = False
            for cand in candidate_branches:
                if cand == effective_base:
                    continue
                cand_res = requests.get(f"{self.BASE_API}/repos/{owner}/{repo}/git/ref/heads/{cand}", headers=headers, timeout=15)
                if cand_res.status_code == 200:
                    ref_res = cand_res
                    effective_base = cand
                    found = True
                    print(f"[GitHub] Successfully resolved base branch to '{effective_base}'.")
                    break

            if not found:
                branches_res = requests.get(f"{self.BASE_API}/repos/{owner}/{repo}/branches", headers=headers, timeout=15)
                if branches_res.status_code == 200 and len(branches_res.json()) > 0:
                    first_branch = branches_res.json()[0]["name"]
                    cand_res = requests.get(f"{self.BASE_API}/repos/{owner}/{repo}/git/ref/heads/{first_branch}", headers=headers, timeout=15)
                    if cand_res.status_code == 200:
                        ref_res = cand_res
                        effective_base = first_branch
                        found = True
                        print(f"[GitHub] Successfully resolved base branch to '{effective_base}'.")

            if not found:
                raise RuntimeError(f"Base branch '{base_branch}' not found and no active branch located on repository '{owner}/{repo}'.")

        base_sha = ref_res.json()["object"]["sha"]

        # 2. Create new branch ref
        create_res = requests.post(
            f"{self.BASE_API}/repos/{owner}/{repo}/git/refs",
            headers=headers,
            json={
                "ref": f"refs/heads/{new_branch_name}",
                "sha": base_sha
            },
            timeout=15
        )

        if create_res.status_code == 422:
            # Branch already exists, update ref or accept
            return True, effective_base
        elif create_res.status_code != 201:
            raise RuntimeError(f"Failed to create branch '{new_branch_name}' ({create_res.status_code}): {create_res.text}")

        return True, effective_base

    def commit_file_change(
        self,
        auth_token: str,
        owner: str,
        repo: str,
        branch: str,
        file_path: str,
        file_content: str,
        commit_message: str
    ) -> bool:
        """
        Commits an updated or new file to the specified branch.
        """
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Accept": "application/vnd.github+json"
        }
        clean_path = self._normalize_repo_file_path(file_path)
        encoded_path = quote(clean_path, safe="/")

        # 1. Check if file exists to acquire its SHA
        get_res = requests.get(
            f"{self.BASE_API}/repos/{owner}/{repo}/contents/{encoded_path}?ref={quote(branch, safe='')}",
            headers=headers,
            timeout=15
        )

        payload: Dict[str, Any] = {
            "message": commit_message,
            "content": base64.b64encode(file_content.encode("utf-8")).decode("utf-8"),
            "branch": branch
        }

        if get_res.status_code == 200:
            payload["sha"] = get_res.json().get("sha")

        put_res = requests.put(
            f"{self.BASE_API}/repos/{owner}/{repo}/contents/{encoded_path}",
            headers=headers,
            json=payload,
            timeout=20
        )

        if put_res.status_code not in (200, 201):
            raise RuntimeError(f"Failed to commit {clean_path} ({put_res.status_code}): {put_res.text}")

        return True

    @staticmethod
    def _normalize_repo_file_path(file_path: str) -> str:
        """Normalize a project-relative path for GitHub's Contents API."""
        raw_path = str(file_path or "").strip().replace("\\", "/")
        # Filter duplicate separators and harmless current-directory segments;
        # reject traversal and drive-qualified paths instead of sending invalid
        # or out-of-repository paths to GitHub.
        parts = [part for part in raw_path.split("/") if part not in ("", ".")]
        if not parts or any(part == ".." for part in parts) or ":" in parts[0]:
            raise ValueError("Corrected file path must be a safe project-relative path.")
        return "/".join(parts)

    def create_pull_request(
        self,
        auth_token: str,
        owner: str,
        repo: str,
        head_branch: str,
        base_branch: str,
        title: str,
        body: str
    ) -> Dict[str, Any]:
        """
        Opens a new Pull Request on GitHub.
        """
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Accept": "application/vnd.github+json"
        }

        payload = {
            "title": title,
            "body": body,
            "head": head_branch,
            "base": base_branch
        }

        res = requests.post(f"{self.BASE_API}/repos/{owner}/{repo}/pulls", headers=headers, json=payload, timeout=20)
        if res.status_code == 201:
            data = res.json()
            return {
                "success": True,
                "pr_number": data["number"],
                "html_url": data["html_url"],
                "title": data["title"],
                "head": head_branch,
                "base": base_branch
            }
        else:
            raise RuntimeError(f"Failed to create pull request ({res.status_code}): {res.text}")

    def push_review_fixes_and_open_pr(
        self,
        auth_token: str,
        owner: str,
        repo: str,
        base_branch: str,
        corrected_files: List[Dict[str, str]],
        pr_title: Optional[str] = None,
        pr_body: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes the complete workflow:
        1. Creates a separate branch: ai-review/fix-{timestamp}
        2. Commits each corrected code file to the branch
        3. Opens a clean Pull Request targeting base_branch
        """
        if not corrected_files:
            raise ValueError("No corrected files were provided to commit.")

        timestamp_str = datetime.now().strftime("%Y%m%d-%H%M%S") if 'datetime' in globals() else str(int(time.time()))
        new_branch = f"ai-review/fix-{timestamp_str}"

        # 1. Create branch (auto-resolves default branch if base_branch doesn't exist)
        _, effective_base = self.create_branch(auth_token, owner, repo, base_branch, new_branch)

        # 2. Commit each file
        committed_paths = []
        for item in corrected_files:
            fpath = item.get("path") or item.get("file_name") or "corrected_file.py"
            content = item.get("code") or item.get("content") or ""
            if content.strip():
                msg = f"fix(ai-review): apply verified correction to {fpath}"
                self.commit_file_change(auth_token, owner, repo, new_branch, fpath, content, msg)
                committed_paths.append(fpath)

        # 3. Create PR targeting effective_base branch
        title = pr_title or f"AI Code Review: Automated Corrections ({len(committed_paths)} files)"
        body = pr_body or (
            f"## 🤖 AI Code Review Automated Fixes\n\n"
            f"This pull request contains verified corrections generated by the **AI Code Review Assistant**.\n\n"
            f"### Modified Files:\n" +
            "\n".join([f"- `{p}`" for p in committed_paths]) +
            f"\n\n---\n*Branch:* `{new_branch}` → `{effective_base}`\n"
            f"*Generated by [Code Review Assistant](https://github.com/apps/code-review-assistant-project)*"
        )

        pr_info = self.create_pull_request(auth_token, owner, repo, new_branch, effective_base, title, body)
        pr_info["branch"] = new_branch
        pr_info["base_branch"] = effective_base
        pr_info["files_changed"] = len(committed_paths)
        return pr_info


github_app_service = GitHubAppService()

