# Document Template Matching System

Upload reference **templates** (invoices, certificates, forms, etc.), then
upload any new document and get back the templates it most closely
resembles — ranked by semantic similarity, not just keyword overlap.

## How it works

```
Uploaded file (PDF/DOCX/TXT/PNG/JPG)
        │
        ▼
 extractor.py  ── PDF: try native text (PyMuPDF) → falls back to OCR
                   (Tesseract) automatically if the PDF is a scanned
                   image with no text layer
                   DOCX: python-docx | TXT: direct read
                   Images: OCR directly
        │
        ▼
 embedder.py   ── sentence-transformers (all-MiniLM-L6-v2) turns the
                   text into a 384-dim semantic vector. Two documents
                   with different wording but the same *meaning/structure*
                   still score high — this is what makes it "smart"
                   matching rather than exact-text matching.
        │
        ▼
 storage.py    ── SQLite. Each template's text + embedding is stored.
        │
        ▼
 matcher.py    ── cosine similarity between the query embedding and
                   every stored template embedding → ranked list.
```

## Project structure

```
document_matcher/
├── app/
│   ├── main.py         # FastAPI app + all routes
│   ├── extractor.py     # file → text (with OCR fallback)
│   ├── embedder.py      # text → embedding vector
│   ├── matcher.py        # embedding → ranked matches
│   ├── storage.py        # SQLite persistence
│   ├── models.py         # request/response schemas
│   └── static/
│       └── index.html   # demo frontend (upload + match UI)
├── requirements.txt
└── README.md
```

## Setup

```bash
# 1. System dependencies (for OCR)
sudo apt install tesseract-ocr poppler-utils

# 2. Python dependencies
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Run
uvicorn app.main:app --reload --port 8000
```

Then open **http://localhost:8000** — the bundled demo page lets you upload
templates and test matching directly in the browser.
Interactive API docs (auto-generated): **http://localhost:8000/docs**

> First run will download the `all-MiniLM-L6-v2` model (~80MB) from
> HuggingFace — needs internet access once, then it's cached locally.

## API Endpoints

| Method | Path                     | Purpose                                   |
|--------|--------------------------|--------------------------------------------|
| POST   | `/api/templates`         | Upload a new template (file + name + category) |
| GET    | `/api/templates`         | List all stored templates                 |
| GET    | `/api/templates/{id}`    | Get one template's detail                 |
| DELETE | `/api/templates/{id}`    | Remove a template                         |
| POST   | `/api/match`             | Upload a document, get top-N matches      |
| GET    | `/api/health`            | Healthcheck                               |

### Example: matching a document (curl)
```bash
curl -X POST http://localhost:8000/api/match \
  -F "file=@sample_invoice.pdf"
```
Response:
```json
{
  "query_filename": "sample_invoice.pdf",
  "extraction_method": "native_text",
  "extracted_text_preview": "INVOICE ...",
  "top_matches": [
    {"template_id": 3, "name": "Invoice Template A", "category": "Finance",
     "similarity_score": 0.87, "confidence_label": "High"},
    {"template_id": 1, "name": "Purchase Order Template", "category": "Finance",
     "similarity_score": 0.52, "confidence_label": "Low"}
  ]
}
```

## What's been tested in this build
- ✅ FastAPI app loads and all routes register correctly
- ✅ TXT extraction
- ✅ DOCX extraction (paragraphs + tables)
- ✅ Native-text PDF extraction
- ✅ Scanned-PDF → automatic OCR fallback (verified with a synthetic image-only PDF)
- ✅ SQLite storage: add / list / delete
- ✅ Cosine-similarity ranking logic (verified with synthetic vectors)
- ⚠️ The actual embedding model (`all-MiniLM-L6-v2`) could not be
  downloaded in this build environment (no internet access to HuggingFace),
  so run it once on your own machine to confirm — the plumbing around it
  is fully tested and correct.

## Frontend — what's built vs. what to build next

**Built (included):** `app/static/index.html` — a plain HTML/JS single-page
demo. It's intentionally minimal (no framework) so it runs with zero extra
setup and is enough to demonstrate the whole flow for your submission:
upload a template → upload a document to match → see ranked results with
similarity bars.

**Suggested full frontend (for the remaining 50%):** if you want a more
"production" looking submission, rebuild the same 3 screens in
React (or plain HTML if you want to keep it simple):

1. **Templates page** — grid/list of uploaded templates (name, category,
   upload date, delete button), with an "Add Template" modal/form.
2. **Match page** — a drag-and-drop upload zone, a "Matching..." loading
   state, then a ranked results list with:
   - similarity % as a progress bar (already returned by the API)
   - confidence badge (High/Medium/Low, already returned by the API)
   - expandable "extracted text preview" for transparency
3. **Optional: Document detail / history page** — if your project needs
   "matching history," add a `match_history` table (mirrors `templates`)
   that logs each match request + its top result, and a page listing past
   matches.

Since the API already returns clean JSON for all of this, the frontend
work is purely UI — no new backend logic needed for those three screens.

## Possible extensions if you have time before the deadline
- Weight OCR-derived text lower than native text in the confidence label
  (OCR introduces noise, so a 0.75 OCR match is less certain than a 0.75
  native-text match).
- Add a `/api/templates/{id}` PATCH endpoint to rename/re-categorize.
- Switch SQLite embeddings to `faiss` if you want to demonstrate proper
  vector-index search (overkill for a handful of templates, but examiners
  sometimes like seeing awareness of it).
- Add basic auth if multiple students/users will share one deployment.
