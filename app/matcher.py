"""
matcher.py
----------
Given a query embedding, ranks all stored templates by cosine similarity.
Since embeddings from embedder.py are already L2-normalized, cosine
similarity reduces to a plain dot product -- fast even with numpy loops
for the modest number of templates a college project will realistically have.
"""
import numpy as np
from . import storage


def _confidence_label(score: float) -> str:
    if score >= 0.80:
        return "High"
    elif score >= 0.60:
        return "Medium"
    elif score >= 0.40:
        return "Low"
    return "Very Low"


def find_matches(query_embedding: np.ndarray, top_n: int = 5) -> list[dict]:
    templates = storage.get_all_templates()
    if not templates:
        return []

    scored = []
    for row in templates:
        template_vec = storage.row_to_embedding(row)
        # Both vectors are unit-normalized -> dot product == cosine similarity
        score = float(np.dot(query_embedding, template_vec))
        scored.append({
            "template_id": row["id"],
            "name": row["name"],
            "category": row["category"],
            "similarity_score": round(score, 4),
            "confidence_label": _confidence_label(score),
        })

    scored.sort(key=lambda x: x["similarity_score"], reverse=True)
    return scored[:top_n]
