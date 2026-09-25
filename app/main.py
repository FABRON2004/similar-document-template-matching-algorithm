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

<<<<<<< HEAD
import numpy as np

=======
>>>>>>> ba5f726fc4c60de617d94b6f15883cd8ae6b35d2
from . import storage, matcher
from .extractor import extract_text
from .embedder import embed_text
from .models import TemplateOut, MatchResponse, MatchResult, DeleteResponse

<<<<<<< HEAD
CATEGORY_TEMPLATES = {
    "business": {
        "label": "Business",
        "icon": "🏢",
        "text": "Business Proposal Executive Summary Company Overview Market Analysis "
                "Objectives Strategy Marketing Plan Sales Forecast Operations Plan "
                "Management Team Organizational Structure Financial Projections Revenue "
                "Model Competitive Analysis Risk Assessment Growth Strategy Partnership "
                "Agreement Stakeholders Meeting Minutes Action Items Deliverables Timeline "
                "Milestones Budget Allocation Return on Investment Board of Directors "
                "Client Customer Vendor Proposal Contract Invoice Budget Service Product "
                "Pricing Offer Renewal Operations Team"
    },
    "education": {
        "label": "Education",
        "icon": "🎓",
        "text": "Academic Transcript Student Name Course Title Semester Grade Point "
                "Average Credits Earned Attendance Record Curriculum Syllabus Examination "
                "Marks Assignment Submission Report Card Principal Signature School Name "
                "Enrollment Number Subject Marks Obtained Total Marks Percentage Scored "
                "Class Rank Extracurricular Activities Academic Achievement Certificate "
                "of Merit Faculty Advisor Student Teacher College University Course Grade"
    },
    "medical": {
        "label": "Medical",
        "icon": "🩺",
        "text": "Patient Name Date of Birth Medical Record Number Diagnosis "
                "Prescription Dosage Physician Name Hospital Name Treatment Plan Symptoms "
                "Vital Signs Blood Pressure Lab Results Test Report Follow Up Appointment "
                "Discharge Summary Allergies Medication History Consultation Notes "
                "Referral Insurance Claim Health Checkup Immunization Record Ward Number "
                "Doctor Nurse Clinic Care Medication Surgery Diagnosis Treatment"
    },
    "financial": {
        "label": "Financial",
        "icon": "💰",
        "text": "Balance Sheet Income Statement Cash Flow Statement Assets Liabilities "
                "Equity Revenue Expenses Net Profit Gross Margin Tax Filing Audit Report "
                "Bank Statement Account Number Transaction History Investment Portfolio "
                "Interest Rate Loan Agreement Credit Score Financial Year Quarterly Report "
                "Annual Report Shareholder Dividend Fiscal Period Cash Flow Balance Sheet"
    },
}

=======
>>>>>>> ba5f726fc4c60de617d94b6f15883cd8ae6b35d2
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


<<<<<<< HEAD
@app.post("/api/categories/match")
async def match_document_against_categories(file: UploadFile = File(...)):
    """Compare one document against the fixed category templates using embeddings."""
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
    scored = []
    for key, payload in CATEGORY_TEMPLATES.items():
        category_vector = embed_text(payload["text"])
        score = float(np.dot(query_vector, category_vector))
        scored.append({
            "key": key,
            "label": payload["label"],
            "icon": payload["icon"],
            "score": round(score, 4),
            "confidence_label": (
                "High" if score >= 0.80 else "Medium" if score >= 0.60 else "Low" if score >= 0.40 else "Very Low"
            )
        })
    scored.sort(key=lambda item: item["score"], reverse=True)
    return {
        "query_filename": file.filename,
        "extraction_method": extraction.method,
        "results": scored,
    }


=======
>>>>>>> ba5f726fc4c60de617d94b6f15883cd8ae6b35d2
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
