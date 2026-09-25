"""
storage.py
----------
Lightweight persistence layer using SQLite. No external DB server needed,
which keeps setup trivial for a college project (and for your viva demo).

Embeddings are stored as raw float32 bytes (BLOB) and reconstructed with
numpy on read -- simplest possible "vector store" without pulling in a
dedicated vector DB.
"""
import sqlite3
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).parent.parent / "data" / "templates.db"


def _connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = _connect()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            filename TEXT NOT NULL,
            extracted_text TEXT NOT NULL,
            embedding BLOB NOT NULL,
            embedding_dim INTEGER NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def add_template(name: str, category: Optional[str], filename: str,
                  extracted_text: str, embedding: np.ndarray) -> int:
    conn = _connect()
    cur = conn.execute(
        """INSERT INTO templates
           (name, category, filename, extracted_text, embedding, embedding_dim, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            name,
            category,
            filename,
            extracted_text,
            embedding.astype(np.float32).tobytes(),
            embedding.shape[0],
            datetime.utcnow().isoformat(),
        ),
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


def get_all_templates() -> list[dict]:
    conn = _connect()
    rows = conn.execute("SELECT * FROM templates ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_template(template_id: int) -> Optional[dict]:
    conn = _connect()
    row = conn.execute("SELECT * FROM templates WHERE id = ?", (template_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_template(template_id: int) -> bool:
    conn = _connect()
    cur = conn.execute("DELETE FROM templates WHERE id = ?", (template_id,))
    conn.commit()
    deleted = cur.rowcount > 0
    conn.close()
    return deleted


def row_to_embedding(row: dict) -> np.ndarray:
    return np.frombuffer(row["embedding"], dtype=np.float32).reshape(row["embedding_dim"])
