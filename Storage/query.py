"""
Storage/query.py

Read-only query functions against the PostgreSQL (Supabase) database.
"""

import os
import psycopg2
import psycopg2.extras
from Storage.db import _connect

# DB_PATH = Path(__file__).parent.parent / 'data' / 'invoices.db'

# def _connect()->sqlite3.Connection:
#     DB_PATH.parent.mkdir(parents=True, exist_ok=True)
#     from Storage.db import init_db
#     init_db()
#     conn = sqlite3.connect(DB_PATH)
#     conn.row_factory = sqlite3.Row
#     return conn

# def _connect() -> psycopg2.extensions.connection:
#     from Storage.db import init_db
#     init_db()
#     # conn = psycopg2.connect()
# conn: psycopg2.extensions.connection = None
# cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

def get_cursor(conn: psycopg2.extensions.connection):
    return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

def get_all_invoices()->list:
    conn = _connect()
    # rows = conn.execute(
    cur = get_cursor(conn=conn)
    cur.execute(
        """
        SELECT id, vendor_name, vendor_address, invoice_number, invoice_date, 
            due_date, total, currency, file_path
        FROM invoices
        ORDER BY invoice_date DESC
        """
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in rows]

def search_invoices_by_vendor(vendor_name: str)->list:
    conn = _connect()
    cur = get_cursor(conn)
    rows = cur.execute(
        """
        SELECT id, vendor_name, invoice_number, invoice_date,
            due_date, total, currency, file_path
        FROM invoices
        WHERE vendor_name ILIKE %s
        ORDER BY invoice_date DESC
        """,
        (f"%{vendor_name}%",),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in rows]

def get_invoice_details(invoice_id: int)->dict:
    conn = _connect()
    cur = get_cursor(conn)
    cur.execute(
        "SELECT * FROM invoices where id = ?", (invoice_id,) 
    )
    row = cur.fetchone()
    if not row:
        cur.close()
        conn.close()
        return {}
    
    invoice = dict(row)
    invoice.pop("raw_text", None)

    cur.execute(
        "SELECT description, quantity, unit_price, total FROM line_items WHERE invoice_id = ?", (invoice_id,)
    )
    invoice['line_items'] = [dict(i) for i in cur.fetchall()]
    # invoice['line_items'] = [dict(i) for i in items]
    cur.close()
    conn.close()
    return invoice

def get_total_spending(start_date: str=None, end_date: str=None)->dict:
    conn = _connect()
    cur = get_cursor(conn)
    if start_date and end_date:
        cur.execute(
            """
            SELECT SUM(total) as total, COUNT(*) as count, currency
            FROM invoices
            WHERE invoice_date BETWEEN %s AND %s
            GROUP BY currency
            """,
            (start_date, end_date),
        )
    else:
        cur.execute(
            """
            SELECT SUM(total) as total, COUNT(*) as count, currency
            FROM invoices
            GROUP BY currency
            """
        )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return {'totals': [dict(r) for r in rows]}

def get_spending_by_vendor()->list:
    conn = _connect()
    cur = get_cursor(conn)
    cur.execute(
        """
        SELECT vendor_name, SUM(total) AS total_spent, COUNT(*) AS invoice_count, currency
        FROM invoices
        GROUP BY vendor_name, currency
        ORDER BY invoice_date DESC
        """
    )

    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in rows]

def search_by_invoice_date_range(start_date: str, end_date: str)->list:
    conn = _connect()
    cur = get_cursor(conn)
    rows = conn.execute(
        """
        SELECT id, vendor_name, vendor_address, invoice_number, invoice_date, total, currency
        FROM invoices
        WHERE invoice_date BETWEEN %s AND %s
        ORDER BY invoice_date DESC
        """,(start_date, end_date),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in rows]

def search_invoices_fulltext(query: str)->list:
    conn = _connect()
    cur = get_cursor(conn)
    q = f"%{query}%"

    cur.execute(
        """
        SELECT id, vendor_name, invoice_number, invoice_date, total, currency
        FROM invoices
        WHERE vendor_name ILIKE %s
        OR invoice_number ILIKE %s
        OR bill_to_name ILIKE %s
        OR notes ILIKE %s
        OR raw_text ILIKE %s
        ORDER BY invoice_date DESC
        """, (q, q, q, q, q),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in rows]
