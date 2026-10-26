"""SQLite storage for expenses and budgets."""

from __future__ import annotations

import datetime as dt
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pandas as pd

DB_PATH = Path(__file__).resolve().parent.parent / "expenses.db"

DEFAULT_CATEGORIES = [
    "Food",
    "Housing",
    "Transport",
    "Health",
    "Entertainment",
    "Shopping",
    "Bills",
    "Other",
]

_SCHEMA = """
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY,
    date TEXT NOT NULL,
    amount REAL NOT NULL CHECK (amount > 0),
    category TEXT NOT NULL,
    note TEXT
);
CREATE TABLE IF NOT EXISTS budgets (
    category TEXT PRIMARY KEY,
    monthly_limit REAL NOT NULL CHECK (monthly_limit > 0)
);
"""


@contextmanager
def connect(db_path: Path | str = DB_PATH) -> Iterator[sqlite3.Connection]:
    """Open a connection that commits on success, rolls back on error and always closes."""
    conn = sqlite3.connect(db_path)
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def init_db(db_path: Path | str = DB_PATH) -> None:
    """Create the tables if they do not exist yet."""
    with connect(db_path) as conn:
        conn.executescript(_SCHEMA)


def add_expense(
    date: str,
    amount: float,
    category: str,
    note: str = "",
    db_path: Path | str = DB_PATH,
) -> int:
    """Insert an expense and return its id. Raises ValueError on invalid input."""
    date = dt.date.fromisoformat(date).isoformat()  # normalise so month filtering by prefix works
    if not amount > 0:
        raise ValueError("Amount must be greater than zero.")
    category = category.strip()
    if not category:
        raise ValueError("Category is required.")
    with connect(db_path) as conn:
        cur = conn.execute(
            "INSERT INTO expenses (date, amount, category, note) VALUES (?, ?, ?, ?)",
            (date, float(amount), category, note.strip() or None),
        )
        return cur.lastrowid


def get_expenses(db_path: Path | str = DB_PATH) -> pd.DataFrame:
    """Return all expenses, newest first, with columns id, date, amount, category, note."""
    with connect(db_path) as conn:
        return pd.read_sql_query(
            "SELECT id, date, amount, category, note FROM expenses ORDER BY date DESC, id DESC",
            conn,
        )


def delete_expense(expense_id: int, db_path: Path | str = DB_PATH) -> bool:
    """Delete an expense by id. Returns True if a row was removed."""
    with connect(db_path) as conn:
        return conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,)).rowcount > 0


def set_budget(category: str, monthly_limit: float, db_path: Path | str = DB_PATH) -> None:
    """Create or update the monthly limit for a category."""
    if not monthly_limit > 0:
        raise ValueError("Monthly limit must be greater than zero.")
    with connect(db_path) as conn:
        conn.execute(
            "INSERT INTO budgets (category, monthly_limit) VALUES (?, ?) "
            "ON CONFLICT(category) DO UPDATE SET monthly_limit = excluded.monthly_limit",
            (category, float(monthly_limit)),
        )


def get_budgets(db_path: Path | str = DB_PATH) -> pd.DataFrame:
    """Return all budgets with columns category, monthly_limit."""
    with connect(db_path) as conn:
        return pd.read_sql_query(
            "SELECT category, monthly_limit FROM budgets ORDER BY category", conn
        )


def get_categories(db_path: Path | str = DB_PATH) -> list[str]:
    """Return the default categories followed by any custom ones already in use."""
    with connect(db_path) as conn:
        rows = conn.execute(
            "SELECT category FROM expenses UNION SELECT category FROM budgets"
        ).fetchall()
    custom = sorted({r[0] for r in rows} - set(DEFAULT_CATEGORIES))
    return DEFAULT_CATEGORIES + custom
