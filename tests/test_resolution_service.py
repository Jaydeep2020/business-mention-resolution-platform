from types import SimpleNamespace

import pytest

from sqlalchemy import select

from app.models.resolution_result import (
    ResolutionResult,
)

from app.models.enums import (
    ResolutionDecision,
    ResolutionStatus,
)

from app.services.candidate_service import (
    CandidateService,
)

from app.services.resolution_service import (
    ResolutionService,
)

from app.services.document_service import (
    DocumentService,
)


# ==========================================================
# HELPER
# ==========================================================

def make_candidate(
    business,
    score,
):

    return {
        "business": business,
        "score": score,
        "name_score": score,
        "city_score": 1.0,
        "state_score": 1.0,
        "address_score": 1.0,
    }


# ==========================================================
# AUTO RESOLUTION
# ==========================================================

def test_high_confidence_verified_business_auto_resolves(
    db_session,
    business_factory,
    mention_factory,
    monkeypatch,
):

    business = business_factory(
        name="Target",
        is_verified=True,
    )

    mention = mention_factory(
        text="Target"
    )

    candidates = [
        make_candidate(
            business=business,
            score=0.95,
        )
    ]

    monkeypatch.setattr(
        CandidateService,
        "get_candidates",
        lambda **kwargs: candidates,
    )

    # We test document generation separately.
    # Here we only verify that resolution tries to create it.
    monkeypatch.setattr(
        DocumentService,
        "generate_resolution_summary",
        lambda **kwargs: SimpleNamespace(
            id=999
        ),
    )

    result = (
        ResolutionService.resolve_mention(
            session=db_session,
            mention_id=mention.id,
        )
    )

    db_session.refresh(
        mention
    )

    assert (
        mention.resolution_status
        == ResolutionStatus.AUTO_RESOLVED
    )

    assert (
        mention.resolved_business_id
        == business.id
    )

    assert (
        mention.confidence_score
        == 0.95
    )

    assert (
        result["document_id"]
        == 999
    )

    stored_result = (
        db_session.execute(
            select(ResolutionResult)
            .where(
                ResolutionResult.mention_id
                == mention.id
            )
        )
        .scalar_one()
    )

    assert (
        stored_result.decision
        == ResolutionDecision.AUTO
    )


# ==========================================================
# UNVERIFIED BUSINESS
# ==========================================================

def test_unverified_business_always_goes_to_review(
    db_session,
    business_factory,
    mention_factory,
    monkeypatch,
):

    business = business_factory(
        name="Target",
        is_verified=False,
    )

    mention = mention_factory(
        text="Target"
    )

    candidates = [
        make_candidate(
            business=business,
            score=0.99,
        )
    ]

    monkeypatch.setattr(
        CandidateService,
        "get_candidates",
        lambda **kwargs: candidates,
    )

    def should_not_generate_document(
        **kwargs,
    ):
        pytest.fail(
            "Summary must not be generated "
            "before successful resolution."
        )

    monkeypatch.setattr(
        DocumentService,
        "generate_resolution_summary",
        should_not_generate_document,
    )

    result = (
        ResolutionService.resolve_mention(
            session=db_session,
            mention_id=mention.id,
        )
    )

    db_session.refresh(
        mention
    )

    assert (
        mention.resolution_status
        == ResolutionStatus.SENT_FOR_REVIEWER
    )

    assert (
        mention.resolved_business_id
        is None
    )

    assert (
        result["document_id"]
        is None
    )

    stored_result = (
        db_session.execute(
            select(ResolutionResult)
            .where(
                ResolutionResult.mention_id
                == mention.id
            )
        )
        .scalar_one()
    )

    assert (
        stored_result.decision
        == ResolutionDecision.REVIEW
    )

    assert (
        "unverified"
        in stored_result.notes.lower()
    )


# ==========================================================
# BELOW CONFIDENCE THRESHOLD
# ==========================================================

def test_score_below_threshold_goes_to_review(
    db_session,
    business_factory,
    mention_factory,
    monkeypatch,
):

    business = business_factory(
        is_verified=True,
    )

    mention = mention_factory()

    # Current AUTO threshold = 0.85.
    candidates = [
        make_candidate(
            business=business,
            score=0.80,
        )
    ]

    monkeypatch.setattr(
        CandidateService,
        "get_candidates",
        lambda **kwargs: candidates,
    )

    result = (
        ResolutionService.resolve_mention(
            session=db_session,
            mention_id=mention.id,
        )
    )

    db_session.refresh(
        mention
    )

    assert (
        mention.resolution_status
        == ResolutionStatus.SENT_FOR_REVIEWER
    )

    assert (
        result["resolved_business_id"]
        is None
    )


# ==========================================================
# AMBIGUOUS CANDIDATES
# ==========================================================

def test_close_candidate_scores_go_to_review(
    db_session,
    business_factory,
    mention_factory,
    monkeypatch,
):

    business1 = business_factory(
        business_id="tonys-1",
        name="Tony's Pizza",
        is_verified=True,
    )

    business2 = business_factory(
        business_id="tonys-2",
        name="Tony's Pizza",
        is_verified=True,
    )

    mention = mention_factory(
        text="Tony's Pizza"
    )

    # Difference:
    #
    # 0.90 - 0.88 = 0.02
    #
    # AMBIGUITY_GAP = 0.05
    #
    # So it must be reviewed.
    candidates = [
        make_candidate(
            business1,
            0.90,
        ),
        make_candidate(
            business2,
            0.88,
        ),
    ]

    monkeypatch.setattr(
        CandidateService,
        "get_candidates",
        lambda **kwargs: candidates,
    )

    result = (
        ResolutionService.resolve_mention(
            session=db_session,
            mention_id=mention.id,
        )
    )

    db_session.refresh(
        mention
    )

    assert (
        mention.resolution_status
        == ResolutionStatus.SENT_FOR_REVIEWER
    )

    assert (
        result["resolved_business_id"]
        is None
    )

    stored_results = list(
        db_session.execute(
            select(ResolutionResult)
            .where(
                ResolutionResult.mention_id
                == mention.id
            )
        )
        .scalars()
        .all()
    )

    assert len(
        stored_results
    ) == 2

    assert (
        "similar"
        in stored_results[0].notes.lower()
    )


# ==========================================================
# REVIEWER APPROVAL
# ==========================================================

def test_reviewer_can_approve_candidate(
    db_session,
    business_factory,
    mention_factory,
    user_factory,
    monkeypatch,
):

    business1 = business_factory(
        business_id="candidate-1",
    )

    business2 = business_factory(
        business_id="candidate-2",
    )

    mention = mention_factory(
        resolution_status=(
            ResolutionStatus.SENT_FOR_REVIEWER
        ),
        confidence_score=0.80,
    )

    reviewer = user_factory()

    result1 = ResolutionResult(
        mention_id=mention.id,
        business_id=business1.id,
        score=0.80,
        decision=ResolutionDecision.REVIEW,
        notes="Sent for review because confidence was low.",
    )

    result2 = ResolutionResult(
        mention_id=mention.id,
        business_id=business2.id,
        score=0.78,
        decision=ResolutionDecision.REVIEW,
        notes="Candidate generated during automatic resolution.",
    )

    db_session.add_all(
        [
            result1,
            result2,
        ]
    )

    db_session.commit()

    db_session.refresh(
        result1
    )

    generated_for = []

    def fake_summary(
        **kwargs,
    ):

        generated_for.append(
            kwargs["mention_id"]
        )

        return SimpleNamespace(
            id=1
        )

    monkeypatch.setattr(
        DocumentService,
        "generate_resolution_summary",
        fake_summary,
    )

    approved_result = (
        ResolutionService.approve_resolution(
            session=db_session,
            result_id=result1.id,
            reviewer_id=reviewer.id,
            notes="Correct business confirmed.",
        )
    )

    db_session.refresh(
        mention
    )

    db_session.refresh(
        result2
    )

    assert (
        mention.resolution_status
        == ResolutionStatus.APPROVED
    )

    assert (
        mention.resolved_business_id
        == business1.id
    )

    assert (
        approved_result.decision
        == ResolutionDecision.APPROVED
    )

    assert (
        approved_result.reviewer_id
        == reviewer.id
    )

    assert (
        result2.decision
        == ResolutionDecision.REJECTED
    )

    assert generated_for == [
        mention.id
    ]


# ==========================================================
# REVIEWER REJECTION
# ==========================================================

def test_reviewer_can_reject_candidate(
    db_session,
    business_factory,
    mention_factory,
    user_factory,
):

    business = business_factory()

    mention = mention_factory(
        resolution_status=(
            ResolutionStatus.SENT_FOR_REVIEWER
        ),
        confidence_score=0.75,
    )

    reviewer = user_factory()

    resolution_result = ResolutionResult(
        mention_id=mention.id,
        business_id=business.id,
        score=0.75,
        decision=ResolutionDecision.REVIEW,
        notes="Sent for review because confidence was low.",
    )

    db_session.add(
        resolution_result
    )

    db_session.commit()

    db_session.refresh(
        resolution_result
    )

    result = (
        ResolutionService.reject_resolution(
            session=db_session,
            result_id=resolution_result.id,
            reviewer_id=reviewer.id,
            notes="Not the correct business.",
        )
    )

    db_session.refresh(
        mention
    )

    assert (
        mention.resolution_status
        == ResolutionStatus.REJECTED
    )

    assert (
        mention.resolved_business_id
        is None
    )

    assert (
        result.decision
        == ResolutionDecision.REJECTED
    )

    assert (
        result.reviewer_id
        == reviewer.id
    )