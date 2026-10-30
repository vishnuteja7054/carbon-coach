"""
SQLite persistence store for Carbon Coach.

Provides deterministic storage of logged activities across sessions so the agent
can answer questions like "How did I do today?" or "How did I do this week?"
and compute personalized reduction tips from actual historical data.
"""

import os
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional

DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "carbon_memory.db",
)


def get_db_path() -> str:
    return os.environ.get("CARBON_DB_PATH", DEFAULT_DB_PATH)


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initialize SQLite tables if they do not exist."""
    conn = _get_connection()
    try:
        with conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS activity_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL DEFAULT 'default_user',
                    category TEXT NOT NULL,
                    subcategory TEXT NOT NULL,
                    label TEXT NOT NULL,
                    quantity REAL NOT NULL,
                    unit TEXT NOT NULL,
                    kg_co2e REAL NOT NULL,
                    formula TEXT NOT NULL,
                    source TEXT NOT NULL,
                    group_name TEXT NOT NULL DEFAULT 'General',
                    logged_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_activity_user_time
                ON activity_logs (user_id, logged_at)
                """
            )
    finally:
        conn.close()


def insert_activity(
    category: str,
    subcategory: str,
    label: str,
    quantity: float,
    unit: str,
    kg_co2e: float,
    formula: str,
    source: str,
    user_id: str = "default_user",
    group_name: str = "General",
    logged_at: Optional[str] = None,
) -> Dict[str, Any]:
    """Insert a single calculated emission activity into SQLite."""
    init_db()
    ts = logged_at or datetime.now(timezone.utc).isoformat()
    rounded_co2 = round(float(kg_co2e), 4)
    rounded_qty = round(float(quantity), 4)

    conn = _get_connection()
    try:
        with conn:
            cursor = conn.execute(
                """
                INSERT INTO activity_logs (
                    user_id, category, subcategory, label,
                    quantity, unit, kg_co2e, formula, source, group_name, logged_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    category.lower().strip(),
                    subcategory.lower().strip(),
                    label,
                    rounded_qty,
                    unit,
                    rounded_co2,
                    formula,
                    source,
                    group_name,
                    ts,
                ),
            )
            row_id = cursor.lastrowid
    finally:
        conn.close()

    return {
        "id": row_id,
        "user_id": user_id,
        "category": category.lower().strip(),
        "subcategory": subcategory.lower().strip(),
        "label": label,
        "quantity": rounded_qty,
        "unit": unit,
        "kg_co2e": rounded_co2,
        "formula": formula,
        "source": source,
        "group_name": group_name,
        "logged_at": ts,
    }


def fetch_activities(
    period: str = "today",
    user_id: str = "default_user",
) -> List[Dict[str, Any]]:
    """
    Fetch activities for a user within the requested period:
    - 'today' / 'daily' / 'day': last 24 hours / current UTC date
    - 'week' / 'weekly' / '7d': last 7 days
    - 'month' / 'monthly' / '30d': last 30 days
    - 'all' / 'session': all logged activities
    """
    init_db()
    now = datetime.now(timezone.utc)
    p = period.lower().strip()

    if p in ("today", "daily", "day", "24h"):
        start_dt = now - timedelta(hours=24)
    elif p in ("week", "weekly", "this_week", "this week", "7d"):
        start_dt = now - timedelta(days=7)
    elif p in ("month", "monthly", "this_month", "this month", "30d"):
        start_dt = now - timedelta(days=30)
    else:
        start_dt = None

    conn = _get_connection()
    try:
        if start_dt is not None:
            rows = conn.execute(
                """
                SELECT * FROM activity_logs
                WHERE user_id = ? AND logged_at >= ?
                ORDER BY id ASC
                """,
                (user_id, start_dt.isoformat()),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT * FROM activity_logs
                WHERE user_id = ?
                ORDER BY id ASC
                """,
                (user_id,),
            ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def clear_user_activities(user_id: str = "default_user") -> int:
    """Delete all logged activities for a given user_id and return count removed."""
    init_db()
    conn = _get_connection()
    try:
        with conn:
            cursor = conn.execute(
                "DELETE FROM activity_logs WHERE user_id = ?",
                (user_id,),
            )
            return cursor.rowcount
    finally:
        conn.close()


def get_leaderboard_stats() -> List[Dict[str, Any]]:
    """Aggregate logged emissions by group_name for community/campus leaderboard."""
    init_db()
    conn = _get_connection()
    try:
        rows = conn.execute(
            """
            SELECT
                group_name,
                COUNT(*) AS activities_count,
                COUNT(DISTINCT user_id) AS participants,
                ROUND(SUM(kg_co2e), 3) AS total_kg_co2e,
                ROUND(AVG(kg_co2e), 3) AS avg_kg_per_activity
            FROM activity_logs
            GROUP BY group_name
            ORDER BY total_kg_co2e ASC
            """
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
