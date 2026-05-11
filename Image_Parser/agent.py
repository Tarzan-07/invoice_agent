import os

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from .tools import extract_text_from_image

litellm_model = LiteLlm(
    model='openrouter/nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free',
    api_key=os.getenv('OPENROUTER_API_KEY', 'DEFAULT'),
    api_base='https://openrouter.ai/api/v1'
)

agent = Agent(
    name='image_parsing_agent',
    model=litellm_model,
    instruction=(
        'You are a image OCR agent. Use the extract_text_from_image tool to extract',
        'raw text from image-based invoice files (jpg, jpeg, png, tiff)'
    ),
    description='Extracts text from image-based invoice documents using OCR.',
    tools=[extract_text_from_image],
)