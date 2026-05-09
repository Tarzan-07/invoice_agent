"""
Storage/query.py
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / 'data' / 'invoices.db'

def _connect()->sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

