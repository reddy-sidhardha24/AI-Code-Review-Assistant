# ============================================================
# AI CODE REVIEW ASSISTANT
# backend/db/crud.py
# ============================================================

import json
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from .database import get_db_connection


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ============================================================
# USERS CRUD
# ============================================================

def upsert_user(user_id: str, email: str, full_name: Optional[str] = None, image_url: Optional[str] = None) -> Dict[str, Any]:
    """
    Inserts or updates a user in the SQLite database linked to Clerk.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    now = _now_iso()

    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    existing = cursor.fetchone()

    if existing:
        cursor.execute("""
            UPDATE users
            SET email = ?,
                full_name = COALESCE(?, full_name),
                image_url = COALESCE(?, image_url),
                updated_at = ?
            WHERE id = ?
        """, (email, full_name, image_url, now, user_id))
    else:
        cursor.execute("""
            INSERT INTO users (id, email, full_name, image_url, theme_preference, created_at, updated_at)
            VALUES (?, ?, ?, ?, 'dark', ?, ?)
        """, (user_id, email, full_name or "", image_url or "", now, now))

    conn.commit()

    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user_row = cursor.fetchone()
    conn.close()

    return dict(user_row) if user_row else {}


def get_user(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetches a user record by their Clerk user ID.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def update_user_theme(user_id: str, theme: str) -> bool:
    """
    Updates user's selected theme preference in SQLite.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    now = _now_iso()

    # Ensure user exists first or update
    cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO users (id, email, full_name, theme_preference, created_at, updated_at)
            VALUES (?, ?, '', ?, ?, ?)
        """, (user_id, f"{user_id}@user.local", theme, now, now))
    else:
        cursor.execute("""
            UPDATE users
            SET theme_preference = ?, updated_at = ?
            WHERE id = ?
        """, (theme, now, user_id))

    conn.commit()
    conn.close()
    return True


def get_user_theme(user_id: str) -> str:
    """
    Retrieves the user's saved theme preference (defaults to 'dark').
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT theme_preference FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row and row["theme_preference"]:
        return row["theme_preference"]
    return "dark"


# ============================================================
# UPLOADED FILES CRUD
# ============================================================

def create_uploaded_file(
    file_id: str,
    user_id: str,
    file_name: str,
    file_path: str,
    file_size: int,
    file_type: str
) -> Dict[str, Any]:
    """
    Records an uploaded file entry linked to a user.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    now = _now_iso()

    # Ensure foreign key target user exists
    cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    if not cursor.fetchone():
        upsert_user(user_id=user_id, email=f"{user_id}@user.local")

    cursor.execute("""
        INSERT INTO uploaded_files (id, user_id, file_name, file_path, file_size, file_type, upload_time)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (file_id, user_id, file_name, file_path, file_size, file_type, now))

    conn.commit()
    cursor.execute("SELECT * FROM uploaded_files WHERE id = ?", (file_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else {}


def get_user_files(user_id: str) -> List[Dict[str, Any]]:
    """
    Returns all uploaded files for a specific user.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM uploaded_files
        WHERE user_id = ?
        ORDER BY upload_time DESC
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_uploaded_file(file_id: str, user_id: str) -> bool:
    """
    Deletes an uploaded file record belonging to the user.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM uploaded_files
        WHERE id = ? AND user_id = ?
    """, (file_id, user_id))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0


# ============================================================
# REVIEWS CRUD
# ============================================================

def create_review(
    review_id: str,
    user_id: str,
    project_name: str,
    language: str,
    question: str,
    score: Optional[float],
    confidence: Optional[float],
    issue_count: int,
    bugs_count: int,
    security_count: int,
    performance_count: int,
    quality_count: int,
    raw_review: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Saves a code review, its metrics, and complete AI-generated JSON results.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    now = _now_iso()

    # Ensure foreign key target user exists
    cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    if not cursor.fetchone():
        upsert_user(user_id=user_id, email=f"{user_id}@user.local")

    raw_json_str = json.dumps(raw_review)

    cursor.execute("""
        INSERT INTO reviews (
            id, user_id, project_name, language, question, score, confidence,
            issue_count, bugs_count, security_count, performance_count, quality_count,
            raw_review_json, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        review_id, user_id, project_name, language, question, score, confidence,
        issue_count, bugs_count, security_count, performance_count, quality_count,
        raw_json_str, now
    ))

    conn.commit()
    cursor.execute("SELECT * FROM reviews WHERE id = ?", (review_id,))
    row = cursor.fetchone()
    conn.close()

    result = dict(row) if row else {}
    if "raw_review_json" in result and isinstance(result["raw_review_json"], str):
        try:
            result["review"] = json.loads(result["raw_review_json"])
        except Exception:
            result["review"] = {}
    return result


def get_user_reviews(user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Returns list of reviews for the specified user (ordered newest first).
    Includes parsed review JSON for immediate access.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM reviews
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT ?
    """, (user_id, limit))
    rows = cursor.fetchall()
    conn.close()

    results = []
    for r in rows:
        item = dict(r)
        # Parse json for convenience
        try:
            item["review"] = json.loads(item.get("raw_review_json", "{}"))
        except Exception:
            item["review"] = {}
        results.append(item)
    return results


def get_review_by_id(review_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves full details of a specific review if it belongs to the user.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM reviews
        WHERE id = ? AND user_id = ?
    """, (review_id, user_id))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    item = dict(row)
    try:
        item["review"] = json.loads(item.get("raw_review_json", "{}"))
    except Exception:
        item["review"] = {}
    return item


def delete_review(review_id: str, user_id: str) -> bool:
    """
    Deletes a review record belonging to the user.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM reviews
        WHERE id = ? AND user_id = ?
    """, (review_id, user_id))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0


def delete_all_reviews(user_id: str) -> int:
    """
    Deletes all review records for a user.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM reviews
        WHERE user_id = ?
    """, (user_id,))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected


# ============================================================
# USER LLM CONFIGS CRUD
# ============================================================

def list_user_llm_configs(user_id: str) -> List[Dict[str, Any]]:
    """
    Lists all LLM model configurations configured by the user.
    Masks API keys for privacy.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM user_llm_configs
        WHERE user_id = ?
        ORDER BY created_at ASC
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()

    result = []
    for r in rows:
        item = dict(r)
        if item.get("api_key"):
            key = item["api_key"]
            if len(key) > 8:
                item["masked_key"] = f"{key[:4]}...{key[-4:]}"
            else:
                item["masked_key"] = "••••••••"
        else:
            item["masked_key"] = ""
        result.append(item)
    return result


def get_llm_config(config_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetches a specific LLM configuration with unmasked key.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM user_llm_configs
        WHERE id = ? AND user_id = ?
    """, (config_id, user_id))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_active_llm_config(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Returns the currently active LLM configuration for the user.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM user_llm_configs
        WHERE user_id = ? AND is_active = 1
        LIMIT 1
    """, (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def save_llm_config(
    config_id: str,
    user_id: str,
    config_name: str,
    provider: str,
    api_key: Optional[str],
    base_url: Optional[str],
    model_name: str,
    temperature: float = 0.1,
    max_tokens: int = 4096,
    is_active: bool = False
) -> Dict[str, Any]:
    """
    Creates or updates an LLM provider configuration.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    now = _now_iso()

    # If this config will be active, unset any existing active configs
    if is_active:
        cursor.execute("UPDATE user_llm_configs SET is_active = 0 WHERE user_id = ?", (user_id,))

    cursor.execute("SELECT id FROM user_llm_configs WHERE id = ? AND user_id = ?", (config_id, user_id))
    exists = cursor.fetchone()

    if exists:
        # If api_key is None or empty, retain previous api_key
        if not api_key:
            cursor.execute("""
                UPDATE user_llm_configs
                SET config_name = ?, provider = ?, base_url = ?, model_name = ?,
                    temperature = ?, max_tokens = ?, is_active = ?, updated_at = ?
                WHERE id = ? AND user_id = ?
            """, (config_name, provider, base_url, model_name, temperature, max_tokens, 1 if is_active else 0, now, config_id, user_id))
        else:
            cursor.execute("""
                UPDATE user_llm_configs
                SET config_name = ?, provider = ?, api_key = ?, base_url = ?, model_name = ?,
                    temperature = ?, max_tokens = ?, is_active = ?, updated_at = ?
                WHERE id = ? AND user_id = ?
            """, (config_name, provider, api_key, base_url, model_name, temperature, max_tokens, 1 if is_active else 0, now, config_id, user_id))
    else:
        # Check if this is the user's first config; if so, make it active by default
        cursor.execute("SELECT COUNT(*) as cnt FROM user_llm_configs WHERE user_id = ?", (user_id,))
        count = cursor.fetchone()["cnt"]
        actual_active = 1 if (is_active or count == 0) else 0

        cursor.execute("""
            INSERT INTO user_llm_configs
            (id, user_id, config_name, provider, api_key, base_url, model_name, temperature, max_tokens, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (config_id, user_id, config_name, provider, api_key or "", base_url or "", model_name, temperature, max_tokens, actual_active, now, now))

    conn.commit()
    conn.close()
    return get_llm_config(config_id, user_id) or {}


def set_active_llm_config(config_id: str, user_id: str) -> bool:
    """
    Sets the specified config as active and deactivates others.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE user_llm_configs SET is_active = 0 WHERE user_id = ?", (user_id,))
    cursor.execute("UPDATE user_llm_configs SET is_active = 1 WHERE id = ? AND user_id = ?", (config_id, user_id))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0


def get_user_multi_agent_config_ids(user_id: str) -> List[str]:
    """Return the model IDs selected for multi-agent reviews."""
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT config_id FROM user_multi_agent_models WHERE user_id = ? ORDER BY selected_at ASC",
        (user_id,),
    ).fetchall()
    conn.close()
    return [row["config_id"] for row in rows]


def get_user_single_agent_config(user_id: str) -> Optional[Dict[str, Any]]:
    """Return the explicitly selected single-agent model, with legacy active-model fallback."""
    conn = get_db_connection()
    row = conn.execute(
        """SELECT c.* FROM user_single_agent_models AS s
           JOIN user_llm_configs AS c ON c.id = s.config_id AND c.user_id = s.user_id
           WHERE s.user_id = ?""",
        (user_id,),
    ).fetchone()
    if not row:
        row = conn.execute(
            "SELECT * FROM user_llm_configs WHERE user_id = ? ORDER BY is_active DESC, created_at ASC LIMIT 1",
            (user_id,),
        ).fetchone()
    conn.close()
    return dict(row) if row else None


def set_user_single_agent_config_id(user_id: str, config_id: str) -> bool:
    """Persist a single-agent model after verifying it belongs to this user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    owned = cursor.execute(
        "SELECT 1 FROM user_llm_configs WHERE id = ? AND user_id = ?", (config_id, user_id)
    ).fetchone()
    if not owned:
        conn.close()
        return False
    cursor.execute(
        """INSERT INTO user_single_agent_models (user_id, config_id, selected_at) VALUES (?, ?, ?)
           ON CONFLICT(user_id) DO UPDATE SET config_id = excluded.config_id, selected_at = excluded.selected_at""",
        (user_id, config_id, _now_iso()),
    )
    conn.commit()
    conn.close()
    return True


def get_user_single_agent_config_id(user_id: str) -> Optional[str]:
    config = get_user_single_agent_config(user_id)
    return config["id"] if config else None


def get_user_multi_agent_configs(user_id: str) -> List[Dict[str, Any]]:
    """Return selected model configs, including credentials, for backend use only."""
    conn = get_db_connection()
    rows = conn.execute(
        """
        SELECT c.*
        FROM user_multi_agent_models AS m
        JOIN user_llm_configs AS c ON c.id = m.config_id AND c.user_id = m.user_id
        WHERE m.user_id = ?
        ORDER BY m.selected_at ASC
        """,
        (user_id,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def set_user_multi_agent_config_ids(user_id: str, config_ids: List[str]) -> bool:
    """Replace a user's multi-agent pool after validating every config belongs to them."""
    unique_ids = list(dict.fromkeys(str(config_id) for config_id in config_ids if config_id))
    conn = get_db_connection()
    cursor = conn.cursor()
    if unique_ids:
        owned_ids = {
            row["id"]
            for row in cursor.execute(
                "SELECT id FROM user_llm_configs WHERE user_id = ?",
                (user_id,),
            ).fetchall()
        }
        if not set(unique_ids).issubset(owned_ids):
            conn.close()
            return False

    now = _now_iso()
    cursor.execute("DELETE FROM user_multi_agent_models WHERE user_id = ?", (user_id,))
    cursor.executemany(
        "INSERT INTO user_multi_agent_models (user_id, config_id, selected_at) VALUES (?, ?, ?)",
        [(user_id, config_id, now) for config_id in unique_ids],
    )
    conn.commit()
    conn.close()
    return True


def delete_llm_config(config_id: str, user_id: str) -> bool:
    """
    Deletes an LLM configuration.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_llm_configs WHERE id = ? AND user_id = ?", (config_id, user_id))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0


# ============================================================
# USER PREFERENCES CRUD
# ============================================================

def get_user_preferences(user_id: str) -> Dict[str, Any]:
    """
    Fetches user preferences or returns default.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_preferences WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return dict(row)
    return {
        "user_id": user_id,
        "theme": "light",
        "agent_mode": "single",
        "email_api_url": "https://technovacseai.pythonanywhere.com/send-email"
    }


def upsert_user_preferences(
    user_id: str,
    theme: Optional[str] = None,
    agent_mode: Optional[str] = None,
    email_api_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Updates or inserts user preferences.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    now = _now_iso()

    cursor.execute("SELECT * FROM user_preferences WHERE user_id = ?", (user_id,))
    existing = cursor.fetchone()

    if existing:
        cursor.execute("""
            UPDATE user_preferences
            SET theme = COALESCE(?, theme),
                agent_mode = COALESCE(?, agent_mode),
                email_api_url = COALESCE(?, email_api_url),
                updated_at = ?
            WHERE user_id = ?
        """, (theme, agent_mode, email_api_url, now, user_id))
    else:
        cursor.execute("""
            INSERT INTO user_preferences (user_id, theme, agent_mode, email_api_url, created_at, updated_at)
            VALUES (?, COALESCE(?, 'light'), COALESCE(?, 'single'), COALESCE(?, 'https://technovacseai.pythonanywhere.com/send-email'), ?, ?)
        """, (user_id, theme, agent_mode, email_api_url, now, now))

    conn.commit()
    conn.close()
    return get_user_preferences(user_id)


# ============================================================
# GITHUB CONNECTIONS CRUD
# ============================================================

def get_github_connection(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves stored GitHub connection details for a user.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM github_connections WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_github_connection_by_username(username: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves stored GitHub connection details by GitHub username.
    """
    if not username:
        return None
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM github_connections WHERE LOWER(github_username) = LOWER(?) LIMIT 1", (username.strip(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None



def save_github_connection(
    user_id: str,
    github_username: str,
    oauth_token: str,
    installation_id: Optional[str] = None
) -> bool:
    """
    Stores or updates GitHub connection token for a user.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    now = _now_iso()

    cursor.execute("SELECT user_id FROM github_connections WHERE user_id = ?", (user_id,))
    existing = cursor.fetchone()

    if existing:
        cursor.execute("""
            UPDATE github_connections
            SET github_username = ?, oauth_token = ?, installation_id = ?, connected_at = ?
            WHERE user_id = ?
        """, (github_username, oauth_token, installation_id or "", now, user_id))
    else:
        cursor.execute("""
            INSERT INTO github_connections (user_id, github_username, oauth_token, installation_id, connected_at)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, github_username, oauth_token, installation_id or "", now))

    conn.commit()
    conn.close()
    return True


def delete_github_connection(user_id: str) -> bool:
    """
    Disconnects user's GitHub connection.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM github_connections WHERE user_id = ?", (user_id,))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0

