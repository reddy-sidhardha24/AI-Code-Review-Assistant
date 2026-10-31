# ============================================================
# AI CODE REVIEW ASSISTANT
# backend/db/database.py
# ============================================================

import sqlite3
import os
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "code_review.db"


def get_db_connection() -> sqlite3.Connection:
    """
    Returns a configured SQLite database connection with row factory
    enabled for dictionary-like column access.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False, timeout=15.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn


def init_db():
    """
    Initializes the SQLite database tables if they do not already exist.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Users Table (Linked with Clerk / Local)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT NOT NULL,
            full_name TEXT,
            image_url TEXT,
            theme_preference TEXT DEFAULT 'light',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    # 2. Uploaded Files Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS uploaded_files (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            file_name TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            file_type TEXT NOT NULL,
            upload_time TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    # 3. Reviews Table (Code Review History & Full AI Results)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            project_name TEXT NOT NULL,
            language TEXT,
            question TEXT NOT NULL,
            score REAL,
            confidence REAL,
            issue_count INTEGER DEFAULT 0,
            bugs_count INTEGER DEFAULT 0,
            security_count INTEGER DEFAULT 0,
            performance_count INTEGER DEFAULT 0,
            quality_count INTEGER DEFAULT 0,
            raw_review_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    # 4. User LLM Provider Configurations (Unlimited models per user)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_llm_configs (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            config_name TEXT NOT NULL,
            provider TEXT NOT NULL,
            api_key TEXT,
            base_url TEXT,
            model_name TEXT NOT NULL,
            temperature REAL DEFAULT 0.1,
            max_tokens INTEGER DEFAULT 4096,
            is_active INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    # Multi-agent model pool is independent of the single-agent active model.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_multi_agent_models (
            user_id TEXT NOT NULL,
            config_id TEXT NOT NULL,
            selected_at TEXT NOT NULL,
            PRIMARY KEY (user_id, config_id),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (config_id) REFERENCES user_llm_configs(id) ON DELETE CASCADE
        )
    """)

    # Single-agent model choice is independent from model configuration and the multi-agent pool.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_single_agent_models (
            user_id TEXT PRIMARY KEY,
            config_id TEXT NOT NULL,
            selected_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (config_id) REFERENCES user_llm_configs(id) ON DELETE CASCADE
        )
    """)

    # 5. User App Preferences
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_preferences (
            user_id TEXT PRIMARY KEY,
            theme TEXT DEFAULT 'light',
            agent_mode TEXT DEFAULT 'single',
            email_api_url TEXT DEFAULT 'https://technovacseai.pythonanywhere.com/send-email',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    # 6. GitHub App OAuth Connections
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS github_connections (
            user_id TEXT PRIMARY KEY,
            github_username TEXT,
            oauth_token TEXT,
            installation_id TEXT,
            connected_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    # Indices for fast queries
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reviews_user_id ON reviews(user_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reviews_created_at ON reviews(created_at DESC);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_user_id ON uploaded_files(user_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_llm_configs_user_id ON user_llm_configs(user_id);")

    conn.commit()
    conn.close()
    print(f"[DB] SQLite database initialized successfully at: {DB_PATH}")


if __name__ == "__main__":
    init_db()
