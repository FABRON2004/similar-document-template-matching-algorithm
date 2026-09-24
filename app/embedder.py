"""
embedder.py
-----------
Wraps a sentence-transformers model so the rest of the app never has to
think about the ML details. Semantic embeddings mean two documents can
match even if they don't share exact wording -- e.g. an "Invoice" template
and a "Bill" document with similar structure/meaning will still score high,
which plain keyword matching (TF-IDF) would miss.

Model: all-MiniLM-L6-v2
  - 384-dim vectors, ~80MB, runs fine on CPU, good accuracy/speed tradeoff.
  - First run downloads the model from HuggingFace (needs internet once;
    it's then cached locally under ~/.cache).
"""
import re
import numpy as np
from functools import lru_cache

MODEL_NAME = "all-MiniLM-L6-v2"
MAX_INPUT_CHARS = 5000  # keep embedding calls fast; templates rarely need more


def _clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)  # collapse whitespace/newlines
    return text.strip()[:MAX_INPUT_CHARS]


@lru_cache(maxsize=1)
def _get_model():
    # Imported lazily so the rest of the app can be tested/imported
    # without paying the (heavy) import cost of torch + transformers.
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(MODEL_NAME)


def embed_text(text: str) -> np.ndarray:
    """Return a single L2-normalized embedding vector for the given text."""
    cleaned = _clean_text(text)
    if not cleaned:
        # Empty document -> zero vector (will score 0 similarity everywhere)
        model = _get_model()
        dim = model.get_sentence_embedding_dimension()
        return np.zeros(dim, dtype=np.float32)

    model = _get_model()
    vector = model.encode(cleaned, normalize_embeddings=True)
    return vector.astype(np.float32)


def embed_batch(texts: list[str]) -> np.ndarray:
    """Batch version - more efficient when embedding many templates at once."""
    cleaned = [_clean_text(t) for t in texts]
    model = _get_model()
    vectors = model.encode(cleaned, normalize_embeddings=True, batch_size=16)
    return vectors.astype(np.float32)
