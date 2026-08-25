
# Now we combine the old algorithm with FAISS.

from difflib import SequenceMatcher

from sqlalchemy import (
    or_,
    select,
)

from sqlalchemy.orm import Session

from app.core.config import settings

from app.models.business import Business
from app.models.mention import Mention

from app.services.embedding_service import (
    BusinessEmbeddingService,
)


class CandidateService:

    AUTO_RESOLUTION_THRESHOLD = 0.85

    AMBIGUITY_GAP = 0.05

    MAX_DB_CANDIDATES = 100

    VECTOR_SEARCH_CANDIDATES = (
        settings.VECTOR_SEARCH_CANDIDATES
    )


    # ======================================================
    # NORMALIZE
    # ======================================================

    @staticmethod
    def normalize_text(
        text: str,
    ) -> str:

        if not text:

            return ""

        text = (
            text
            .lower()
            .strip()
        )

        allowed = []

        for char in text:

            if (
                char.isalnum()
                or char.isspace()
            ):

                allowed.append(
                    char
                )

        normalized = "".join(
            allowed
        )

        return " ".join(
            normalized.split()
        )


    # ======================================================
    # STRING SIMILARITY
    # ======================================================

    @classmethod
    def similarity(
        cls,
        text1: str,
        text2: str,
    ) -> float:

        text1 = cls.normalize_text(
            text1
        )

        text2 = cls.normalize_text(
            text2
        )

        if (
            not text1
            or not text2
        ):

            return 0.0

        if text1 == text2:

            return 1.0

        return SequenceMatcher(
            None,
            text1,
            text2,
        ).ratio()


    # ======================================================
    # TOKEN OVERLAP
    # ======================================================

    @classmethod
    def token_overlap(
        cls,
        text1: str,
        text2: str,
    ) -> float:

        text1 = cls.normalize_text(
            text1
        )

        text2 = cls.normalize_text(
            text2
        )

        if (
            not text1
            or not text2
        ):

            return 0.0

        tokens1 = set(
            text1.split()
        )

        tokens2 = set(
            text2.split()
        )

        if (
            not tokens1
            or not tokens2
        ):

            return 0.0

        intersection = (
            tokens1.intersection(
                tokens2
            )
        )

        union = (
            tokens1.union(
                tokens2
            )
        )

        return (
            len(intersection)
            / len(union)
        )


    # ======================================================
    # NAME SCORE
    # ======================================================

    @classmethod
    def calculate_name_score(
        cls,
        mention_text: str,
        business_name: str,
    ) -> float:

        sequence_score = (
            cls.similarity(
                mention_text,
                business_name,
            )
        )

        token_score = (
            cls.token_overlap(
                mention_text,
                business_name,
            )
        )

        return (
            0.70 * sequence_score
            + 0.30 * token_score
        )


    # ======================================================
    # CITY
    # ======================================================

    @classmethod
    def calculate_city_score(
        cls,
        source_text: str | None,
        city: str | None,
    ) -> float:

        if (
            not source_text
            or not city
        ):

            return 0.0

        source_normalized = (
            cls.normalize_text(
                source_text
            )
        )

        city_normalized = (
            cls.normalize_text(
                city
            )
        )

        if not city_normalized:

            return 0.0

        if (
            city_normalized
            in source_normalized
        ):

            return 1.0

        return (
            cls.similarity(
                source_normalized,
                city_normalized,
            )
            * 0.5
        )


    # ======================================================
    # STATE
    # ======================================================

    @classmethod
    def calculate_state_score(
        cls,
        source_text: str | None,
        state: str | None,
    ) -> float:

        if (
            not source_text
            or not state
        ):

            return 0.0

        source_normalized = (
            cls.normalize_text(
                source_text
            )
        )

        state_normalized = (
            cls.normalize_text(
                state
            )
        )

        if not state_normalized:

            return 0.0

        if (
            state_normalized
            in source_normalized
        ):

            return 1.0

        return 0.0


    # ======================================================
    # ADDRESS
    # ======================================================

    @classmethod
    def calculate_address_score(
        cls,
        source_text: str | None,
        address: str | None,
    ) -> float:

        if (
            not source_text
            or not address
        ):

            return 0.0

        source_normalized = (
            cls.normalize_text(
                source_text
            )
        )

        address_normalized = (
            cls.normalize_text(
                address
            )
        )

        if not address_normalized:

            return 0.0

        if (
            address_normalized
            in source_normalized
        ):

            return 1.0

        return cls.token_overlap(
            source_normalized,
            address_normalized,
        )


    # ======================================================
    # FINAL SCORE
    # ======================================================

    @classmethod
    def calculate_score(
        cls,
        mention: Mention,
        business: Business,
        embedding_score: float | None = None,
    ) -> dict:

        name_score = (
            cls.calculate_name_score(
                mention.text,
                business.name,
            )
        )

        city_score = (
            cls.calculate_city_score(
                mention.source_text,
                business.city,
            )
        )

        state_score = (
            cls.calculate_state_score(
                mention.source_text,
                business.state,
            )
        )

        address_score = (
            cls.calculate_address_score(
                mention.source_text,
                business.address,
            )
        )

        # --------------------------------------------------
        # FALLBACK
        #
        # If FAISS index hasn't been built yet,
        # preserve your previous scoring formula.
        # --------------------------------------------------

        if embedding_score is None:

            final_score = (
                name_score * 0.65
                + city_score * 0.15
                + state_score * 0.10
                + address_score * 0.10
            )

        # --------------------------------------------------
        # HYBRID SCORE
        # --------------------------------------------------

        else:

            embedding_score = max(
                0.0,
                min(
                    1.0,
                    embedding_score,
                ),
            )

            final_score = (
                name_score * 0.50
                + embedding_score * 0.25
                + city_score * 0.10
                + state_score * 0.05
                + address_score * 0.10
            )

        final_score = max(
            0.0,
            min(
                1.0,
                final_score,
            ),
        )

        return {
            "score": round(
                final_score,
                4,
            ),
            "name_score": round(
                name_score,
                4,
            ),
            "embedding_score": (
                round(
                    embedding_score,
                    4,
                )
                if embedding_score
                is not None
                else None
            ),
            "city_score": round(
                city_score,
                4,
            ),
            "state_score": round(
                state_score,
                4,
            ),
            "address_score": round(
                address_score,
                4,
            ),
        }


    # ======================================================
    # GET CANDIDATES
    # ======================================================

    @classmethod
    def get_candidates(
        cls,
        session: Session,
        mention: Mention,
        max_candidates: int = 5,
    ) -> list[dict]:

        mention_text = (
            cls.normalize_text(
                mention.text
            )
        )

        if not mention_text:

            return []

        # ==================================================
        # 1. OLD LEXICAL DATABASE SEARCH
        # ==================================================

        tokens = [
            token
            for token
            in mention_text.split()
            if len(token) >= 2
        ]

        lexical_businesses = []

        conditions = []

        for token in tokens:

            conditions.append(
                Business.name.ilike(
                    f"%{token}%"
                )
            )

        if conditions:

            lexical_businesses = list(
                session.execute(
                    select(Business)
                    .where(
                        or_(
                            *conditions
                        )
                    )
                    .limit(
                        cls
                        .MAX_DB_CANDIDATES
                    )
                )
                .scalars()
                .all()
            )

        # ==================================================
        # 2. VECTOR SEARCH
        # ==================================================

        vector_ready = (
            BusinessEmbeddingService
            .is_ready()
        )

        vector_results = []

        if vector_ready:

            vector_results = (
                BusinessEmbeddingService
                .search_businesses(
                    mention=mention,
                    top_k=(
                        cls
                        .VECTOR_SEARCH_CANDIDATES
                    ),
                )
            )

        # {
        #     business PK: embedding score
        # }
        vector_score_map = {
            item["business_id"]:
            item["embedding_score"]
            for item
            in vector_results
        }

        # ==================================================
        # 3. MERGE LEXICAL + VECTOR CANDIDATES
        # ==================================================

        business_map = {
            business.id: business
            for business
            in lexical_businesses
        }

        vector_business_ids = list(
            vector_score_map.keys()
        )

        missing_business_ids = [
            business_id
            for business_id
            in vector_business_ids
            if business_id
            not in business_map
        ]

        if missing_business_ids:

            vector_businesses = list(
                session.execute(
                    select(Business)
                    .where(
                        Business.id.in_(
                            missing_business_ids
                        )
                    )
                )
                .scalars()
                .all()
            )

            for business in vector_businesses:

                business_map[
                    business.id
                ] = business

        if not business_map:

            return []

        # ==================================================
        # 4. SCORE ALL MERGED CANDIDATES
        # ==================================================

        scored_candidates = []

        for business in (
            business_map.values()
        ):

            if vector_ready:

                embedding_score = (
                    vector_score_map.get(
                        business.id,
                        0.0,
                    )
                )

            else:

                # Causes calculate_score() to use the
                # previous scoring formula.
                embedding_score = None

            scores = (
                cls.calculate_score(
                    mention=mention,
                    business=business,
                    embedding_score=(
                        embedding_score
                    ),
                )
            )

            scored_candidates.append(
                {
                    "business": business,
                    **scores,
                }
            )

        # ==================================================
        # 5. HIGHEST SCORE FIRST
        # ==================================================

        scored_candidates.sort(
            key=lambda item: (
                item["score"]
            ),
            reverse=True,
        )

        return scored_candidates[
            :max_candidates
        ]

    # Preserve the original scoring formula when the FAISS index
    # is unavailable, so resolution can continue working even
    # before the vector index has been built.
    #
    # Fallback scoring:
    # Name    = 0.65
    # City    = 0.15
    # State   = 0.10
    # Address = 0.10