import os

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from Query_Agent.agent import agent as query_agent
from Doc_Class_agent.agent import agent as doc_class_agent
from Image_Parser.agent import agent as image_parser_agent
from PDF_Parser.agent import agent as pdf_parser_agent
from .tools import store_parsed_invoice

litellm_model = LiteLlm(
    model='openrouter/nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free',
    api_key=os.getenv('OPENROUTER_API_KEY'),
    api_base='https://openrouter.ai/api/v1'
)

root_agent = Agent(
    name='invoice_orchestrator',
    model=litellm_model,
    instruction="""\
You are the central Invoice Assisstant. You co-ordinate specialized sub-agents to help users.

## Available sub-agents

1. **document_classification_agent** - classifies a file as PDF or image, digital or scanned. 
2. **image_parsing_agent** - extracts text from image invoices (JPG, PNG, TIFF) using a vision model. 
3. **pdf_parsing_agent** - extracts text from PDF invoices (handles both digital and scanned pages).
4. **invoice_query_agent** - answers questions about stored invoices, spending, vendors, etc.

## Available tools

- **store_parsed_invocies** - takes a file_path and the raw extracted text, parses it into
    structured invoice fields via an LLM, and stores it in the database. 

## Processing a new invoice (file path provided by the user)

Follow these steps in order:
1. Delegate to **document_classification_agent** to classify the file.
2. Based on the classification:
    - If it is an image -> delegate to **image_parsing_agent** to extract text.
    - If it is a PDF -> delegate to **pdf_parsing_agent** to extract text.
3. Once you have the extracted raw text, call the **store_parsed_invoice** tool
    with the file_path and raw_text.
4. Confirm to the user what was saved (vendor, invoice number, date, total, currency).

## Querying existing invoice data

If the user asks a question about their invoices, transactions, spending, vendors, 
or date ranges, delegate to **invoice_query_agents**.

## Routing rules
- Message contains a file path pr user wants to upload/add/process/import -> process the invoice.
- Message is a question or analysis request about existing data -> delegate to invoice_query_agent. 

Always be concise and strucutured in your responses.
""",
    description='Central invoice assisstant - processes new invoice files and answers questions about existing ones.',
    tools=[store_parsed_invoice],
    sub_agents=[query_agent, doc_class_agent, image_parser_agent, pdf_parser_agent],
)