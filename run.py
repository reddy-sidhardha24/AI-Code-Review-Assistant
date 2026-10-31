#!/usr/bin/env python3
"""
Launcher script for AI Code Review Assistant Unified Single Application.
Builds the React frontend if missing and runs FastAPI backend serving both on port 8000.
"""

import os
import sys
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = ROOT_DIR / "frontend"
FRONTEND_BUILD_DIR = FRONTEND_DIR / "build"
BACKEND_DIR = ROOT_DIR / "backend"


def build_frontend():
    print("============================================================")
    print("Building React Frontend static assets...")
    print("============================================================")
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"

    # Install dependencies when missing or out of sync with the lockfile.
    lock_file = FRONTEND_DIR / "package-lock.json"
    installed_lock = FRONTEND_DIR / "node_modules" / ".package-lock.json"
    if (
        not installed_lock.exists()
        or (lock_file.exists() and lock_file.stat().st_mtime > installed_lock.stat().st_mtime)
    ):
        print("Installing frontend dependencies...")
        subprocess.run([npm_cmd, "ci"], cwd=FRONTEND_DIR, check=True)

    # Build frontend
    subprocess.run([npm_cmd, "run", "build"], cwd=FRONTEND_DIR, check=True)
    print("Frontend build complete!")


def frontend_build_is_stale():
    index_file = FRONTEND_BUILD_DIR / "index.html"
    if not index_file.exists():
        return True

    built_at = index_file.stat().st_mtime
    source_paths = [
        FRONTEND_DIR / "src",
        FRONTEND_DIR / "public",
        FRONTEND_DIR / "package.json",
        FRONTEND_DIR / "package-lock.json",
        FRONTEND_DIR / ".env",
    ]
    for source_path in source_paths:
        if source_path.is_file() and source_path.stat().st_mtime > built_at:
            return True
        if source_path.is_dir():
            for path in source_path.rglob("*"):
                if path.is_file() and path.stat().st_mtime > built_at:
                    return True
    return False


def main():
    # This launcher is for local development. Production launchers must use
    # APP_ENV=production and configure Clerk JWT verification.
    os.environ.setdefault("APP_ENV", "development")
    force_build = "--build" in sys.argv

    if force_build or frontend_build_is_stale():
        build_frontend()

    print("============================================================")
    print("Starting AI Code Review Assistant Unified Server...")
    print("Application available at: http://localhost:8000")
    print("============================================================")

    import uvicorn
    import threading
    import webbrowser

    # Open browser automatically after 1.5 seconds
    threading.Timer(1.5, lambda: webbrowser.open("http://localhost:8000")).start()

    sys.path.insert(0, str(BACKEND_DIR))
    # Backend storage paths (uploads, extracted projects, and vector_db) are
    # relative to the backend directory. Match the direct uvicorn and Docker
    # launchers so running this script from the repository root uses the same data.
    os.chdir(BACKEND_DIR)
    # This launcher enables local development auth, so keep it off network interfaces.
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=False, app_dir=str(BACKEND_DIR))


if __name__ == "__main__":
    main()
