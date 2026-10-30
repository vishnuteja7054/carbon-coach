"""SQLite persistence layer for Carbon Coach."""
from .store import (
    get_db_path,
    init_db,
    insert_activity,
    fetch_activities,
    clear_user_activities,
    get_leaderboard_stats,
)

__all__ = [
    "get_db_path",
    "init_db",
    "insert_activity",
    "fetch_activities",
    "clear_user_activities",
    "get_leaderboard_stats",
]
