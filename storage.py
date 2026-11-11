"""Local SQLite persistence for the single-user portfolio."""
from __future__ import annotations

import sqlite3
from pathlib import Path
import pandas as pd
from portfolio import COLUMNS, default_portfolio

DB_PATH = Path(__file__).resolve().parent / "portfolio.db"

def _connect(db_path: str | Path = DB_PATH):
    connection = sqlite3.connect(str(db_path))
    connection.execute("""
        CREATE TABLE IF NOT EXISTS holdings (
            ticker TEXT PRIMARY KEY, name TEXT NOT NULL, asset_type TEXT NOT NULL,
            quantity REAL NOT NULL, average_cost REAL, target_weight_pct REAL NOT NULL
        )
    """)
    connection.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY, value REAL NOT NULL
        )
    """)
    return connection

def load_portfolio(db_path: str | Path = DB_PATH):
    with _connect(db_path) as connection:
        rows = connection.execute(
            "SELECT ticker, name, asset_type, quantity, average_cost, target_weight_pct FROM holdings ORDER BY rowid"
        ).fetchall()
        cash_row = connection.execute("SELECT value FROM settings WHERE key='cash_usd'").fetchone()
    if not rows:
        return default_portfolio(), 0.0
    return pd.DataFrame(rows, columns=COLUMNS), float(cash_row[0]) if cash_row else 0.0

def save_portfolio(holdings: pd.DataFrame, cash_usd: float, db_path: str | Path = DB_PATH):
    with _connect(db_path) as connection:
        connection.execute("DELETE FROM holdings")
        connection.executemany(
            """INSERT INTO holdings
            (ticker, name, asset_type, quantity, average_cost, target_weight_pct)
            VALUES (?, ?, ?, ?, ?, ?)""",
            [
                (str(row.ticker).strip().upper(), str(row.name), str(row.asset_type),
                 float(row.quantity), None if pd.isna(row.average_cost) else float(row.average_cost),
                 float(row.target_weight_pct))
                for row in holdings.itertuples(index=False)
            ],
        )
        connection.execute(
            "INSERT INTO settings(key, value) VALUES('cash_usd', ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (float(cash_usd),),
        )
