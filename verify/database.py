# verify/database.py

import sqlite3
from pathlib import Path
from contextlib import contextmanager

SQLITE_DB_PATH = Path("verify/data/verify.db")


def db_connect():
    connection = sqlite3.connect(SQLITE_DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


@contextmanager
def database_connection():
    SQLITE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = db_connect()
    try:
        yield connection
    finally:
        connection.close()


def init_database() -> None:
    with database_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS voice_totals (
                member_id TEXT PRIMARY KEY,
                seconds INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS support_daily (
                day TEXT NOT NULL,
                member_id TEXT NOT NULL,
                seconds INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (day, member_id)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS active_voice (
                member_id TEXT PRIMARY KEY,
                joined_at REAL NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS daily_reports (
                day TEXT PRIMARY KEY
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS support_actions (
                day TEXT NOT NULL,
                member_id TEXT NOT NULL,
                verified INTEGER NOT NULL DEFAULT 0,
                no_access INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (day, member_id)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS support_reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                day TEXT NOT NULL,
                member_id TEXT NOT NULL,
                reviewer_id TEXT NOT NULL,
                reviewer_name TEXT NOT NULL,
                rating INTEGER NOT NULL,
                comment TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
            """
        )
        connection.commit()


def load_stats_db():
    init_database()
    with database_connection() as connection:
        cursor = connection.cursor()

        cursor.execute("SELECT member_id, seconds FROM voice_totals")
        voice_total_seconds = {str(row[0]): int(row[1]) for row in cursor.fetchall()}

        cursor.execute("SELECT day, member_id, seconds FROM support_daily")
        support_daily_seconds = {}
        for day, member_id, seconds in cursor.fetchall():
            support_daily_seconds.setdefault(str(day), {})[str(member_id)] = int(seconds)

        cursor.execute("SELECT day, member_id, verified, no_access FROM support_actions")
        support_action_stats = {}
        for day, member_id, verified, no_access in cursor.fetchall():
            support_action_stats.setdefault(str(day), {})[str(member_id)] = {
                "verified": int(verified),
                "no_access": int(no_access),
                "reviews": [],
            }

        cursor.execute(
            """
            SELECT day, member_id, reviewer_id, reviewer_name, rating, comment, timestamp
            FROM support_reviews
            ORDER BY timestamp DESC
            """
        )
        for day, member_id, reviewer_id, reviewer_name, rating, comment, timestamp in cursor.fetchall():
            day_stats = support_action_stats.setdefault(str(day), {})
            member_stats = day_stats.setdefault(str(member_id), {"verified": 0, "no_access": 0, "reviews": []})
            reviews = member_stats.setdefault("reviews", [])
            reviews.append(
                {
                    "reviewer_id": int(reviewer_id),
                    "reviewer_name": str(reviewer_name),
                    "rating": int(rating),
                    "comment": str(comment),
                    "timestamp": str(timestamp),
                }
            )

        cursor.execute("SELECT member_id, joined_at FROM active_voice")
        persisted_voice_joined_at = {str(row[0]): float(row[1]) for row in cursor.fetchall()}

        cursor.execute("SELECT day FROM daily_reports")
        daily_report_sent_dates = {str(row[0]) for row in cursor.fetchall()}

    return (
        voice_total_seconds,
        support_daily_seconds,
        support_action_stats,
        persisted_voice_joined_at,
        daily_report_sent_dates,
    )


def save_stats_db(
    voice_total_seconds,
    support_daily_seconds,
    support_action_stats,
    voice_joined_at,
    daily_report_sent_dates,
):
    with database_connection() as connection:
        cursor = connection.cursor()
        for table in (
            "voice_totals",
            "support_daily",
            "support_actions",
            "support_reviews",
            "active_voice",
            "daily_reports",
        ):
            cursor.execute(f"DELETE FROM {table}")

        cursor.executemany(
            "INSERT INTO voice_totals (member_id, seconds) VALUES (?, ?)",
            [(str(member_id), int(seconds)) for member_id, seconds in voice_total_seconds.items()],
        )

        cursor.executemany(
            "INSERT INTO support_daily (day, member_id, seconds) VALUES (?, ?, ?)",
            [
                (str(day), str(member_id), int(seconds))
                for day, members in support_daily_seconds.items()
                for member_id, seconds in members.items()
            ],
        )

        action_rows = []
        review_rows = []
        for day, members in support_action_stats.items():
            for member_id, stats in members.items():
                if not isinstance(stats, dict):
                    continue
                action_rows.append(
                    (
                        str(day),
                        str(member_id),
                        int(stats.get("verified", 0) or 0),
                        int(stats.get("no_access", 0) or 0),
                    )
                )
                reviews = stats.get("reviews", [])
                if isinstance(reviews, list):
                    for review in reviews:
                        if not isinstance(review, dict):
                            continue
                        review_rows.append(
                            (
                                str(day),
                                str(member_id),
                                str(review.get("reviewer_id", "")),
                                str(review.get("reviewer_name", "")),
                                int(review.get("rating", 0) or 0),
                                str(review.get("comment", "")),
                                str(review.get("timestamp", "")),
                            )
                        )

        cursor.executemany(
            "INSERT INTO support_actions (day, member_id, verified, no_access) VALUES (?, ?, ?, ?)",
            action_rows,
        )
        cursor.executemany(
            "INSERT INTO support_reviews (day, member_id, reviewer_id, reviewer_name, rating, comment, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
            review_rows,
        )
        cursor.executemany(
            "INSERT INTO active_voice (member_id, joined_at) VALUES (?, ?)",
            [(str(member_id), float(joined_at)) for member_id, joined_at in voice_joined_at.items()],
        )
        cursor.executemany(
            "INSERT INTO daily_reports (day) VALUES (?)",
            [(str(day),) for day in sorted(daily_report_sent_dates)],
        )
        connection.commit()
