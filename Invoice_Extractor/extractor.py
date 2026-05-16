"""
Invoice_Extractor/extractor.py

Uses an LLM to parse raw invoice text into a structured JSON record.
"""

import os
import json
import logging

from google.adk.models.lite_llm import LiteLlm
import litellm

logger = logging.getLogger(__name__)

_EXTRACTION_PROMPT = """\
Extract structured invoice data from the text below.
Return ONLY a valid JSON object - no markdown, no explanation.

Required fields (use null when the information is absent):
    - vendor_name (string)
    - vendor_address (string)
    - invoice_number (string)
    - invoice_date (string, ISO 8601 preferred e.g. "2024-03-15")
    - due_date (string, ISO 8601 preferred)
    - bill_to_name (string)
    - bill_to_address (string)
    - line_items (array of object: {{description, quantity, unit_price, total}})
    - subtotal (number)
    - tax (number)
    - tax_rate (number, percentage e.g. 10 for 10%)
    - total (number)
    - currency (string, e.g. "USD")
    - payment_status (string, e.g. "Net 30")
    - notes (string)

All monetary values must be numbers, not strings. 

Invoice text:
{raw_text}
"""

def extract_invoice_data(raw_text: str)->dict:
    """
    Parse raw invoice text into structured fields using an LLM.

    Args:
        raw_text: Raw text extracted from an invoice document.

    Returns:
        dict of structured invoice fields, or a dict with an 'error' key on failure.
    """

    if not raw_text or not raw_text.strip():
        return {'error': 'No text provided for extraction'}
    
    prompt = _EXTRACTION_PROMPT.format(raw_text=raw_text[:4000])
    model = os.getenv('ORC_MODEL')
    try:
        response = litellm.completion(
            model=f'openrouter/{model}',
            messages=[{'role': 'user', 'content': prompt}],
            api_key=os.getenv('OPENROUTER_API_KEY'),
            api_base='https://openrouter.ai/api/v1',
            response_format={'type':'json_object'},
            temperature=0,
            max_tokens=4000,
        )

        content = response.choices[0].message.content
        if not content:
            msg = response.choices[0].message
            reasoning = getattr(msg, 'reasoning_content', None) or (
                getattr(msg, 'provider_specific_fields', None) or {}
            ).get('reasoning_content', '')

            if reasoning:
                import re
                json_blocks = re.findall(r'```(?:json)?\s*\n(.*?)```', reasoning, re.DOTALL)
                if json_blocks:
                    content = json_blocks[-1].strip()
            
        if not content:
            logger.error('LLM returned empty content. Full response: %s', response)
            return {'error': 'LLM returned empty response'}
        
        content = content.strip()

        if content.startswith('```'):
            content = content.split('\n', 1)[1]
            content = content.rsplit('```', 1)[0]
            content = content.strip()

        return json.loads(content)
    
    except json.JSONDecodeError as exc:
        logger.error('Failed to parse LLM response as JSON: %s - raw: %s', exc)
        return {'error': f'JSON parsing failed: {exc}'}

    except Exception as e:
        logger.error('LLM extraction failed: %s', e)
        return {'error': e}