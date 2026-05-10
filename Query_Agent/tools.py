"""
Query_Agent/tools.py
"""

from Storage.query import (
    get_all_invoices as _all,
    search_invoices_by_vendor as _by_vendor,
    get_invoice_details as _details,
    get_total_spending as _total_spending,
    get_spending_by_vendor as _by_vendor_sum,
    search_by_invoice_date_range as _date_range,
    search_invoices_fulltext as _fulltext
)

def list_all_invoices()-> list:
    return _all()

def search_invoices_by_vendor(vendor_name: str):
    return _by_vendor(vendor_name)

def get_invoice_details(invoice_id: int):
    return _details(invoice_id)

def get_total_spending(start_date: str=None, end_date: str=None):
    return _total_spending(start_date, end_date)

def get_spending_by_vendor():
    return _by_vendor_sum

def search_by_invoice_date_range(start_date, end_date):
    return _date_range(start_date, end_date)

def search_invoices_fulltext(query):
    return _fulltext(query)