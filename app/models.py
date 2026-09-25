"""
Pydantic schemas used across the API for request validation and response shaping.
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class TemplateOut(BaseModel):
    """What we return to the client when describing a stored template."""
    id: int
    name: str
    category: Optional[str] = None
    filename: str
    text_preview: str
    created_at: datetime

    class Config:
        from_attributes = True


class MatchResult(BaseModel):
    """A single scored candidate returned by the matcher."""
    template_id: int
    name: str
    category: Optional[str] = None
    similarity_score: float          # 0.0 - 1.0 (cosine similarity)
    confidence_label: str            # human readable bucket, e.g. "High"


class MatchResponse(BaseModel):
    query_filename: str
    extraction_method: str           # "native_text" or "ocr"
    extracted_text_preview: str
    top_matches: List[MatchResult]


class DeleteResponse(BaseModel):
    deleted_id: int
    message: str
