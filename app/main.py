"""
main.py
-------
FastAPI entrypoint. Exposes:

  POST   /api/templates          upload a new template file
  GET    /api/templates          list all stored templates
  GET    /api/templates/{id}     get one template's detail
  DELETE /api/templates/{id}     remove a template
  POST   /api/match              upload a document, get ranked template matches
  GET    /api/health             simple healthcheck

Run with:  uvicorn app.main:app --reload --port 8000
Docs auto-generated at:  http://localhost:8000/docs
"""
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from typing import Optional

from . import storage, matcher
from .extractor import extract_text
from .embedder import embed_text
from .models import TemplateOut, MatchResponse, MatchResult, DeleteResponse

app = FastAPI(
    title="Document Template Matching API",
    description="Upload template documents, then match new documents against them "
                "using semantic (embedding-based) similarity.",
    version="1.0.0",
)

# Allow a separate frontend (React/Vite dev server etc.) to call this API.
# Tighten this to your actual frontend origin before deploying.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    storage.init_db()


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/templates", response_model=TemplateOut)
async def upload_template(
    file: UploadFile = File(...),
    name: str = Form(...),
    category: Optional[str] = Form(None),
):
    """Register a new template: extract its text, embed it, store it."""
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(400, "Uploaded file is empty.")

    try:
        extraction = extract_text(file.filename, file_bytes)
    except ValueError as e:
        raise HTTPException(400, str(e))

    if not extraction.text:
        raise HTTPException(
            422, "Could not extract any text from this file (even via OCR)."
        )

    vector = embed_text(extraction.text)
    new_id = storage.add_template(
        name=name,
        category=category,
        filename=file.filename,
        extracted_text=extraction.text,
        embedding=vector,
    )
    row = storage.get_template(new_id)
    return TemplateOut(
        id=row["id"],
        name=row["name"],
        category=row["category"],
        filename=row["filename"],
        text_preview=row["extracted_text"][:200],
        created_at=row["created_at"],
    )


@app.get("/api/templates", response_model=list[TemplateOut])
def list_templates():
    rows = storage.get_all_templates()
    return [
        TemplateOut(
            id=r["id"],
            name=r["name"],
            category=r["category"],
            filename=r["filename"],
            text_preview=r["extracted_text"][:200],
            created_at=r["created_at"],
        )
        for r in rows
    ]


@app.get("/api/templates/{template_id}", response_model=TemplateOut)
def get_template(template_id: int):
    row = storage.get_template(template_id)
    if not row:
        raise HTTPException(404, "Template not found.")
    return TemplateOut(
        id=row["id"],
        name=row["name"],
        category=row["category"],
        filename=row["filename"],
        text_preview=row["extracted_text"][:200],
        created_at=row["created_at"],
    )


@app.delete("/api/templates/{template_id}", response_model=DeleteResponse)
def remove_template(template_id: int):
    deleted = storage.delete_template(template_id)
    if not deleted:
        raise HTTPException(404, "Template not found.")
    return DeleteResponse(deleted_id=template_id, message="Template deleted.")


@app.post("/api/match", response_model=MatchResponse)
async def match_document(file: UploadFile = File(...), top_n: int = 5):
    """Upload any document and get back the top-N most similar templates."""
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(400, "Uploaded file is empty.")

    try:
        extraction = extract_text(file.filename, file_bytes)
    except ValueError as e:
        raise HTTPException(400, str(e))

    if not extraction.text:
        raise HTTPException(
            422, "Could not extract any text from this file (even via OCR)."
        )

    query_vector = embed_text(extraction.text)
    matches = matcher.find_matches(query_vector, top_n=top_n)

    return MatchResponse(
        query_filename=file.filename,
        extraction_method=extraction.method,
        extracted_text_preview=extraction.text[:300],
        top_matches=[MatchResult(**m) for m in matches],
    )


# --- Simple demo frontend (static HTML) served at "/" ---
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
def serve_demo_page():
    return FileResponse(static_dir / "index.html")
