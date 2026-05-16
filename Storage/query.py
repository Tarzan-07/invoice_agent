"""
Storage/query.py
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / 'data' / 'invoices.db'

def _connect()->sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_all_invoices()->list:
    conn = _connect()
    rows = conn.execute(
        """
        SELECT id, vendor_name, vendor_address, invoice_number, invoice_date, 
            due_date, total, currency, file_path
        FROM invoices
        ORDER BY invoice_date DESC
        """
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def search_invoices_by_vendor(vendor_name: str)->list:
    conn = _connect()
    rows = conn.execute(
        """
        SELECT id, vendor_name, invoice_number, invoice_date,
            due_date, total, currency, file_path
        FROM invoices
        WHERE vendor_name LIKE ?
        ORDER BY invoice_date DESC
        """,
        (f"%{vendor_name}%",),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_invoice_details(invoice_id: int)->dict:
    conn = _connect()
    row = conn.execute(
        "SELECT * FROM invoices where id = ?", (invoice_id,) 
    ).fetchone()
    if not row:
        conn.close()
        return {}
    
    invoice = dict(row)
    invoice.pop("raw_text", None)

    items = conn.execute(
        "SELECT description, quantity, unit_price, total FROM line_items WHERE invoice_id = ?", (invoice_id,)
    ).fetchall()
    invoice['line_items'] = [dict(i) for i in items]
    conn.close()
    return invoice

def get_total_spending(start_date: str=None, end_date: str=None)->dict:
    conn = _connect()
    if start_date and end_date:
        rows = conn.execute(
            """
            SELECT SUM(total) as total, COUNT(*) as count, currency
            FROM invoices
            WHERE invoice_date BETWEEN ? AND ?
            GROUP BY currency
            """,
            (start_date, end_date),
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT SUM(total) as total, COUNT(*) as count, currency
            FROM invoices
            GROUP BY currency
            """
        ).fetchall()
    conn.close()
    return {'totals':[dict(r) for r in rows]}

def get_spending_by_vendor()->list:
    conn = _connect()
    rows = conn.execute(
        """
        SELECT vendor_name, SUM(total) AS total_spent, COUNT(*) AS invoice_count, currency
        FROM invoices
        GROUP BY vendor_name, currency
        ORDER BY invoice_date DESC
        """
    )
    return [dict(r) for r in rows]

def search_by_invoice_date_range(start_date: str, end_date: str)->list:
    conn = _connect()
    rows = conn.execute(
        """
        SELECT id, vendor_name, vendor_address, invoice_number, invoice_date, total, currency
        FROM invoices
        WHERE invoice_date BETWEEN ? AND ?
        ORDER BY invoice_date DESC
        """,(start_date, end_date),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def search_invoices_fulltext(query: str)->list:
    conn = _connect()
    q = f"%{query}%"

    rows = conn.execute(
        """
        SELECT id, vendor_name, invoice_number, invoice_date, total, currency
        FROM invoices
        WHERE vendor_name LIKE ?
        OR invoice_number LIKE ?
        OR bill_to_name LIKE ?
        OR notes LIKE ?
        OR raw_text LIKE ?
        ORDER BY invoice_date DESC
        """, (q, q, q, q, q),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
