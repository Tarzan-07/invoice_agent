"""
A simply agent that can process invoice details
"""

import os
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
import logging

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from .tools import classify_document

logger = logging.getLogger(__name__)
model = os.getenv('ORC_MODEL')
litellm_model = LiteLlm(
    model=f'openrouter/{model}',
    api_key=os.getenv('OPENROUTER_API_KEY', 'DEFAULT'),
    api_base='https://openrouter.ai/api/v1'
)

agent = Agent(
    name='document_classification_agent',
    model=litellm_model,
    instruction=(
        'You are a document classification agent. Use the classify_document tool '
        'to determine whether a file is a PDF ot image, and whether it is a digital or scanned.'
    ),
    description='Classifies uploaded invoice documents by type (PDF.image, digital/scanned).',
    tools=[classify_document]
)