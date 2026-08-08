import sqlite3
import os

DB_PATH = "reports/data/reports.db"

def init_db():
    os.makedirs("reports/data", exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rep_id TEXT,
                author_id INTEGER,
                target_id INTEGER,
                channel_id INTEGER,
                status TEXT DEFAULT '🟡 Open',
                moderator_id INTEGER,
                reason TEXT,
                description TEXT
            );
            CREATE TABLE IF NOT EXISTS report_messages (id INTEGER PRIMARY KEY, report_id INTEGER);
            CREATE TABLE IF NOT EXISTS report_history (id INTEGER PRIMARY KEY, report_id INTEGER, action TEXT, actor_id INTEGER, timestamp DATETIME);
        """)

def create_report(author_id, channel_id, reason, description, target_id=None):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            """
            INSERT INTO reports (rep_id, author_id, target_id, channel_id, reason, description)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("pending", author_id, target_id, channel_id, reason, description),
        )
        report_id = cursor.lastrowid
        conn.execute("UPDATE reports SET rep_id = ? WHERE id = ?", (f"R-{report_id:04d}", report_id))
        conn.execute(
            "INSERT INTO report_history (report_id, action, actor_id, timestamp) VALUES (?, 'created', ?, datetime('now'))",
            (report_id, author_id),
        )
        return report_id
