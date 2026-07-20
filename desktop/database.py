"""SQLite database for paper history and wordbook."""
import csv
import io
import os
import sqlite3
import time
from datetime import datetime, timezone, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), 'data.db')
CST = timezone(timedelta(hours=8))


def _now():
    return datetime.now(CST).strftime('%Y-%m-%d %H:%M')


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init():
    with get_db() as db:
        db.execute('''CREATE TABLE IF NOT EXISTS papers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filepath TEXT NOT NULL,
            filename TEXT NOT NULL,
            extracted_text TEXT DEFAULT '',
            analysis TEXT DEFAULT '',
            created_at TEXT DEFAULT ''
        )''')
        db.execute('''CREATE TABLE IF NOT EXISTS vocabulary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paper_id INTEGER,
            word TEXT NOT NULL,
            meaning TEXT DEFAULT '',
            created_at TEXT DEFAULT '',
            FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE
        )''')
        db.commit()


# ---- Papers ----
def add_paper(filepath, filename, extracted_text, analysis):
    with get_db() as db:
        cur = db.execute(
            "INSERT INTO papers (filepath, filename, extracted_text, analysis, created_at) VALUES (?,?,?,?,?)",
            (filepath, filename, extracted_text, analysis, _now())
        )
        return cur.lastrowid


def get_papers(limit=50):
    with get_db() as db:
        return [dict(r) for r in db.execute(
            "SELECT id, filename, created_at FROM papers ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()]


def get_paper(paper_id):
    with get_db() as db:
        return dict(db.execute("SELECT * FROM papers WHERE id=?", (paper_id,)).fetchone() or {})


def delete_paper(paper_id):
    with get_db() as db:
        db.execute("DELETE FROM papers WHERE id=?", (paper_id,))
        db.commit()


# ---- Vocabulary ----
def add_vocabulary(paper_id, word, meaning):
    with get_db() as db:
        existing = db.execute(
            "SELECT id FROM vocabulary WHERE paper_id=? AND word=? COLLATE NOCASE",
            (paper_id, word)
        ).fetchone()
        if existing:
            db.execute("UPDATE vocabulary SET meaning=?, created_at=? WHERE id=?",
                       (meaning, _now(), existing['id']))
        else:
            db.execute(
                "INSERT INTO vocabulary (paper_id, word, meaning, created_at) VALUES (?,?,?,?)",
                (paper_id, word, meaning, _now())
            )
        db.commit()


def get_vocabulary(paper_id=None):
    with get_db() as db:
        if paper_id:
            rows = db.execute(
                "SELECT * FROM vocabulary WHERE paper_id=? ORDER BY created_at DESC", (paper_id,)
            ).fetchall()
        else:
            rows = db.execute(
                "SELECT * FROM vocabulary ORDER BY created_at DESC LIMIT 500"
            ).fetchall()
        return [dict(r) for r in rows]


def delete_vocabulary(vocab_id):
    with get_db() as db:
        db.execute("DELETE FROM vocabulary WHERE id=?", (vocab_id,))
        db.commit()


def export_csv(paper_id=None):
    vocab = get_vocabulary(paper_id)
    output = io.StringIO()
    output.write('﻿')
    w = csv.writer(output)
    w.writerow(['单词', '含义', '添加时间'])
    for v in vocab:
        w.writerow([v['word'], v['meaning'], v['created_at']])
    return output.getvalue()
