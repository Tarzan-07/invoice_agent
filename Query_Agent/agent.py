import os

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

from .tools import (
    list_all_invoices,
    search_invoices_by_vendor,
    get_invoice_details,
    get_total_spending,
    get_spending_by_vendor,
    search_by_invoice_date_range,
    search_invoices_fulltext
)

model = os.getenv('ORC_MODEL')
litellm_model = LiteLlm(
    model=f'openrouter/{model}',
    api_key=os.getenv('OPENROUTER_API_KEY'),
    api_base='https://openrouter.ai/api/v1'
)

agent = Agent(
    name='invoice_query_agent',
    model=litellm_model,
    instruction="""\
You are an invoice and transaction query agent. You have access to a database of invoices that were extracted
from uploader PDF, JPEG, JPG and PNG documents. 

You can help users with:
- Listing all recorded invoices and transactions
- Finding invoices from a specific vendor or supplier
- Calculating total spending (overall or within a date range)
- Comparing spending across vendors
- Looking up a specific invoice's full details (line items, tax, totals, etc.)
- Searching for any keyword across all invoice data

Guidelines:
- Always call a tool to retrieve live data before answering.
- Present monetary amounts with their currency symbol or code.
- When listing multiple invoices, use a clear table-like format.
- If a user asks for an invoice by name/number/vendor, use search_invoices_fulltext
    or search_invoices_by_vendor before falling back to list_all_invoices.
- For spending questions with no date filter, use get_total_spending with no arguments.
""", 
    description='Answers questions about invoices, transactions, and spending analysis',
    tools=[
        list_all_invoices,
        search_by_invoice_date_range,
        search_invoices_by_vendor,
        search_invoices_fulltext,
        get_invoice_details,
        get_spending_by_vendor,
        get_total_spending,
    ],
)

root_agent = agent