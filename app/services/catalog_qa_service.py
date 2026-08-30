# The LLM interprets the question, but this service controls all database queries.

## It can Access : Businesses, Categories, Mentions tables from DB

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.models.business import Business

from app.models.category import Category
from app.models.mention import Mention
from app.models.enums import ResolutionStatus

from app.schemas.qa import CatalogQuestionRequest, CatalogQueryPlan

from app.services.llm_service import LLMService


class CatalogQAService:

    SUCCESSFUL_MENTION_STATUSES = [
        ResolutionStatus.AUTO_RESOLVED,
        ResolutionStatus.APPROVED,
    ]


    # ======================================================
    # BUILD SAFE BUSINESS FILTERS
    # ======================================================

    @staticmethod
    def build_business_filters(plan: CatalogQueryPlan) -> list:

        filters = []

        # --------------------------------------------------
        # Business name
        # --------------------------------------------------

        if plan.business_name:

            business_name = plan.business_name.strip()

            if business_name:

                filters.append(Business.name.ilike(f"%{business_name}%"))

        # --------------------------------------------------
        # City
        # --------------------------------------------------

        if plan.city:

            city = plan.city.strip()

            if city:

                filters.append(Business.city.ilike(city))

        # --------------------------------------------------
        # State
        # --------------------------------------------------

        if plan.state:

            state = plan.state.strip()

            if state:

                filters.append(Business.state.ilike(state))

        # --------------------------------------------------
        # Verified
        # --------------------------------------------------

        if plan.is_verified is not None:

            filters.append(Business.is_verified == plan.is_verified)

        # --------------------------------------------------
        # Category
        #
        # .any() creates an EXISTS-style condition.
        # This avoids duplicate businesses from joins.
        # --------------------------------------------------

        if plan.category:

            category = plan.category.strip()

            if category:

                filters.append(Business.categories.any(Category.name.ilike(f"%{category}%")))

        return filters


    # ======================================================
    # LIMIT
    # ======================================================

    @staticmethod
    def get_safe_limit(plan: CatalogQueryPlan) -> int:

        requested_limit = (plan.limit or 5)

        return min( max(1, requested_limit), settings.QA_MAX_RESULTS, 20)


    # ======================================================
    # BUSINESS → RESPONSE DICT
    # ======================================================

    @staticmethod
    def business_to_dict(business: Business) -> dict:

        return {
            "business_id": business.id,
            "catalog_business_id": business.business_id,
            "business_name": business.name,
            "address": business.address,
            "city": business.city,
            "state": business.state,
            "postal_code": business.postal_code,
            "is_verified": business.is_verified,
            "categories": [
                category.name for category in business.categories
            ],
        }


    # ======================================================
    # LIST BUSINESSES
    # ======================================================

    @classmethod
    def query_businesses(cls, session: Session, plan: CatalogQueryPlan) -> dict:

        filters = cls.build_business_filters(plan)

        limit = cls.get_safe_limit(plan)

        stmt = (
            select(Business).options(selectinload(Business.categories))
        )

        if filters:
            stmt = stmt.where(*filters)

        stmt = (
            stmt.order_by(Business.name.asc()).limit(limit)
        )

        businesses = list(
            session.execute(stmt).scalars().unique().all()
        )

        records = [
            cls.business_to_dict(business) for business in businesses
        ]

        return {
            "type": "business_list",
            "count": len(records),
            "records": records,
        }


    # ======================================================
    # COUNT BUSINESSES
    # ======================================================

    @classmethod
    def count_businesses(cls, session: Session, plan: CatalogQueryPlan) -> dict:

        filters = cls.build_business_filters(plan)

        stmt = select(func.count(Business.id))

        if filters:
            stmt = stmt.where(*filters)

        count = (
            session.execute(stmt).scalar_one()
        )

        return {
            "type": "business_count",
            "count": int(count),
            "records": [],
        }


    # ======================================================
    # TOP BUSINESSES BY RESOLVED MENTIONS
    # ======================================================

    @classmethod
    def top_businesses_by_mentions(cls, session: Session, plan: CatalogQueryPlan) -> dict:

        filters = cls.build_business_filters(plan)

        limit = cls.get_safe_limit(plan)

        mention_count = (
            func.count(Mention.id).label("mention_count")
        )

        # Join only successfully resolved mentions.
        mention_join_condition = and_(
            Mention.resolved_business_id == Business.id,

            Mention.resolution_status.in_(cls.SUCCESSFUL_MENTION_STATUSES),
        )

        stmt = (
            select(
                Business.id,
                Business.business_id,
                Business.name,
                Business.address,
                Business.city,
                Business.state,
                Business.postal_code,
                Business.is_verified,
                mention_count,
            )
            .outerjoin(
                Mention,
                mention_join_condition,
            )
        )

        if filters:

            stmt = stmt.where(*filters)

        stmt = (
            stmt
            .group_by(
                Business.id,
                Business.business_id,
                Business.name,
                Business.address,
                Business.city,
                Business.state,
                Business.postal_code,
                Business.is_verified,
            )
            .order_by(
                mention_count.desc(),
                Business.name.asc(),
            )
            .limit(limit)
        )

        rows = (
            session.execute(
                stmt
            )
            .all()
        )

        records = []

        for row in rows:

            records.append(
                {
                    "business_id": row.id,
                    "catalog_business_id": row.business_id,
                    "business_name": row.name,
                    "address": row.address,
                    "city": row.city,
                    "state": row.state,
                    "postal_code": row.postal_code,
                    "is_verified": row.is_verified,
                    "mention_count": int(row.mention_count),
                }
            )

        return {
            "type": "top_by_mentions",
            "count": len(records),
            "records": records,
        }


    # ======================================================
    # EXECUTE QUERY PLAN
    # ======================================================

    @classmethod
    def execute_plan(cls, session: Session, plan: CatalogQueryPlan) -> dict:

        if plan.intent == "count_businesses":
            return (
                cls.count_businesses(session=session, plan=plan)
            )


        if plan.intent == "top_by_mentions":
            return cls.top_businesses_by_mentions(session=session, plan=plan)


        if plan.intent in {"list_businesses", "business_details"}:
            return cls.query_businesses(session=session, plan=plan)


        return {
            "type": "unsupported",
            "count": 0,
            "records": [],
        }


    # ======================================================
    # CREATE REFERENCES
    # ======================================================

    @staticmethod
    def create_references(database_result: dict) -> list[dict]:

        references = []

        for record in (database_result.get("records", [],)):

            references.append(
                {
                    "business_id": record["business_id"],
                    "catalog_business_id": record["catalog_business_id"],
                    "business_name": record["business_name"],
                    "city": record.get("city"),
                    "state": record.get("state"),
                    "mention_count": record.get("mention_count"),
                }
            )

        return references


    # ======================================================
    # ASK QUESTION
    # ======================================================

    @classmethod
    def ask_question(cls, session: Session, data: CatalogQuestionRequest) -> dict:

        question = data.question.strip()

        # --------------------------------------------------
        # 1. Understand question
        # --------------------------------------------------

        plan = LLMService.create_catalog_query_plan(question)

        # --------------------------------------------------
        # 2. Clarification required
        # --------------------------------------------------

        if plan.needs_clarification:

            clarification = (
                plan.clarification_question
                or (
                    "Please provide more information "
                    "so I can query the catalog."
                )
            )

            return {
                "question": question,
                "answer": clarification,
                "intent": plan.intent,
                "records_used": 0,
                "references": [],
                "needs_clarification": True,
                "clarification_question": (
                    clarification
                ),
            }

        # --------------------------------------------------
        # 3. Unsupported question
        # --------------------------------------------------

        if plan.intent == "unsupported":

            return {
                "question": question,
                "answer": (
                    "This question cannot be answered "
                    "from the available business catalog "
                    "data."
                ),
                "intent": (
                    plan.intent
                ),
                "records_used": 0,
                "references": [],
                "needs_clarification": False,
                "clarification_question": None,
            }

        # --------------------------------------------------
        # 4. Query PostgreSQL
        # --------------------------------------------------

        database_result = cls.execute_plan(session=session,plan=plan)


        # --------------------------------------------------
        # 5. No records
        # --------------------------------------------------

        if database_result["type"] != "business_count" and not database_result["records"]:

            return {
                "question": question,
                "answer": (
                    "I couldn't find catalog records "
                    "matching that question."
                ),
                "intent": plan.intent,
                "records_used": 0,
                "references": [],
                "needs_clarification": False,
                "clarification_question": None,
            }

        # --------------------------------------------------
        # 6. Generate answer using ONLY DB result
        # --------------------------------------------------

        answer = LLMService.generate_grounded_answer(question=question, plan=plan, database_result=database_result)


        # --------------------------------------------------
        # 7. Record references
        # --------------------------------------------------

        references = cls.create_references(database_result)

        if database_result["type"] == "business_count":

            records_used = int(database_result["count"])

        else:

            records_used = len(database_result["records"])

        return {
            "question": question,
            "answer": answer,
            "intent": plan.intent,
            "records_used": (
                records_used
            ),
            "references": references,
            "needs_clarification": False,
            "clarification_question": None,
        }