"""Human Review Queue view for reviewing, approving, and rejecting escalated mention candidates."""

import pandas as pd
import streamlit as st

from frontend.api_client import ApiError
from frontend.state import get_api_client, has_role
from frontend.utils.ui_helpers import (
    render_header,
    render_pagination_bar,
    render_score_pill,
)


def render_review_queue_view() -> None:
    """Render Human Review Queue interface."""
    render_header(
        title="Human Review Queue",
        subtitle="Review ambiguous, low-confidence, or unverified business candidates and make final resolution decisions",
        icon="⚖️",
    )

    client = get_api_client()
    is_reviewer = has_role("reviewer", "admin")

    if not is_reviewer:
        st.warning("Reviewer or Admin role is required to access and approve items in the review queue.")
        return

    # Pagination controls
    if "rq_page" not in st.session_state:
        st.session_state["rq_page"] = 1

    p_col1, p_col2 = st.columns([3, 1])
    with p_col2:
        page_size = st.selectbox("Page Size", options=[10, 20, 50], index=1, key="rq_page_size")

    # Fetch review queue items
    try:
        with st.spinner("Fetching review queue..."):
            resp = client.get_review_queue(page=st.session_state["rq_page"], page_size=page_size)
            items = resp.get("items", [])
            total = resp.get("total", 0)
            total_pages = resp.get("total_pages", 1)
            current_page = resp.get("page", 1)

        st.markdown(f"**Items awaiting human decision: {total:,}** (Page {current_page} of {max(1, total_pages)})")

        if items:
            # Group items by mention_id for organized reviewing
            mentions_map = {}
            for item in items:
                m_id = item.get("mention_id")
                if m_id not in mentions_map:
                    mentions_map[m_id] = []
                mentions_map[m_id].append(item)

            st.markdown("##### 📌 Pending Mention Review Cards")

            for m_id, candidates in mentions_map.items():
                # Attempt to get mention text
                mention_text_preview = f"Mention #{m_id}"
                source_preview = ""
                try:
                    m_data = client.get_mention(m_id)
                    mention_text_preview = f"Mention #{m_id}: \"{m_data.get('text')}\""
                    source_preview = m_data.get("source_text") or ""
                except Exception:
                    pass

                with st.container():
                    st.markdown(
                        f"""
                        <div style="background: rgba(30, 41, 59, 0.4); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 10px; padding: 14px 18px; margin-bottom: 16px;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <h4 style="margin: 0; color: #f59e0b;">{mention_text_preview}</h4>
                                <span style="background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.4); padding: 3px 10px; border-radius: 9999px; font-size: 0.8rem; font-weight: 600;">
                                    {len(candidates)} Candidate{'s' if len(candidates) > 1 else ''}
                                </span>
                            </div>
                            {f'<div style="margin-top: 6px; color: #cbd5e1; font-size: 0.88rem; font-style: italic;">"{source_preview}"</div>' if source_preview else ''}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    # List candidates for this mention
                    for cand in candidates:
                        res_id = cand.get("id")
                        biz_id = cand.get("business_id")
                        score = cand.get("score", 0)
                        notes = cand.get("notes") or "No notes provided."

                        # Fetch business details
                        biz_name = f"Business #{biz_id}"
                        biz_loc = ""
                        try:
                            b_info = client.get_business(biz_id)
                            biz_name = b_info.get("name")
                            biz_loc = f"{b_info.get('address') or ''}, {b_info.get('city') or ''}, {b_info.get('state') or ''}"
                        except Exception:
                            pass

                        c_box1, c_box2 = st.columns([3, 2])

                        with c_box1:
                            st.markdown(
                                f"""
                                <div style="background: rgba(255, 255, 255, 0.02); border-left: 3px solid #3b82f6; padding: 10px 14px; border-radius: 0 6px 6px 0;">
                                    <div style="font-weight: 600; font-size: 1rem; color: #60a5fa;">{biz_name} (ID #{biz_id})</div>
                                    <div style="color: #94a3b8; font-size: 0.85rem; margin-top: 2px;">{biz_loc}</div>
                                    <div style="margin-top: 4px;">Score: {render_score_pill(score)}</div>
                                    <div style="color: #cbd5e1; font-size: 0.82rem; margin-top: 4px;"><b>Note:</b> {notes}</div>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

                        with c_box2:
                            reviewer_note = st.text_input(
                                "Reviewer Note",
                                placeholder="Optional note for decision...",
                                key=f"note_res_{res_id}",
                                label_visibility="collapsed",
                            )

                            b_col_app, b_col_rej = st.columns(2)
                            with b_col_app:
                                if st.button("✅ Approve", key=f"app_btn_{res_id}", type="primary", use_container_width=True):
                                    with st.spinner("Approving candidate..."):
                                        try:
                                            client.approve_resolution(result_id=res_id, notes=reviewer_note)
                                            st.success(f"Candidate #{res_id} approved for Mention #{m_id}!")
                                            st.rerun()
                                        except ApiError as e:
                                            st.error(f"Approval failed: {e.message}")

                            with b_col_rej:
                                if st.button("❌ Reject", key=f"rej_btn_{res_id}", use_container_width=True):
                                    with st.spinner("Rejecting candidate..."):
                                        try:
                                            client.reject_resolution(result_id=res_id, notes=reviewer_note)
                                            st.success(f"Candidate #{res_id} rejected!")
                                            st.rerun()
                                        except ApiError as e:
                                            st.error(f"Rejection failed: {e.message}")

                    st.markdown("<hr style='border-color: rgba(255,255,255,0.05);'>", unsafe_allow_html=True)

            # Pagination
            new_page = render_pagination_bar(current_page=current_page, total_pages=total_pages, key_prefix="rq_pag")
            if new_page != current_page:
                st.session_state["rq_page"] = new_page
                st.rerun()

        else:
            st.success("🎉 Fantastic! The human review queue is completely clear. No pending items.")

    except ApiError as e:
        st.error(f"Failed to load review queue: {e.message}")
