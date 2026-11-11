"""SQLite3 connection management with WAL mode and schema DDL."""
import sqlite3
from contextlib import contextmanager
from typing import Generator, Optional

from app.config import get_settings

SCHEMA_SQL = """
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS searches (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL,
  query TEXT NOT NULL,
  params_json TEXT,
  result_count INTEGER,
  latency_ms INTEGER,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS product_snapshots (
  id TEXT PRIMARY KEY,
  search_id TEXT NOT NULL REFERENCES searches(id),
  channel3_id TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT,
  key_features_json TEXT,
  materials_json TEXT,
  image_url TEXT,
  merchant_domain TEXT,
  price TEXT NOT NULL,
  currency TEXT NOT NULL,
  availability TEXT,
  buy_url TEXT,
  raw_json TEXT NOT NULL,
  fetched_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS quotes (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL,
  snapshot_id TEXT NOT NULL REFERENCES product_snapshots(id),
  quantity INTEGER NOT NULL,
  unit_price TEXT NOT NULL,
  currency TEXT NOT NULL,
  total TEXT NOT NULL,
  budget TEXT,
  status TEXT NOT NULL,
  confirmed_at TEXT,
  expires_at TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL,
  quote_id TEXT NOT NULL REFERENCES quotes(id),
  paypal_order_id TEXT,
  status TEXT NOT NULL,
  capture_id TEXT,
  captured_amount TEXT,
  captured_currency TEXT,
  message TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS payment_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  order_id TEXT NOT NULL,
  step TEXT NOT NULL,
  http_status INTEGER,
  paypal_debug_id TEXT,
  summary TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS grounding_runs (
  id TEXT PRIMARY KEY,
  search_id TEXT NOT NULL REFERENCES searches(id),
  session_id TEXT NOT NULL,
  kept_count INTEGER NOT NULL,
  removed_count INTEGER NOT NULL,
  created_at TEXT NOT NULL
);
"""


def init_db(db_path: Optional[str] = None) -> None:
    """Initialize SQLite database with WAL mode and target DDL."""
    path = db_path or get_settings().DATABASE_PATH
    conn = sqlite3.connect(path)
    try:
        conn.executescript(SCHEMA_SQL)
        conn.commit()
    finally:
        conn.close()


@contextmanager
def get_db(db_path: Optional[str] = None) -> Generator[sqlite3.Connection, None, None]:
    """Yield a connection configured with sqlite3.Row and foreign keys."""
    path = db_path or get_settings().DATABASE_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


get_db_connection = get_db
