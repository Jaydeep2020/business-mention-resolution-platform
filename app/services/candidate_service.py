from difflib import SequenceMatcher

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.business import Business
from app.models.mention import Mention


class CandidateService:

    # Main threshold for automatic resolution
    AUTO_RESOLUTION_THRESHOLD = 0.85

    # If top two candidates are too close,
    # send the mention for manual review.
    AMBIGUITY_GAP = 0.05

    # Maximum number of rows fetched from DB
    # before scoring.
    MAX_DB_CANDIDATES = 100

    @staticmethod
    def normalize_text(text: str) -> str:
        """
        Normalize text before comparison.

        Example:

        "Tony's Pizza!"
            ->
        "tonys pizza"
        """

        if not text:
            return ""

        text = text.lower().strip()

        allowed = []

        for char in text:

            if char.isalnum() or char.isspace():
                allowed.append(char)

        normalized = "".join(allowed)

        return " ".join(
            normalized.split()
        )

    @classmethod
    def similarity(
        cls,
        text1: str,
        text2: str,
    ) -> float:

        text1 = cls.normalize_text(text1)
        text2 = cls.normalize_text(text2)

        if not text1 or not text2:
            return 0.0

        if text1 == text2:
            return 1.0

        return SequenceMatcher(
            None,
            text1,
            text2,
        ).ratio()

    @classmethod
    def token_overlap(
        cls,
        text1: str,
        text2: str,
    ) -> float:

        text1 = cls.normalize_text(text1)
        text2 = cls.normalize_text(text2)

        if not text1 or not text2:
            return 0.0

        tokens1 = set(text1.split())
        tokens2 = set(text2.split())

        if not tokens1 or not tokens2:
            return 0.0

        intersection = tokens1.intersection(
            tokens2
        )

        union = tokens1.union(
            tokens2
        )

        return len(intersection) / len(union)

    @classmethod
    def calculate_name_score(
        cls,
        mention_text: str,
        business_name: str,
    ) -> float:

        sequence_score = cls.similarity(
            mention_text,
            business_name,
        )

        token_score = cls.token_overlap(
            mention_text,
            business_name,
        )

        # Give more importance to the actual
        # string similarity.
        return (
            0.70 * sequence_score
            + 0.30 * token_score
        )

    @classmethod
    def calculate_city_score(
        cls,
        source_text: str | None,
        city: str | None,
    ) -> float:

        if not source_text or not city:
            return 0.0

        source_normalized = cls.normalize_text(
            source_text
        )

        city_normalized = cls.normalize_text(
            city
        )

        if not city_normalized:
            return 0.0

        if city_normalized in source_normalized:
            return 1.0

        return cls.similarity(
            source_normalized,
            city_normalized,
        ) * 0.5

    @classmethod
    def calculate_state_score(
        cls,
        source_text: str | None,
        state: str | None,
    ) -> float:

        if not source_text or not state:
            return 0.0

        source_normalized = cls.normalize_text(
            source_text
        )

        state_normalized = cls.normalize_text(
            state
        )

        if not state_normalized:
            return 0.0

        if state_normalized in source_normalized:
            return 1.0

        return 0.0

    @classmethod
    def calculate_address_score(
        cls,
        source_text: str | None,
        address: str | None,
    ) -> float:

        if not source_text or not address:
            return 0.0

        source_normalized = cls.normalize_text(
            source_text
        )

        address_normalized = cls.normalize_text(
            address
        )

        if not address_normalized:
            return 0.0

        # Check complete address first
        if address_normalized in source_normalized:
            return 1.0

        # Otherwise use token overlap
        return cls.token_overlap(
            source_normalized,
            address_normalized,
        )

    @classmethod
    def calculate_score(
        cls,
        mention: Mention,
        business: Business,
    ) -> dict:

        name_score = cls.calculate_name_score(
            mention.text,
            business.name,
        )

        city_score = cls.calculate_city_score(
            mention.source_text,
            business.city,
        )

        state_score = cls.calculate_state_score(
            mention.source_text,
            business.state,
        )

        address_score = cls.calculate_address_score(
            mention.source_text,
            business.address,
        )

        # Name has the highest importance.
        final_score = (
            (name_score * 0.65)
            + (city_score * 0.15)
            + (state_score * 0.10)
            + (address_score * 0.10)
        )

        # Make sure floating point value remains
        # inside [0, 1].
        final_score = max(
            0.0,
            min(1.0, final_score),
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

    @classmethod
    def get_candidates(
        cls,
        session: Session,
        mention: Mention,
        max_candidates: int = 5,
    ) -> list[dict]:

        mention_text = cls.normalize_text(
            mention.text
        )

        if not mention_text:
            return []

        # Split into words.
        tokens = [
            token
            for token in mention_text.split()
            if len(token) >= 2
        ]

        # Create DB conditions using name.
        conditions = []

        for token in tokens:
            conditions.append(
                Business.name.ilike(
                    f"%{token}%"
                )
            )

        # If we have no usable tokens, return nothing.
        if not conditions:
            return []

        stmt = (
            select(Business)
            .where(
                or_(*conditions)
            )
            .limit(
                cls.MAX_DB_CANDIDATES
            )
        )

        businesses = list(
            session.execute(stmt)
            .scalars()
            .all()
        )

        scored_candidates = []

        for business in businesses:

            scores = cls.calculate_score(
                mention,
                business,
            )

            scored_candidates.append(
                {
                    "business": business,
                    **scores,
                }
            )

        # Highest score first
        scored_candidates.sort(
            key=lambda item: item["score"],
            reverse=True,
        )

        return scored_candidates[
            :max_candidates
        ]