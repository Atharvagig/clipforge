import sqlite3
import json
import os
from clipforge.config.config import DB_PATH, DEFAULT_SETTINGS

class DatabaseManager:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Initializes the database schema and default settings."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Settings Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            
            # Populate settings with defaults if they don't exist
            for key, val in DEFAULT_SETTINGS.items():
                cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, val))

            # 2. Videos Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS videos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    file_path TEXT,
                    youtube_url TEXT,
                    duration REAL,
                    status TEXT DEFAULT 'ingested',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 3. Transcripts Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transcripts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id INTEGER NOT NULL,
                    start_time REAL NOT NULL,
                    end_time REAL NOT NULL,
                    text TEXT NOT NULL,
                    speaker TEXT DEFAULT 'Speaker 1',
                    words TEXT, -- JSON list of word dicts [{"word": "...", "start": 0.1, "end": 0.5}]
                    FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE
                )
            """)

            # 4. Clips Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS clips (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    start_time REAL NOT NULL,
                    end_time REAL NOT NULL,
                    viral_score INTEGER DEFAULT 0,
                    hook TEXT,
                    caption TEXT,
                    description TEXT,
                    tags TEXT,
                    status TEXT DEFAULT 'detected',
                    export_path TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE
                )
            """)

            # 5. Upload Queue Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS upload_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    clip_id INTEGER NOT NULL,
                    platform TEXT NOT NULL,
                    scheduled_time DATETIME NOT NULL,
                    status TEXT DEFAULT 'queued',
                    retry_count INTEGER DEFAULT 0,
                    error_message TEXT,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (clip_id) REFERENCES clips(id) ON DELETE CASCADE
                )
            """)

            # 6. Analytics Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    clip_id INTEGER NOT NULL,
                    platform TEXT NOT NULL,
                    views INTEGER DEFAULT 0,
                    watch_time REAL DEFAULT 0.0,
                    likes INTEGER DEFAULT 0,
                    retention_rate REAL DEFAULT 0.0,
                    ctr REAL DEFAULT 0.0,
                    snapshot_date DATE DEFAULT (CURRENT_DATE),
                    FOREIGN KEY (clip_id) REFERENCES clips(id) ON DELETE CASCADE
                )
            """)
            
            conn.commit()

    # --- Settings Operations ---
    def get_setting(self, key, default=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row["value"] if row else default

    def set_setting(self, key, value):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
            conn.commit()

    def get_all_settings(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM settings")
            return {row["key"]: row["value"] for row in cursor.fetchall()}

    # --- Videos Operations ---
    def add_video(self, title, file_path=None, youtube_url=None, duration=0.0):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO videos (title, file_path, youtube_url, duration, status) VALUES (?, ?, ?, ?, 'ingested')",
                (title, file_path, youtube_url, duration)
            )
            conn.commit()
            return cursor.lastrowid

    def get_video(self, video_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM videos WHERE id = ?", (video_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_all_videos(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM videos ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]

    def update_video_status(self, video_id, status):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE videos SET status = ? WHERE id = ?", (status, video_id))
            conn.commit()

    def update_video_details(self, video_id, title=None, duration=None, file_path=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if title is not None:
                cursor.execute("UPDATE videos SET title = ? WHERE id = ?", (title, video_id))
            if duration is not None:
                cursor.execute("UPDATE videos SET duration = ? WHERE id = ?", (duration, video_id))
            if file_path is not None:
                cursor.execute("UPDATE videos SET file_path = ? WHERE id = ?", (file_path, video_id))
            conn.commit()

    def delete_video(self, video_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM videos WHERE id = ?", (video_id,))
            conn.commit()

    # --- Transcripts Operations ---
    def add_transcript_segment(self, video_id, start_time, end_time, text, speaker="Speaker 1", words=None):
        words_json = json.dumps(words) if words else None
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO transcripts (video_id, start_time, end_time, text, speaker, words) VALUES (?, ?, ?, ?, ?, ?)",
                (video_id, start_time, end_time, text, speaker, words_json)
            )
            conn.commit()
            return cursor.lastrowid

    def get_transcripts_for_video(self, video_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM transcripts WHERE video_id = ? ORDER BY start_time ASC", (video_id,))
            rows = cursor.fetchall()
            result = []
            for row in rows:
                d = dict(row)
                d["words"] = json.loads(d["words"]) if d["words"] else []
                result.append(d)
            return result

    def clear_transcripts_for_video(self, video_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM transcripts WHERE video_id = ?", (video_id,))
            conn.commit()

    # --- Clips Operations ---
    def add_clip(self, video_id, title, start_time, end_time, viral_score=0, hook="", caption="", description="", tags=""):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO clips (video_id, title, start_time, end_time, viral_score, hook, caption, description, tags, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'detected')""",
                (video_id, title, start_time, end_time, viral_score, hook, caption, description, tags)
            )
            conn.commit()
            return cursor.lastrowid

    def get_clip(self, clip_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM clips WHERE id = ?", (clip_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_clips_for_video(self, video_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM clips WHERE video_id = ? ORDER BY start_time ASC", (video_id,))
            return [dict(row) for row in cursor.fetchall()]

    def get_all_clips(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.*, v.title as video_title 
                FROM clips c 
                JOIN videos v ON c.video_id = v.id 
                ORDER BY c.created_at DESC
            """)
            return [dict(row) for row in cursor.fetchall()]

    def update_clip_status(self, clip_id, status, export_path=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if export_path:
                cursor.execute("UPDATE clips SET status = ?, export_path = ? WHERE id = ?", (status, export_path, clip_id))
            else:
                cursor.execute("UPDATE clips SET status = ? WHERE id = ?", (status, clip_id))
            conn.commit()

    def update_clip_metadata(self, clip_id, title=None, hook=None, caption=None, description=None, tags=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            fields = []
            params = []
            if title is not None:
                fields.append("title = ?")
                params.append(title)
            if hook is not None:
                fields.append("hook = ?")
                params.append(hook)
            if caption is not None:
                fields.append("caption = ?")
                params.append(caption)
            if description is not None:
                fields.append("description = ?")
                params.append(description)
            if tags is not None:
                fields.append("tags = ?")
                params.append(tags)
            
            if fields:
                params.append(clip_id)
                query = f"UPDATE clips SET {', '.join(fields)} WHERE id = ?"
                cursor.execute(query, params)
                conn.commit()

    def delete_clip(self, clip_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM clips WHERE id = ?", (clip_id,))
            conn.commit()

    # --- Upload Queue Operations ---
    def enqueue_post(self, clip_id, platform, scheduled_time):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO upload_queue (clip_id, platform, scheduled_time, status) VALUES (?, ?, ?, 'queued')",
                (clip_id, platform, scheduled_time)
            )
            conn.commit()
            return cursor.lastrowid

    def get_queued_posts(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT q.*, c.title as clip_title, c.export_path, c.description, c.tags 
                FROM upload_queue q
                JOIN clips c ON q.clip_id = c.id
                ORDER BY q.scheduled_time ASC
            """)
            return [dict(row) for row in cursor.fetchall()]

    def update_post_status(self, post_id, status, error_message=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if error_message:
                cursor.execute("""
                    UPDATE upload_queue 
                    SET status = ?, error_message = ?, retry_count = retry_count + 1, updated_at = CURRENT_TIMESTAMP 
                    WHERE id = ?
                """, (status, error_message, post_id))
            else:
                cursor.execute("""
                    UPDATE upload_queue 
                    SET status = ?, error_message = NULL, updated_at = CURRENT_TIMESTAMP 
                    WHERE id = ?
                """, (status, post_id))
            conn.commit()

    def delete_queued_post(self, post_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM upload_queue WHERE id = ?", (post_id,))
            conn.commit()

    # --- Analytics Operations ---
    def add_analytics_record(self, clip_id, platform, views, watch_time, likes, retention_rate, ctr):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO analytics (clip_id, platform, views, watch_time, likes, retention_rate, ctr)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (clip_id, platform, views, watch_time, likes, retention_rate, ctr)
            )
            conn.commit()
            return cursor.lastrowid

    def get_analytics_for_clip(self, clip_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM analytics WHERE clip_id = ? ORDER BY snapshot_date ASC", (clip_id,))
            return [dict(row) for row in cursor.fetchall()]

    def get_aggregated_analytics(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT platform, SUM(views) as total_views, SUM(likes) as total_likes, 
                       AVG(retention_rate) as avg_retention, AVG(ctr) as avg_ctr
                FROM analytics
                GROUP BY platform
            """)
            return [dict(row) for row in cursor.fetchall()]
