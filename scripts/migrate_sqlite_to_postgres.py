from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import sqlite3

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app import normalize_database_url
from app.persistence import Base, HistoryEntry, User


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Migra usuarios e historial desde SQLite hacia PostgreSQL.",
    )
    parser.add_argument(
        "--sqlite-path",
        default="instance/bnf_validator.sqlite3",
        help="Ruta al archivo SQLite origen.",
    )
    parser.add_argument(
        "--database-url",
        required=True,
        help="Cadena de conexion destino para PostgreSQL.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    sqlite_path = Path(args.sqlite_path)
    if not sqlite_path.exists():
        raise FileNotFoundError(f"No se encontro la base SQLite en: {sqlite_path}")

    destination_url = normalize_database_url(args.database_url)
    engine = create_engine(destination_url, future=True, pool_pre_ping=True)
    Base.metadata.create_all(engine)

    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row

    migrated_users = 0
    migrated_entries = 0

    with Session(engine) as session:
        user_id_map: dict[int, int] = {}

        for row in sqlite_conn.execute("SELECT id, username, password_hash, created_at FROM users ORDER BY id"):
            existing_user = session.execute(
                select(User).where(User.username == row["username"])
            ).scalar_one_or_none()

            if existing_user is None:
                user = User(
                    username=row["username"],
                    password_hash=row["password_hash"],
                    created_at=parse_timestamp(row["created_at"]),
                )
                session.add(user)
                session.flush()
                migrated_users += 1
            else:
                user = existing_user

            user_id_map[row["id"]] = user.id

        for row in sqlite_conn.execute(
            """
            SELECT id, user_id, label, grammar, inputs, start_symbol, derivation_mode, created_at
            FROM history_entries
            ORDER BY id
            """
        ):
            target_user_id = user_id_map[row["user_id"]]
            existing_entry = session.execute(
                select(HistoryEntry).where(
                    HistoryEntry.user_id == target_user_id,
                    HistoryEntry.label == row["label"],
                    HistoryEntry.grammar == row["grammar"],
                    HistoryEntry.inputs == row["inputs"],
                    HistoryEntry.created_at == parse_timestamp(row["created_at"]),
                )
            ).scalar_one_or_none()

            if existing_entry is not None:
                continue

            entry = HistoryEntry(
                user_id=target_user_id,
                label=row["label"],
                grammar=row["grammar"],
                inputs=row["inputs"],
                start_symbol=row["start_symbol"],
                derivation_mode=row["derivation_mode"],
                created_at=parse_timestamp(row["created_at"]),
            )
            session.add(entry)
            migrated_entries += 1

        session.commit()

    sqlite_conn.close()

    print(f"Usuarios migrados: {migrated_users}")
    print(f"Entradas de historial migradas: {migrated_entries}")


def parse_timestamp(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


if __name__ == "__main__":
    main()
