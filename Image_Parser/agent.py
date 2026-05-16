import os

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from .tools import extract_text_from_image

model=os.getenv('ORC_MODEL')

litellm_model = LiteLlm(
    model=f'openrouter/{model}',
    api_key=os.getenv('OPENROUTER_API_KEY', 'DEFAULT'),
    api_base='https://openrouter.ai/api/v1'
)

agent = Agent(
    name='image_parsing_agent',
    model=litellm_model,
    instruction=(
        'You are a image parsing agent. Use the extract_text_from_image tool to extract '
        'raw text from image-based invoice files (jpg, jpeg, png, tiff). '
        'The tool uses a vision language model to read the document contents.'
    ),
    description='Extracts text from image-based invoice documents using a vision model.',
    tools=[extract_text_from_image],
)