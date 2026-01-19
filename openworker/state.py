import sqlite3
import os
from datetime import datetime
from typing import List

class StateDB:
    def __init__(self, db_path: str = "./.store/openworker.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS folders (
                path TEXT PRIMARY KEY,
                added_at TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

    def add_folder(self, path: str):
        path = os.path.abspath(path)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT OR IGNORE INTO folders (path, added_at) VALUES (?, ?)', 
                           (path, datetime.now()))
            conn.commit()
        finally:
            conn.close()

    def remove_folder(self, path: str):
        path = os.path.abspath(path)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute('DELETE FROM folders WHERE path = ?', (path,))
            conn.commit()
        finally:
            conn.close()

    def list_folders(self) -> List[str]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT path FROM folders')
            rows = cursor.fetchall()
            return [r[0] for r in rows]
        finally:
            conn.close()

# Singleton
_db = None
def get_db():
    global _db
    if _db is None:
        _db = StateDB()
    return _db
