import pytest

from app.models.business import Business
from app.models.mention import Mention
from app.models.enums import SourceType

from app.services.candidate_service import (
    CandidateService,
)


# ==========================================================
# NORMALIZATION
# ==========================================================

def test_normalize_text():

    result = (
        CandidateService.normalize_text(
            "  Tony's   Pizza!!!  "
        )
    )

    assert result == "tonys pizza"


def test_normalize_empty_text():

    assert (
        CandidateService.normalize_text("")
        == ""
    )


# ==========================================================
# SIMILARITY
# ==========================================================

def test_identical_text_has_full_similarity():

    score = (
        CandidateService.similarity(
            "Target",
            "target",
        )
    )

    assert score == 1.0


def test_different_names_have_lower_similarity():

    exact_score = (
        CandidateService.similarity(
            "Target",
            "Target",
        )
    )

    different_score = (
        CandidateService.similarity(
            "Target",
            "Walmart",
        )
    )

    assert exact_score > different_score


# ==========================================================
# TOKEN OVERLAP
# ==========================================================

def test_token_overlap():

    score = (
        CandidateService.token_overlap(
            "Tonys Pizza Restaurant",
            "Tonys Pizza",
        )
    )

    assert score > 0
    assert score <= 1


# ==========================================================
# LOCATION SCORING
# ==========================================================

def test_city_found_in_source_text():

    score = (
        CandidateService.calculate_city_score(
            source_text=(
                "I visited Target in Tucson yesterday."
            ),
            city="Tucson",
        )
    )

    assert score == 1.0


def test_state_found_in_source_text():

    score = (
        CandidateService.calculate_state_score(
            source_text=(
                "I visited the store in Tucson AZ."
            ),
            state="AZ",
        )
    )

    assert score == 1.0


def test_address_found_in_source_text():

    score = (
        CandidateService.calculate_address_score(
            source_text=(
                "I went to Target at "
                "5255 E Broadway Blvd yesterday."
            ),
            address=(
                "5255 E Broadway Blvd"
            ),
        )
    )

    assert score == 1.0


# ==========================================================
# COMPLETE SCORE
# ==========================================================

def test_exact_business_context_gets_high_score():

    mention = Mention(
        text="Target",
        source_text=(
            "I visited Target at "
            "5255 E Broadway Blvd "
            "in Tucson AZ."
        ),
        source_type=SourceType.REVIEW,
    )

    business = Business(
        business_id="target-1",
        name="Target",
        address="5255 E Broadway Blvd",
        city="Tucson",
        state="AZ",
        postal_code="85711",
        latitude=32.223236,
        longitude=-110.880452,
        is_verified=True,
    )

    scores = (
        CandidateService.calculate_score(
            mention=mention,
            business=business,
        )
    )

    assert scores["name_score"] == 1.0
    assert scores["city_score"] == 1.0
    assert scores["state_score"] == 1.0
    assert scores["address_score"] == 1.0

    assert scores["score"] == 1.0


# ==========================================================
# CANDIDATE RANKING
# ==========================================================

def test_best_candidate_is_returned_first(
    db_session,
    business_factory,
    mention_factory,
):

    tucson_target = business_factory(
        business_id="target-tucson",
        name="Target",
        address="5255 E Broadway Blvd",
        city="Tucson",
        state="AZ",
    )

    phoenix_target = business_factory(
        business_id="target-phoenix",
        name="Target",
        address="100 Phoenix Road",
        city="Phoenix",
        state="AZ",
    )

    business_factory(
        business_id="target-center",
        name="Target Practice Center",
        address="50 Practice Road",
        city="Phoenix",
        state="AZ",
    )

    mention = mention_factory(
        text="Target",
        source_text=(
            "I visited Target at "
            "5255 E Broadway Blvd "
            "in Tucson AZ."
        ),
    )

    candidates = (
        CandidateService.get_candidates(
            session=db_session,
            mention=mention,
            max_candidates=3,
        )
    )

    assert len(candidates) == 3

    assert (
        candidates[0]["business"].id
        == tucson_target.id
    )

    assert (
        candidates[0]["score"]
        > candidates[1]["score"]
    )


def test_max_candidates_is_respected(
    db_session,
    business_factory,
    mention_factory,
):

    for i in range(5):

        business_factory(
            business_id=f"coffee-{i}",
            name=f"Coffee House {i}",
            city="Tucson",
        )

    mention = mention_factory(
        text="Coffee House",
        source_text=(
            "I visited Coffee House in Tucson."
        ),
    )

    candidates = (
        CandidateService.get_candidates(
            session=db_session,
            mention=mention,
            max_candidates=2,
        )
    )

    assert len(candidates) == 2


def test_no_candidate_for_one_character_name(
    db_session,
    mention_factory,
):

    mention = mention_factory(
        text="A"
    )

    candidates = (
        CandidateService.get_candidates(
            session=db_session,
            mention=mention,
        )
    )

    assert candidates == []