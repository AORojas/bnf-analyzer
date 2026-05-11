from __future__ import annotations

from datetime import datetime
from typing import Any

from flask import current_app, g
from sqlalchemy import DateTime, ForeignKey, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship
from werkzeug.security import check_password_hash, generate_password_hash


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    history_entries: Mapped[list["HistoryEntry"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class HistoryEntry(Base):
    __tablename__ = "history_entries"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    label: Mapped[str] = mapped_column(String(120), nullable=False)
    grammar: Mapped[str] = mapped_column(Text, nullable=False)
    inputs: Mapped[str] = mapped_column(Text, nullable=False)
    start_symbol: Mapped[str | None] = mapped_column(String(120))
    derivation_mode: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped[User] = relationship(back_populates="history_entries")


def init_db(app) -> None:
    engine = create_engine(
        app.config["DATABASE_URL"],
        future=True,
        pool_pre_ping=True,
    )
    app.extensions["db_engine"] = engine
    with app.app_context():
        Base.metadata.create_all(engine)


def get_db() -> Session:
    if "db" not in g:
        engine = current_app.extensions["db_engine"]
        g.db = Session(engine)
    return g.db


def close_db() -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def get_user_by_id(_app, user_id: int) -> dict[str, Any] | None:
    user = get_db().get(User, user_id)
    return serialize_user(user) if user else None


def get_user_by_username(username: str) -> User | None:
    normalized = username.strip().lower()
    stmt = select(User).where(User.username == normalized)
    return get_db().execute(stmt).scalar_one_or_none()


def create_user(username: str, password: str) -> dict[str, Any]:
    normalized = username.strip().lower()
    user = User(
        username=normalized,
        password_hash=generate_password_hash(password),
        created_at=local_timestamp(),
    )
    db = get_db()
    db.add(user)
    db.commit()
    db.refresh(user)
    return serialize_user(user)


def authenticate_user(username: str, password: str) -> dict[str, Any] | None:
    user = get_user_by_username(username)
    if user is None or not check_password_hash(user.password_hash, password):
        return None
    return serialize_user(user)


def create_history_entry(
    user_id: int,
    label: str,
    grammar: str,
    inputs: str,
    start_symbol: str | None,
    derivation_mode: str,
) -> dict[str, Any]:
    entry = HistoryEntry(
        user_id=user_id,
        label=label,
        grammar=grammar,
        inputs=inputs,
        start_symbol=start_symbol,
        derivation_mode=derivation_mode,
        created_at=local_timestamp(),
    )
    db = get_db()
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return serialize_history_entry(entry)


def list_history_entries(user_id: int) -> list[dict[str, Any]]:
    stmt = (
        select(HistoryEntry)
        .where(HistoryEntry.user_id == user_id)
        .order_by(HistoryEntry.created_at.desc(), HistoryEntry.id.desc())
    )
    rows = get_db().execute(stmt).scalars().all()
    return [serialize_history_entry(row) for row in rows]


def delete_history_entry(user_id: int, entry_id: int) -> bool:
    db = get_db()
    entry = db.get(HistoryEntry, entry_id)
    if entry is None or entry.user_id != user_id:
        return False
    db.delete(entry)
    db.commit()
    return True


def local_timestamp() -> datetime:
    return datetime.now().astimezone()


def serialize_user(user: User) -> dict[str, Any]:
    return {
        "id": user.id,
        "username": user.username,
        "created_at": user.created_at.isoformat(timespec="seconds"),
    }


def serialize_history_entry(entry: HistoryEntry) -> dict[str, Any]:
    return {
        "id": entry.id,
        "label": entry.label,
        "grammar": entry.grammar,
        "inputs": entry.inputs,
        "start_symbol": entry.start_symbol,
        "derivation_mode": entry.derivation_mode,
        "created_at": entry.created_at.isoformat(timespec="seconds"),
    }
