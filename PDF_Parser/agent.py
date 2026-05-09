import os

from google.adk.models.lite_llm import LiteLlm
from google.adk.agents import Agent

from .tools import extract_text_from_pdf

litellm_model = LiteLlm(
    model='openrouter/openai/gpt-4o',
    api_key=os.getenv('OPENROUTER_API_KEY'),
    api_base='https://openrouter.ai/api/v1'
)

agent = Agent(
    name='pdf_parsing_agent',
    model=litellm_model,
    instruction=(
        'You are a PDF parsing agent. Use the extract_text_from_pdf tool to extract',
        'raw text from PDF invoice files. The tool automatically detects whether the ',
        'PDF is digital or scanned and applies OCR when needed.'
    ),
    description='Extracts text from PDF invoices, supporting both digital and scanned PDFs.',
    tools=[extract_text_from_pdf],
)