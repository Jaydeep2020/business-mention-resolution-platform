# Requirement 17


import json

from fastapi import HTTPException, status

from app.core.llm import get_qa_llm
from app.schemas.qa import CatalogQueryPlan


class LLMService:

    # ======================================================
    # QUESTION → SAFE QUERY PLAN
    # ======================================================

    @staticmethod
    def create_catalog_query_plan(question: str) -> CatalogQueryPlan:

        try:

            llm = get_qa_llm()

            structured_llm = llm.with_structured_output(CatalogQueryPlan, method="json_schema")

            system_prompt = """
You convert natural-language questions about a local
business catalog into a SAFE structured query plan.

You are NOT allowed to write SQL.

Available catalog information:
- business name
- city
- state
- category
- verified/unverified status
- resolved mention counts

Supported intents:

1. list_businesses
   Examples:
   - Show pizza restaurants in Tucson.
   - List verified cafes in Philadelphia.

2. count_businesses
   Examples:
   - How many Starbucks locations are in the catalog?
   - How many cafes are in Tucson?

3. top_by_mentions
   Examples:
   - Which cafes have the most mentions?
   - Show the most mentioned restaurants in Tucson.

4. business_details
   Examples:
   - Tell me about Starbucks in Tucson.
   - Find Tony's Pizza.

5. unsupported
   Use when the question cannot be answered from the
   available business catalog data.

Important rules:

- Extract only information explicitly stated by the user.
- Do not invent a city, state, category or business name.
- "near me", "this area", "around here", etc. require
  clarification because no user location is available.
- If important information is missing, set
  needs_clarification=true.
- Put the question to ask the user into
  clarification_question.
- limit should normally be 5.
- limit must never exceed 20.
"""

            messages = [
                (
                    "system",
                    system_prompt,
                ),
                (
                    "human",
                    question,
                ),
            ]

            plan = (
                structured_llm.invoke(messages)
            )

            return plan

        except HTTPException:

            raise

        except Exception as exc:

            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "Question understanding service "
                    "is currently unavailable."
                ),
            ) from exc


    # ======================================================
    # DATABASE RESULTS → NATURAL ANSWER
    # ======================================================

    @staticmethod
    def generate_grounded_answer(question: str, plan: CatalogQueryPlan, database_result: dict) -> str:

        try:
            llm = get_qa_llm()

            system_prompt = """
You answer questions about a business catalog.

You MUST use only the DATABASE RESULT provided to you.

Do not use your own knowledge about businesses.

Do not invent:
- businesses
- locations
- categories
- mention counts
- IDs
- verification status

If the database result contains no matching records,
say that no matching catalog records were found.

When business records are present, mention business names
naturally. Do not claim information that is absent from
the database result.

Keep the answer concise and useful.
"""

            payload = {
                "question": question,
                "query_plan": (plan.model_dump()),
                "database_result": database_result,
            }

            messages = [
                (
                    "system",
                    system_prompt,
                ),
                (
                    "human",
                    json.dumps(payload,ensure_ascii=False,default=str),
                ),
            ]

            response = llm.invoke(messages)

            # Newer LangChain messages expose .text.
            response_text = getattr(response, "text", None)

            if response_text:

                return str(response_text).strip()

            # Safe fallback.
            if isinstance(response.content, str):

                return response.content.strip()

            return str(response.content).strip()

        except Exception as exc:

            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "Answer generation service "
                    "is currently unavailable."
                ),
            ) from exc