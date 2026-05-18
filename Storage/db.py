"""
Storage/db.py

PostgreSQL persistence layer for extracted invoice data (via Supabase)
"""

import json
import logging
import os
import psycopg2
import psycopg2.extras
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
# DB_PATH = Path(__file__).parent.parent / 'data' / 'invoices.db'

def _connect()->psycopg2.extensions.connection:
    conn = psycopg2.connect(
        host = os.getenv('SUPABASE_DB_HOST'),
        port = int(os.getenv('SUPABASE_DB_PORT', '5432')),
        dbname = os.getenv('SUPABASE_DB_NAME', 'postgres'),
        user = os.getenv('SUPABASE_DB_USER', 'postgres'),
        password = os.getenv('SUPABASE_DB_PASSWORD'),
        sslmode = 'require',
    )
    return conn

def init_db() -> None:
    conn = _connect()
    cur = conn.cursor()
    cur.executes(
        """
        CREATE TABLE IF NOT EXISTS invoices (
        id SERIAL PRIMARY KEY AUTOINCREMENT,
        file_path TEXT UNIQUE,
        vendor_name TEXT,
        vendor_address TEXT,
        invoice_number TEXT,
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
        id SERIAL PRIMARY KEY AUTOINCREMENT,
        invoice_id INTEGER NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
        description TEXT,
        quantity REAL,
        unit_price REAL,
        total REAL
        );
        """
    )
    conn.commit()
    cur.close()
    conn.close()

def store_invoice(file_path: str, invoice_data: dict, raw_text: str) -> int:
    init_db()
    conn = _connect()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # sql_query = """"""

    try:
        cur.execute(
            """
            INSERT INTO invoices (
                file_path, vendor_name, vendor_address, invoice_number, invoice_date, due_date, 
                bill_to_name, bill_to_address, subtotal, tax, tax_rate, total, 
                currency, payment_terms, notes, raw_text, extracted_json, created_at
            ) VALUES (
                %(file_path)s, %(vendor_name)s, %(vendor_address)s, %(invoice_number)s, %(invoice_date)s, %(due_date)s, 
                %(bill_to_name)s, %(bill_to_address)s, %(subtotal)s, %(tax)s, %(tax_rate)s, %(total)s, 
                %(currency)s, %(payment_terms)s, %(notes)s, %(raw_text)s, %(extracted_json)s, %(created_at)s
            )
            ON CONFLICT (file_path) DO UPDATE SET
                vendor_name     = EXCLUDED.vendor_name, 
                vendor_address  = EXCLUDED.vendor_address, 
                invoice_number  = EXCLUDED.invoice_number,
                invoice_date    = EXCLUDED.invoice_date, 
                due_date        = EXCLUDED.due_date, 
                bill_to_name    = EXCLUDED.bill_to_name, 
                bill_to_address = EXCLUDED.bill_to_address, 
                subtotal        = EXCLUDED.subtotal, 
                tax             = EXCLUDED.tax, 
                tax_rate        = EXCLUDED.tax_rate, 
                total           = EXCLUDED.total, 
                currency        = EXCLUDED.currency, 
                payment_terms   = EXCLUDED.payment_terms, 
                notes           = EXCLUDED.notes, 
                raw_text        = EXCLUDED.raw_text, 
                extracted_json  = EXCLUDED.extracted_json, 
                created_at      = EXCLUDED.created_at
            RETURNING Id
            """,
            {
                'file_path': file_path,
                'vendor_name': invoice_data.get('vendor_name'), 
                'vendor_address': invoice_data.get('vendor_address'),
                'invoice_number': invoice_data.get('invoice_number'),
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
                'raw_text': raw_text,
                'extracted_json': json.dumps(invoice_data), 
                'created_at': datetime.now(timezone.utc).isoformat(),
            },
        )

        # invoice_id = cur.execute(
        #     "SELECT id FROM invoices WHERE file_path = ?", (file_path,)
        # ).fetchone()['id']

        invoice_id = cur.fetchone()['id']

        cur.execute("DELETE FROM line_items WHERE invoice_id = %s", (invoice_id,))
        for item in invoice_data.get('line_items') or []:
            if isinstance(item, dict):
                cur.execute(
                    """
                    INSERT INTO line_items (invoice_id, description, quantity, unit_price, total)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        invoice_id,
                        item.get('description'),
                        item.get('quantity'),
                        item.get('unit_price'),
                        item.get('total'),
                    ),
                )

        conn.commit()
        logger.info('Stored invoice id=%d from %s', invoice_id, file_path)
        return invoice_id

    except Exception as e:
        conn.rollback()
        logger.error('Failed to store invoice: %s', e)
    
    finally:
        cur.close()
        conn.close()
        