"""Catalog Question Answering view enabling natural language queries over enterprise business data."""

import pandas as pd
import streamlit as st

from frontend.api_client import ApiError
from frontend.state import get_api_client
from frontend.utils.mock_data import SAMPLE_QA_QUESTIONS
from frontend.utils.ui_helpers import render_header, render_metric_card


def render_qa_view() -> None:
    """Render Catalog Q&A natural language assistant interface."""
    render_header(
        title="Catalog Question Answering",
        subtitle="Ask natural-language questions about businesses, locations, categories, and mention metrics",
        icon="💬",
    )

    client = get_api_client()

    # Sample query chips
    st.markdown("##### 💡 Example Questions")
    sample_cols = st.columns(len(SAMPLE_QA_QUESTIONS))
    for idx, q in enumerate(SAMPLE_QA_QUESTIONS):
        with sample_cols[idx]:
            if st.button(q, key=f"qa_sample_{idx}", use_container_width=True):
                st.session_state["qa_input_text"] = q
                st.rerun()

    # Question Input
    st.markdown("##### ❓ Ask a Question")
    default_q = st.session_state.get("qa_input_text", "Show me restaurants in Santa Barbara")

    with st.form("qa_form"):
        user_question = st.text_input(
            "Natural Language Query",
            value=default_q,
            placeholder="e.g. Find top businesses in Philadelphia, What bakeries are in Boise?",
        )
        ask_btn = st.form_submit_button("Ask Catalog AI", type="primary", use_container_width=True)

    if ask_btn:
        if not user_question.strip():
            st.error("Please enter a question to ask.")
        else:
            with st.spinner("Translating question to structured query plan and analyzing catalog..."):
                try:
                    resp = client.ask_catalog_question(user_question.strip())
                    st.session_state["last_qa_result"] = resp
                except ApiError as e:
                    st.error(f"Failed to answer question: {e.message}")
                except Exception as e:
                    st.error(f"Unexpected error: {str(e)}")

    # Display Answer & Referenced Data
    if "last_qa_result" in st.session_state:
        res = st.session_state["last_qa_result"]

        st.markdown("---")
        st.markdown("### 🤖 Answer & Analysis")

        # Intent and Stats
        m1, m2, m3 = st.columns([1.5, 1.5, 3])
        with m1:
            render_metric_card("Query Intent", res.get("intent", "general").replace("_", " ").title(), "Structured plan", "🎯")
        with m2:
            render_metric_card("Catalog Records", res.get("records_used", 0), "Entities referenced", "📚")
        with m3:
            st.markdown(
                f"""
                <div style="background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 10px; padding: 12px 16px;">
                    <div style="font-size: 0.8rem; color: #94a3b8;">ORIGINAL QUERY</div>
                    <div style="color: #cbd5e1; font-weight: 500; margin-top: 4px;">"{res.get('question')}"</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)

        # Clarification prompt if any
        if res.get("needs_clarification"):
            st.warning(f"⚠️ **Clarification Requested:** {res.get('clarification_question')}")

        # Natural Language Answer
        st.markdown("##### 📝 Summary Answer")
        st.markdown(
            f"""
            <div style="background: rgba(30, 41, 59, 0.5); border-left: 4px solid #10b981; border-radius: 0 8px 8px 0; padding: 16px 20px; font-size: 1rem; color: #f1f5f9; line-height: 1.6;">
                {res.get('answer', 'No answer produced.')}
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Referenced Records
        references = res.get("references", [])
        if references:
            st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
            st.markdown("##### 🏢 Referenced Catalog Businesses")

            ref_rows = []
            for r in references:
                ref_rows.append(
                    {
                        "DB ID": r.get("business_id"),
                        "Catalog ID": r.get("catalog_business_id"),
                        "Business Name": r.get("business_name"),
                        "City": r.get("city") or "—",
                        "State": r.get("state") or "—",
                        "Mention Count": r.get("mention_count") if r.get("mention_count") is not None else "—",
                    }
                )
            st.dataframe(pd.DataFrame(ref_rows), use_container_width=True, hide_index=True)
