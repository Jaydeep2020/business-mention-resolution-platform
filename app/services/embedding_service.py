# This handles:
#
# Business → text for embedding
# Mention  → query text
# FAISS    → nearest businesses

import json
import logging
from pathlib import Path
from threading import Lock

import faiss
import numpy as np

from app.core.config import settings

from app.core.embeddings import (
    encode_text,
    get_embedding_dimension,
)

from app.models.business import Business
from app.models.mention import Mention


logger = logging.getLogger(
    __name__
)


class BusinessEmbeddingService:

    # ======================================================
    # PATHS
    # ======================================================

    PROJECT_ROOT = (
        Path(__file__)
        .resolve()
        .parents[2]
    )

    INDEX_PATH = (
        PROJECT_ROOT
        / settings.BUSINESS_VECTOR_INDEX_PATH
    )

    METADATA_PATH = (
        INDEX_PATH.with_suffix(
            ".json"
        )
    )

    # ======================================================
    # INDEX CACHE
    # ======================================================

    _index = None

    _index_lock = Lock()


    # ======================================================
    # BUSINESS TEXT
    # ======================================================

    @staticmethod
    def build_business_text(
        business: Business,
    ) -> str:
        """
        Create the text that represents one business.

        Example:

        Business: Starbucks.
        Address: 123 Main St.
        City: Tucson.
        State: AZ.
        Categories: Coffee & Tea, Cafes.
        """

        parts = [
            f"Business: {business.name}"
        ]

        if business.address:

            parts.append(
                f"Address: {business.address}"
            )

        if business.city:

            parts.append(
                f"City: {business.city}"
            )

        if business.state:

            parts.append(
                f"State: {business.state}"
            )

        if business.postal_code:

            parts.append(
                f"Postal code: "
                f"{business.postal_code}"
            )

        category_names = []

        if business.categories:

            category_names = [
                category.name
                for category
                in business.categories
            ]

        if category_names:

            parts.append(
                "Categories: "
                + ", ".join(
                    category_names
                )
            )

        return ". ".join(parts)


    # ======================================================
    # MENTION TEXT
    # ======================================================

    @staticmethod
    def build_mention_text(
        mention: Mention,
    ) -> str:
        """
        Text used as the vector-search query.
        """

        parts = [
            f"Business: {mention.text}"
        ]

        if mention.source_text:

            # Avoid unnecessarily embedding an extremely
            # large review.
            context = (
                mention.source_text
                .strip()
            )

            if len(context) > 1500:

                context = (
                    context[:1500]
                )

            parts.append(
                f"Context: {context}"
            )

        return ". ".join(parts)


    # ======================================================
    # INDEX EXISTS
    # ======================================================

    @classmethod
    def index_exists(
        cls,
    ) -> bool:

        return (
            cls.INDEX_PATH.exists()
            and cls.INDEX_PATH.is_file()
        )


    # ======================================================
    # LOAD INDEX
    # ======================================================

    @classmethod
    def get_index(
        cls,
    ):

        if cls._index is not None:

            return cls._index

        with cls._index_lock:

            if cls._index is not None:

                return cls._index

            if not cls.index_exists():

                return None

            # ----------------------------------------------
            # Validate metadata when available
            # ----------------------------------------------

            if cls.METADATA_PATH.exists():

                try:

                    metadata = json.loads(
                        cls.METADATA_PATH
                        .read_text(
                            encoding="utf-8"
                        )
                    )

                    indexed_model = (
                        metadata.get(
                            "model_name"
                        )
                    )

                    if (
                        indexed_model
                        and indexed_model
                        != settings.EMBEDDING_MODEL_NAME
                    ):

                        logger.warning(
                            (
                                "Business FAISS index was "
                                "built using model '%s', "
                                "but application currently "
                                "uses '%s'. Rebuild index."
                            ),
                            indexed_model,
                            settings
                            .EMBEDDING_MODEL_NAME,
                        )

                        return None

                except Exception:

                    logger.warning(
                        "Could not read FAISS metadata."
                    )

            # ----------------------------------------------
            # Read FAISS index
            # ----------------------------------------------

            index = faiss.read_index(
                str(cls.INDEX_PATH)
            )

            expected_dimension = (
                get_embedding_dimension()
            )

            if (
                index.d
                != expected_dimension
            ):

                logger.warning(
                    (
                        "FAISS dimension does not "
                        "match embedding model. "
                        "Rebuild the index."
                    )
                )

                return None

            cls._index = index

            return cls._index


    # ======================================================
    # CLEAR CACHE
    # ======================================================

    @classmethod
    def clear_index_cache(
        cls,
    ) -> None:

        with cls._index_lock:

            cls._index = None


    # ======================================================
    # INDEX READY
    # ======================================================

    @classmethod
    def is_ready(
        cls,
    ) -> bool:

        index = cls.get_index()

        return (
            index is not None
            and index.ntotal > 0
        )


    # ======================================================
    # VECTOR SEARCH
    # ======================================================

    @classmethod
    def search_businesses(
        cls,
        mention: Mention,
        top_k: int | None = None,
    ) -> list[dict]:
        """
        Return business database IDs with vector scores.

        Example:

        [
            {
                "business_id": 10,
                "embedding_score": 0.91
            },
            ...
        ]
        """

        index = cls.get_index()

        # Important:
        # If index has not been built yet, return [].
        #
        # CandidateService can still use its old
        # string-based candidate search.
        if (
            index is None
            or index.ntotal == 0
        ):

            return []

        if top_k is None:

            top_k = (
                settings
                .VECTOR_SEARCH_CANDIDATES
            )

        top_k = max(
            1,
            top_k,
        )

        top_k = min(
            top_k,
            index.ntotal,
        )

        query_text = (
            cls.build_mention_text(
                mention
            )
        )

        query_embedding = (
            encode_text(
                query_text
            )
        )

        query_embedding = (
            query_embedding
            .reshape(1, -1)
            .astype(
                np.float32,
                copy=False,
            )
        )

        scores, ids = index.search(
            query_embedding,
            top_k,
        )

        results = []

        for (
            business_id,
            raw_score,
        ) in zip(
            ids[0],
            scores[0],
        ):

            # FAISS uses -1 when fewer results
            # are available.
            if business_id < 0:

                continue

            # Because embeddings are normalized,
            # inner product behaves like cosine score.
            #
            # Clamp because our application confidence
            # values use [0, 1].
            embedding_score = max(
                0.0,
                min(
                    1.0,
                    float(raw_score),
                ),
            )

            results.append(
                {
                    "business_id": (
                        int(business_id)
                    ),
                    "embedding_score": round(
                        embedding_score,
                        4,
                    ),
                }
            )

        return results