from __future__ import annotations

import sqlite3
from typing import Any

from flask import current_app, g
from werkzeug.security import check_password_hash, generate_password_hash


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS history_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    label TEXT NOT NULL,
    grammar TEXT NOT NULL,
    inputs TEXT NOT NULL,
    start_symbol TEXT,
    derivation_mode TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);
"""


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db() -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(app) -> None:
    with app.app_context():
        db = get_db()
        db.executescript(SCHEMA)
        db.commit()


def get_user_by_id(_app, user_id: int) -> dict[str, Any] | None:
    row = get_db().execute(
        "SELECT id, username, created_at FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()
    return dict(row) if row else None


def get_user_by_username(username: str) -> sqlite3.Row | None:
    return get_db().execute(
        "SELECT id, username, password_hash, created_at FROM users WHERE username = ?",
        (username.lower(),),
    ).fetchone()


def create_user(username: str, password: str) -> dict[str, Any]:
    normalized = username.strip().lower()
    db = get_db()
    cursor = db.execute(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
        (normalized, generate_password_hash(password)),
    )
    db.commit()
    return {
        "id": cursor.lastrowid,
        "username": normalized,
    }


def authenticate_user(username: str, password: str) -> dict[str, Any] | None:
    row = get_user_by_username(username.strip().lower())
    if row is None or not check_password_hash(row["password_hash"], password):
        return None
    return {
        "id": row["id"],
        "username": row["username"],
        "created_at": row["created_at"],
    }


def create_history_entry(
    user_id: int,
    label: str,
    grammar: str,
    inputs: str,
    start_symbol: str | None,
    derivation_mode: str,
) -> dict[str, Any]:
    db = get_db()
    cursor = db.execute(
        """
        INSERT INTO history_entries (user_id, label, grammar, inputs, start_symbol, derivation_mode)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (user_id, label, grammar, inputs, start_symbol, derivation_mode),
    )
    db.commit()
    row = db.execute(
        """
        SELECT id, label, grammar, inputs, start_symbol, derivation_mode, created_at
        FROM history_entries
        WHERE id = ?
        """,
        (cursor.lastrowid,),
    ).fetchone()
    return dict(row)


def list_history_entries(user_id: int) -> list[dict[str, Any]]:
    rows = get_db().execute(
        """
        SELECT id, label, grammar, inputs, start_symbol, derivation_mode, created_at
        FROM history_entries
        WHERE user_id = ?
        ORDER BY datetime(created_at) DESC, id DESC
        """,
        (user_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def delete_history_entry(user_id: int, entry_id: int) -> bool:
    db = get_db()
    cursor = db.execute(
        "DELETE FROM history_entries WHERE id = ? AND user_id = ?",
        (entry_id, user_id),
    )
    db.commit()
    return cursor.rowcount > 0
