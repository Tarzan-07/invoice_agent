import os

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

litellm_model = LiteLlm(
    model='openrouter/openai/gpt-4o',
    api_key=os.getenv('OPENROUTER_API_KEY', 'DEFAULT'),
    api_base='https://openrouter.ai/api/v1'
)

agent = Agent(
    name='image_parsing_agent',
    model=litellm_model,
    instruction='You are a image parsing agent.',
    description='Classifies uploaded invoice documents',
)