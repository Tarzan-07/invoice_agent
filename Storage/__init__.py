"""
Storage/db.py

SQLite persistence layer for extracted invoice data.
"""

import json
import logging
from pathlib import Path
import sqlite3
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
DB_PATH = Path(__file__).parent.parent / 'data' / 'invoices.db'

def _connect()->sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db()->None:
    conn = _connect()
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_path TEXT UNIQUE,
        vendor_name TEXT,
        vendor_address TEXT,
        invoice_date TEXT,
        due_date TEXT,
        bill_to_name TEXT,
        bill_to_address TEXT,
        subtotal REAL,
        tax REAL,
        tax_rate REAL,
        total REAL,
        currency TEXT,
        payment_terms TEXT,
        notes TEXT,
        raw_text TEXT,
        extracted_json TEXT,
        created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS line_items (
        id PRIMARY KEY AUTOINCREMENT,
        invoice_id INTEGER NOT NULL REFERENCES invoices(id),
        description TEXT,
        quantity REAL,
        unit_price REAL,
        total REAL
        );
        """
    )
    conn.commit()
    conn.close()

def store_invoice(file_path: str, invoice_data: dict, raw_text: str)->int:
    init_db()
    conn = _connect()
    cur = conn.cursor()

    # sql_query = """"""

    try:
        cur.execute(
            """
            INSERT INTO invoices (
            file_path, vendor_name, vendor_address, invoice_date, due_date, 
            bill_to_name, bill_to_address, subtotal, tax, tax_rate, total, 
            currency, payment_terms, notes, raw_text, extracted_json, created_at
            ) VALUES (
            :file_path, :vendor_name, :vendor_address, :invoice_date, :due_date, 
            :bill_to_name, :bill_to_address, :subtotal, :tax, :tax_rate, :total, 
            :currency, :payment_terms, :notes, :raw_text, :extracted_json, :created_at
            )
            ON CONFLICT(file_path) DO UPDATE SET
            vendor_name = excluded.vendor_name, 
            vendor_address = excluded.vendor_address, 
            invoice_date = excluded.invoice_date, 
            due_date = excluded.due_date, 
            bill_to_name = excluded.bill_to_name, 
            bill_to_address = excluded.bill_to_address, 
            subtotal = excluded.subtotal, 
            tax = excluded.tax, 
            tax_rate = excluded.tax_rate, 
            total = excluded.total, 
            currency = excluded.currency, 
            payment_terms = excluded.payment_terms, 
            notes = excluded.notes, 
            raw_text = excluded.raw_text, 
            extracted_json = excluded.extracted_json, 
            created_at = excluded.created_at
            """,
            {
                'file_path': file_path,
                'vendor_name': invoice_data.get('vendor_name'), 
                'vendor_address': invoice_data.get('vendor_address'),
                'invoice_date': invoice_data.get('invoice_date'),
                'due_date': invoice_data.get('due_date'),
                'bill_to_name': invoice_data.get('bill_to_name'),
                'bill_to_address': invoice_data.get('bill_to_address'), 
                'subtotal': invoice_data.get('subtotal'),
                'tax': invoice_data.get('tax'),
                'tax_rate': invoice_data.get('tax_rate'), 
                'total': invoice_data.get('total'), 
                'currency': invoice_data.get('currency'), 
                'payment_terms': invoice_data.get('payment_terms'), 
                'notes': invoice_data.get('notes'), 
                'raw_text': invoice_data.get('raw_text'), 
                'extracted_json': json.dumps(invoice_data), 
                'created_at': datetime.now(timezone.utc).isoformat(),
            },
        )

        invoice_id = cur.execute(
            "SELECT id FROM invoices WHERE file_path = ?", (file_path)
        ).fetchone()['id']

        cur.execute("DELETE FROM line_items WHERE invoice_id = ?", (invoice_id,))
        for item in invoice_data.get('line_items') or []:
            if isinstance(item, dict):
                cur.execute(
                    """
                    INSERT INTO line_items (invoice_id, description, quantity, unit_price, total)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    {
                        invoice_id,
                        item.get('description'),
                        item.get('quantity'),
                        item.get('unit_price'),
                        item.get('total'),
                    },
                )

        conn.commit()
        logger.info('Stored invoice id=%d from %s', invoice_id, file_path)
        return invoice_id

    except Exception as e:
        return e
    
    finally:
        conn.close()
        