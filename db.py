import sqlite3
from datetime import datetime, timedelta
from typing import Optional, List, Dict

DB_PATH = "logs.db"

class LogsDB:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._init_db()

    def _init_db(self):
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS logs (
                id TEXT,
                tweet TEXT UNIQUE,
                response TEXT,
                user_name TEXT,
                tweet_url TEXT
            )
            """
        )
        self.conn.commit()

    def insert_log(self, id: str, tweet: str, user_name: str, model_response: str, tweet_url: Optional[str] = None) -> None:
        self.cursor.execute(
            """
            INSERT OR IGNORE INTO logs (id, tweet, user_name, response, tweet_url)
            VALUES (?, ?, ?, ?, ?)
            """,
            (id, tweet, user_name, model_response, tweet_url),
        )
        self.conn.commit()

    def tweet_exists(self, tweet_text: str) -> bool:
        self.cursor.execute("SELECT EXISTS(SELECT 1 FROM logs WHERE tweet = ?)", (tweet_text,))
        result = self.cursor.fetchone()[0]
        return bool(result)

    def get_ai_related_logs(self, since: Optional[str] = None) -> List[Dict]:
        if since is None:
            since = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute(
            """
            SELECT id, tweet, response, user_name, tweet_url
            FROM logs
            WHERE response = 1
            AND id >= ?
            ORDER BY id DESC
            """,
            (since,),
        )
        columns = ["id", "tweet", "response", "user_name", "tweet_url"]
        results = [dict(zip(columns, row)) for row in self.cursor.fetchall()]
        return results

    def close(self):
        self.conn.close()
