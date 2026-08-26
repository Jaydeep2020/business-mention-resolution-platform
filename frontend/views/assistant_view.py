"""Smart AI Assistant view powered by LangGraph to resolve business mentions using hybrid rules & LLM reasoning."""

import pandas as pd
import streamlit as st

from frontend.api_client import ApiError
from frontend.state import get_api_client, has_role
from frontend.utils.ui_helpers import (
    render_header,
    render_metric_card,
    render_score_pill,
)


def render_assistant_view() -> None:
    """Render Smart AI Assistant resolution interface."""
    render_header(
        title="Smart AI Assistant",
        subtitle="Intelligent mention resolution pipeline combining fuzzy matching, vector embeddings, validation policies, and LLM reasoning",
        icon="🤖",
    )

    client = get_api_client()
    is_reviewer = has_role("reviewer", "admin")

    if not is_reviewer:
        st.warning("Reviewer or Admin role is required to run the Smart AI Assistant.")
        return

    # Load pending or review mentions for easy dropdown selection
    pending_mentions = []
    try:
        m_resp = client.get_mentions(page=1, page_size=50)
        pending_mentions = [
            m for m in m_resp.get("items", []) if m.get("resolution_status") in ["pending", "sent_for_reviewer"]
        ]
    except Exception:
        pass

    # Mention Selection Controls
    st.markdown("##### 🎯 Target Mention Selection")
    c1, c2, c3 = st.columns([2, 1, 1])

    with c1:
        mention_options = {
            f"#{m.get('id')} — '{m.get('text')}' (Status: {m.get('resolution_status')})": m.get("id")
            for m in pending_mentions
        }

        # Check if pre-selected from another page
        preselected_id = st.session_state.get("selected_mention_id")
        selected_index = 0
        if preselected_id:
            for idx, (label, m_id) in enumerate(mention_options.items()):
                if m_id == preselected_id:
                    selected_index = idx
                    break

        if mention_options:
            chosen_mention_label = st.selectbox(
                "Choose from Pending / Review Mentions:",
                options=list(mention_options.keys()),
                index=selected_index,
                key="assistant_mention_select",
            )
            selected_mention_id = mention_options[chosen_mention_label]
        else:
            selected_mention_id = None
            st.info("No pending mentions currently available in the database.")

    with c2:
        manual_id = st.number_input(
            "Or Enter Mention ID Manually",
            min_value=1,
            value=int(selected_mention_id or 1),
            step=1,
            key="assistant_manual_id",
        )
        target_id = manual_id if manual_id else selected_mention_id

    with c3:
        max_candidates = st.slider(
            "Max Candidates",
            min_value=2,
            max_value=10,
            value=5,
            help="Number of candidate business matches to retrieve and evaluate.",
        )

    # Resolution Trigger
    run_btn = st.button("🚀 Run Smart Resolution Pipeline", type="primary", use_container_width=True)

    if run_btn:
        if not target_id:
            st.error("Please specify a valid Mention ID.")
        else:
            with st.spinner(f"Executing LangGraph workflow on Mention #{target_id}... (Retrieving candidates, calculating embeddings, evaluating policies & LLM reasoning)"):
                try:
                    result = client.smart_resolve_mention(mention_id=int(target_id), max_candidates=max_candidates)
                    st.session_state["last_assistant_result"] = result
                    st.success(f"Assistant evaluation completed for Mention #{target_id}!")
                except ApiError as e:
                    st.error(f"Smart Assistant resolution failed: {e.message}")
                except Exception as e:
                    st.error(f"Unexpected error: {str(e)}")

    # Display Results
    if "last_assistant_result" in st.session_state:
        res = st.session_state["last_assistant_result"]

        st.markdown("---")
        st.markdown("### 📋 Resolution Results & Decision Breakdown")

        action = res.get("action", "escalated")
        is_resolved = action == "resolved"

        # Action banner
        action_bg = "rgba(16, 185, 129, 0.15)" if is_resolved else "rgba(245, 158, 11, 0.15)"
        action_border = "#10b981" if is_resolved else "#f59e0b"
        action_text_color = "#34d399" if is_resolved else "#fbbf24"
        action_title = "✅ AUTOMATICALLY RESOLVED" if is_resolved else "⚠️ ESCALATED FOR HUMAN REVIEW"

        st.markdown(
            f"""
            <div style="background: {action_bg}; border: 1px solid {action_border}; border-radius: 10px; padding: 16px 20px; margin-bottom: 20px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <h3 style="margin: 0; color: {action_text_color}; font-weight: 700;">{action_title}</h3>
                    <span style="background: rgba(255, 255, 255, 0.1); padding: 4px 12px; border-radius: 9999px; font-size: 0.85rem; font-weight: 600;">
                        Source: {res.get('decision_source', 'N/A').upper()}
                    </span>
                </div>
                <div style="margin-top: 10px; font-size: 1.05rem; color: #f1f5f9;">
                    <b>Mention Text:</b> "{res.get('mention_text')}" (ID #{res.get('mention_id')})
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Core metric tiles
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        with m_col1:
            render_metric_card(
                "Assistant Confidence",
                f"{round(res.get('assistant_confidence', 0) * 100, 1)}%" if res.get("assistant_confidence") is not None else "N/A",
                "Model confidence",
                "🎯",
            )
        with m_col2:
            render_metric_card(
                "Best Candidate Score",
                f"{round(res.get('candidate_score', 0) * 100, 1)}%" if res.get("candidate_score") is not None else "N/A",
                "Hybrid matcher",
                "⭐",
            )
        with m_col3:
            render_metric_card(
                "Score Gap",
                f"{res.get('score_gap'):.4f}" if res.get("score_gap") is not None else "N/A",
                "Margin over #2 candidate",
                "📏",
            )
        with m_col4:
            ambig_str = "⚠️ Yes (High)" if res.get("ambiguous") else "✅ No (Clear)"
            render_metric_card("Ambiguous Match", ambig_str, "Similarity gap check", "⚖️")

        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)

        # Explanation & Reasoning Note
        st.markdown("##### 🧠 Assistant Explanation & Reasoning")
        st.markdown(
            f"""
            <div style="background: rgba(30, 41, 59, 0.6); border-left: 4px solid #38bdf8; border-radius: 0 8px 8px 0; padding: 14px 18px; color: #e2e8f0; font-size: 0.95rem; line-height: 1.5;">
                {res.get('note', 'No note provided.')}
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Workflow execution timeline
        workflow_steps = res.get("workflow_steps", [])
        if workflow_steps:
            st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
            st.markdown("##### 🔄 LangGraph Execution Timeline")
            for idx, step in enumerate(workflow_steps, 1):
                st.markdown(
                    f"""
                    <div class="step-card">
                        <div style="background: #10b981; color: white; border-radius: 50%; width: 22px; height: 22px; display: flex; align-items: center; justify-content: center; font-size: 0.75rem; font-weight: 700; flex-shrink: 0;">{idx}</div>
                        <div style="color: #cbd5e1; font-size: 0.9rem;">{step}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        # Candidate ranking cards / breakdown
        candidates = res.get("candidates", [])
        if candidates:
            st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
            st.markdown("##### 🏆 Evaluated Candidate Businesses")

            for rank, cand in enumerate(candidates, 1):
                is_selected = cand.get("business_id") == res.get("resolved_business_id")
                card_border = "#10b981" if is_selected else "rgba(255,255,255,0.1)"
                badge_selected = '<span style="background: #10b981; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600; margin-left: 8px;">MATCHED RESOLUTION</span>' if is_selected else ""

                with st.expander(
                    f"#{rank} — {cand.get('business_name')} (Score: {round(cand.get('score', 0) * 100, 1)}%) { '✅' if is_selected else ''}",
                    expanded=(rank == 1),
                ):
                    st.markdown(
                        f"""
                        <div style="padding: 10px; border-left: 3px solid {card_border};">
                            <h4 style="margin: 0; color: #60a5fa;">{cand.get('business_name')} {badge_selected}</h4>
                            <p style="margin: 4px 0; color: #94a3b8; font-size: 0.85rem;">
                                <b>DB ID:</b> {cand.get('business_id')} | <b>Catalog ID:</b> {cand.get('catalog_business_id')} | 
                                <b>Verified:</b> {'✅ Yes' if cand.get('is_verified') else '❌ No'} | 
                                <b>Location:</b> {cand.get('address') or 'N/A'}, {cand.get('city') or 'N/A'}, {cand.get('state') or 'N/A'}
                            </p>
                            <p style="margin: 4px 0; color: #cbd5e1; font-size: 0.85rem;">
                                <b>Categories:</b> {', '.join(cand.get('categories', [])) or 'None'}
                            </p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    # Score Breakdown
                    st.markdown("###### Similarity Score Components")
                    sc1, sc2, sc3, sc4, sc5, sc6 = st.columns(6)
                    with sc1:
                        st.metric("Total Score", f"{cand.get('score', 0):.4f}")
                    with sc2:
                        st.metric("Name Sim", f"{cand.get('name_score', 0):.4f}")
                    with sc3:
                        emb_s = cand.get("embedding_score")
                        st.metric("Vector Sim", f"{emb_s:.4f}" if emb_s is not None else "N/A")
                    with sc4:
                        st.metric("City Sim", f"{cand.get('city_score', 0):.4f}")
                    with sc5:
                        st.metric("State Sim", f"{cand.get('state_score', 0):.4f}")
                    with sc6:
                        st.metric("Address Sim", f"{cand.get('address_score', 0):.4f}")
