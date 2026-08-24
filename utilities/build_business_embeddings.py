import json
import os
import sys
from pathlib import Path

import faiss
import numpy as np

from sqlalchemy import (
    func,
    select,
)

from sqlalchemy.orm import (
    selectinload,
)

from tqdm import tqdm


# ==========================================================
# Make project root importable when running:
#
# python scripts/build_business_embeddings.py
# ==========================================================

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)

if str(PROJECT_ROOT) not in sys.path:

    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )


from app.core.config import settings

from app.core.embeddings import (
    encode_texts,
    get_embedding_dimension,
)

from app.db.database import (
    get_session,
)

from app.models.business import (
    Business,
)

from app.services.embedding_service import (
    BusinessEmbeddingService,
)


DB_BATCH_SIZE = 1000


def build_business_embeddings(
    session,
) -> None:

    # ======================================================
    # OUTPUT DIRECTORY
    # ======================================================

    index_path = (
        BusinessEmbeddingService
        .INDEX_PATH
    )

    metadata_path = (
        BusinessEmbeddingService
        .METADATA_PATH
    )

    index_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ======================================================
    # CREATE FAISS INDEX
    # ======================================================

    dimension = (
        get_embedding_dimension()
    )

    # Inner-product index.
    #
    # Since vectors are normalized,
    # inner product behaves like cosine similarity.
    flat_index = faiss.IndexFlatIP(
        dimension
    )

    # Business.id becomes the FAISS vector ID.
    index = faiss.IndexIDMap2(
        flat_index
    )

    # ======================================================
    # COUNT BUSINESSES
    # ======================================================

    total_businesses = (
        session.execute(
            select(
                func.count(
                    Business.id
                )
            )
        )
        .scalar_one()
    )

    print(
        f"Businesses to embed: "
        f"{total_businesses}"
    )

    if total_businesses == 0:

        print(
            "No businesses found."
        )

        return

    # ======================================================
    # PROCESS IN DATABASE BATCHES
    # ======================================================

    last_business_id = 0

    processed = 0

    progress = tqdm(
        total=total_businesses,
        desc="Building business embeddings",
        unit="business",
    )

    while True:

        businesses = list(
            session.execute(
                select(Business)
                .options(
                    selectinload(
                        Business.categories
                    )
                )
                .where(
                    Business.id
                    > last_business_id
                )
                .order_by(
                    Business.id.asc()
                )
                .limit(
                    DB_BATCH_SIZE
                )
            )
            .scalars()
            .unique()
            .all()
        )

        if not businesses:

            break

        # ----------------------------------------------
        # Convert each business into text
        # ----------------------------------------------

        business_texts = [
            BusinessEmbeddingService
            .build_business_text(
                business
            )
            for business
            in businesses
        ]

        # ----------------------------------------------
        # Generate embeddings
        # ----------------------------------------------

        embeddings = encode_texts(
            business_texts,
            show_progress_bar=False,
        )

        business_ids = np.asarray(
            [
                business.id
                for business
                in businesses
            ],
            dtype=np.int64,
        )

        # ----------------------------------------------
        # Add vectors + actual database IDs
        # ----------------------------------------------

        index.add_with_ids(
            embeddings,
            business_ids,
        )

        last_business_id = (
            businesses[-1].id
        )

        processed += len(
            businesses
        )

        progress.update(
            len(businesses)
        )

        # Avoid keeping ORM objects from every
        # previous batch.
        session.expunge_all()

    progress.close()

    # ======================================================
    # SAVE INDEX
    # ======================================================

    # Write to temporary files first so an interrupted
    # build doesn't replace a good existing index.

    temporary_index_path = (
        index_path.with_suffix(
            ".tmp.faiss"
        )
    )

    temporary_metadata_path = (
        metadata_path.with_suffix(
            ".tmp.json"
        )
    )

    faiss.write_index(
        index,
        str(
            temporary_index_path
        ),
    )

    metadata = {
        "model_name": (
            settings
            .EMBEDDING_MODEL_NAME
        ),
        "dimension": dimension,
        "business_count": processed,
    }

    temporary_metadata_path.write_text(
        json.dumps(
            metadata,
            indent=2,
        ),
        encoding="utf-8",
    )

    # Atomic-style replacement.
    os.replace(
        temporary_index_path,
        index_path,
    )

    os.replace(
        temporary_metadata_path,
        metadata_path,
    )

    print()
    print(
        "Business embedding index created."
    )

    print(
        f"Indexed businesses: {processed}"
    )

    print(
        f"Vector dimension: {dimension}"
    )

    print(
        f"Index path: {index_path}"
    )


if __name__ == "__main__":

    session_generator = (
        get_session()
    )

    session = next(
        session_generator
    )

    try:

        build_business_embeddings(
            session
        )

    finally:

        session_generator.close()