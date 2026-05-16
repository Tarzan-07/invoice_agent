"""
server.py FastAPI backend for the invoice agent frontend.

Endpoints - 
    POST - /upload  - receive one or more invoice files, run the full pipeline. 
    GET - /invoices - list all stored invoices
    GET - /health   - liveness check

Run -
    uvicorn server:app --reload --port 8888
"""


import ssl
import certifi

_orig_create_default_context = ssl.create_default_context

def _certifi_default_context(purpose=ssl.Purpose.SERVER_AUTH, *args, **kwargs):
    ctx = _orig_create_default_context(purpose, *args, **kwargs)
    ctx.load_verify_locations(certifi.where())
    return ctx

ssl.create_default_context = _certifi_default_context


# SSL Config

import os
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
os.environ['CURL_CA_BUNDLE'] = certifi.where()
os.environ['SSL_VERIFY'] = 'false'
os.environ['LITELLM_SSL_VERIFY'] = 'false'

# Load .env file

from dotenv import load_dotenv
load_dotenv()

import logging
import shutil
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s - %(message)s"
)

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".tiff"}

app = FastAPI(title="Invoice Agent API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['*'],
    allow_headers=['*']
)

# Static Frontend - Kind of an alias for frontend directory. Any endpoint with /static, will get directed
# to this directory.

FRONTEND_DIR = Path(__file__).parent / "frontend"

app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/", include_in_schema=False)
async def serve_index():
    return FileResponse(str(FRONTEND_DIR / "index.html"))
# Health check. FastAPI by default will check the endpoint named '/health' for health check. 

@app.get("/health")
async def health_check():
    return {'status': 'ok'}


# Upload functionality

@app.post("/upload")
async def upload_invoices(files: list[UploadFile] = File(...)):
    """Accept one or more invoice files, run the full ingestion pipeline."""

    from main import process_file

    results = []

    for upload in files:
        suffix = Path(upload.filename).suffix.lower()
        if suffix not in SUPPORTED_EXTENSIONS:
            results.append({
                'filename': upload.filename,
                'success': False,
                'error': f"Unsupported file type '{suffix}'."
                    f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
            })
            continue

        with tempfile.NamedTemporaryFile(
            suffix=suffix, delete=False, prefix='invoice_'
        ) as tmp:
            shutil.copyfileobj(upload.file, tmp)
            tmp_path = tmp.name

        try:
            result = process_file(tmp_path)
            result['filename'] = upload.filename

        except Exception as e:
            logger.exception("Pipeline error for %s", upload.filename)
            result = {
                'filename': upload.filename,
                'success': False,
                'error': str(e)
            }
        finally:
            Path(tmp_path).unlink(missing_ok=True)

        results.append(result)
    return {'results': results}


# List invoices:

@app.get("/invoices")
async def list_invoices():
    """Return all the stored invoices for the frontend dashboard."""
    
    try:
        from Storage.query import get_all_invoices
        return {'invoices': get_all_invoices()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Chat with orchestrator agent

class ChatRequest(BaseModel):
    message: str
    session_id: str = 'default'

_runner = None
_session_service = None

async def _get_runner():
    global _runner, _session_service
    if _runner is None:
        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService
        from Central_Agent.agent import root_agent

        _session_service = InMemorySessionService()
        _runner = Runner(
            agent=root_agent,
            app_name="invoice_agent",
            session_service=_session_service
        )
    return _runner, _session_service


@app.post("/chat")
async def chat(req: ChatRequest):
    """Send a message to the orchestrator agent and return its reply."""
    from google.genai.types import Content, Part
    import asyncio

    runner, session_service = await _get_runner()

    try:
        session = await session_service.get_session(
            app_name="invoice_agent",
            user_id="web_user",
            session_id=req.session_id
        )
    except TypeError:
        session = session_service.get_session(
            app_name="invoice_agent",
            user_id="web_user",
            session_id=req.session_id
        )


    if session is None:
        try:
            session = await session_service.create_session(
                app_name="invoice_agent",
                user_id="web_user",
                session_id=req.session_id,
            )

        except TypeError:
            session = session_service.create_session(
                app_name='invoice_agent',
                user_id='web_user',
                session_id=req.session_id
            )

    message = Content(role="user", parts=[Part(text=req.message)])

    reply_text= ""
    async for event in runner.run_async(
        user_id="web_user",
        session_id=req.session_id,
        new_message=message,
    ):
        if event.is_final_response() and event.content and event.content.parts:
            reply_text = event.content.parts[0].text or ""

    return {'reply': reply_text}