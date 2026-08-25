from functools import lru_cache

import numpy as np

from sentence_transformers import (
    SentenceTransformer,
)

from app.core.config import settings


# ==========================================================
# LOAD MODEL
# ==========================================================

@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """
    Load embedding model once and reuse it.

    The first call loads/downloads the model.
    Later calls reuse the same model.
    """

    return SentenceTransformer(
        settings.EMBEDDING_MODEL_NAME
    )


# ==========================================================
# EMBEDDING DIMENSION
# ==========================================================

def get_embedding_dimension() -> int:

    model = get_embedding_model()

    dimension = (
        model.get_sentence_embedding_dimension()
    )

    if dimension is None:

        raise RuntimeError(
            "Could not determine embedding dimension."
        )

    return dimension


# ==========================================================
# ENCODE MANY TEXTS
# ==========================================================

def encode_texts(
    texts: list[str],
    show_progress_bar: bool = False,
) -> np.ndarray:

    if not texts:

        return np.empty(
            (
                0,
                get_embedding_dimension(),
            ),
            dtype=np.float32,
        )

    model = get_embedding_model()

    embeddings = model.encode(
        texts,
        batch_size=(
            settings.EMBEDDING_BATCH_SIZE
        ),
        show_progress_bar=show_progress_bar,
        convert_to_numpy=True,

        # Important:
        # normalized embeddings allow inner product
        # to behave like cosine similarity.
        normalize_embeddings=True,
    )

    return embeddings.astype(
        np.float32,
        copy=False,
    )


# ==========================================================
# ENCODE ONE TEXT
# ==========================================================

def encode_text(
    text: str,
) -> np.ndarray:

    if (
        not text
        or not text.strip()
    ):

        raise ValueError(
            "Text cannot be empty."
        )

    embeddings = encode_texts(
        [text]
    )

    return embeddings[0]