"""Mentions management view supporting creation, listing, status filtering, and resolution triggering."""

import pandas as pd
import streamlit as st

from frontend.api_client import ApiError
from frontend.state import get_api_client, has_role
from frontend.utils.ui_helpers import (
    render_header,
    render_pagination_bar,
    render_score_pill,
    render_status_badge,
)


def render_mentions_view() -> None:
    """Render Mentions list and resolution interface."""
    render_header(
        title="Business Mentions",
        subtitle="Track extracted mentions, view resolution confidence, and resolve against business catalog",
        icon="🏷️",
    )

    client = get_api_client()
    is_admin = has_role("admin")
    is_reviewer = has_role("reviewer", "admin")

    tab_list, tab_create = st.tabs(["📋 Mentions Explorer", "➕ Ingest New Mention"])

    # ------------------------------------------------------------------
    # TAB 1: Mentions Explorer
    # ------------------------------------------------------------------
    with tab_list:
        # Search & Filter
        f_col1, f_col2, f_col3 = st.columns([2, 1.5, 1])

        with f_col1:
            search_query = st.text_input(
                "Search Mention Text",
                placeholder="e.g. Magnolia, Joe's Pizza...",
                key="m_search_input",
            )
        with f_col2:
            status_options = ["All", "pending", "auto_resolved", "sent_for_reviewer", "approved", "rejected"]
            status_filter = st.selectbox(
                "Resolution Status",
                options=status_options,
                key="m_status_select",
            )
        with f_col3:
            page_size = st.selectbox("Page Size", options=[10, 20, 50], index=1, key="m_page_size")

        if "m_page" not in st.session_state:
            st.session_state["m_page"] = 1

        try:
            with st.spinner("Loading mentions..."):
                resp = client.get_mentions(
                    page=st.session_state["m_page"],
                    page_size=page_size,
                    search=search_query.strip() if search_query else None,
                    status_filter=status_filter if status_filter != "All" else None,
                )

                items = resp.get("items", [])
                total = resp.get("total", 0)
                total_pages = resp.get("total_pages", 1)
                current_page = resp.get("page", 1)

            st.markdown(f"**Found {total:,} mentions** (Page {current_page} of {max(1, total_pages)})")

            if items:
                table_rows = []
                for m in items:
                    table_rows.append(
                        {
                            "ID": m.get("id"),
                            "Mention Text": m.get("text"),
                            "Status": m.get("resolution_status", "").upper(),
                            "Confidence": f"{round(m.get('confidence_score') * 100, 1)}%" if m.get("confidence_score") else "—",
                            "Resolved Business ID": m.get("resolved_business_id") or "—",
                            "Source Type": m.get("source_type"),
                            "Source Text": (m.get("source_text") or "—")[:80] + ("..." if len(m.get("source_text") or "") > 80 else ""),
                        }
                    )

                st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)

                new_page = render_pagination_bar(
                    current_page=current_page,
                    total_pages=total_pages,
                    key_prefix="m_pag",
                )
                if new_page != current_page:
                    st.session_state["m_page"] = new_page
                    st.rerun()

                # Mention Inspection & Resolution Action Hub
                st.markdown("---")
                st.markdown("##### ⚡ Mention Details & Resolution Hub")

                m_lookup = {f"#{m.get('id')} — '{m.get('text')}' ({m.get('resolution_status')})": m for m in items}
                sel_m_col1, sel_m_col2 = st.columns([1.5, 2])

                with sel_m_col1:
                    selected_m_str = st.selectbox(
                        "Select a mention to inspect:",
                        options=list(m_lookup.keys()),
                        key="selected_m_inspect",
                    )
                    selected_m = m_lookup[selected_m_str]

                with sel_m_col2:
                    st.markdown(
                        f"""
                        <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; padding: 14px;">
                            <h4 style="margin: 0; color: #38bdf8;">Mention #{selected_m.get('id')}: "{selected_m.get('text')}"</h4>
                            <p style="margin: 6px 0; font-size: 0.9rem;">
                                <b>Status:</b> {render_status_badge(selected_m.get('resolution_status'))} &nbsp;&nbsp;|&nbsp;&nbsp; 
                                <b>Confidence:</b> {render_score_pill(selected_m.get('confidence_score'))}
                            </p>
                            <p style="margin: 6px 0; color: #cbd5e1; font-size: 0.88rem;">
                                <b>Source Context:</b> <i>"{selected_m.get('source_text') or 'N/A'}"</i>
                            </p>
                            <p style="margin: 4px 0; color: #94a3b8; font-size: 0.85rem;">
                                <b>Resolved Business ID:</b> {selected_m.get('resolved_business_id') or 'None'}
                            </p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                # Action buttons
                act_c1, act_c2, act_c3 = st.columns(3)

                with act_c1:
                    if is_reviewer and selected_m.get("resolution_status") == "pending":
                        if st.button("⚡ Run Standard Resolution", key=f"std_res_{selected_m.get('id')}", use_container_width=True):
                            with st.spinner("Executing rule-based resolution pipeline..."):
                                try:
                                    res = client.resolve_mention(selected_m.get("id"), max_candidates=5)
                                    st.success(
                                        f"Resolution complete! Status: **{res.get('resolution_status')}** (Confidence: {res.get('confidence_score')})"
                                    )
                                    st.rerun()
                                except ApiError as e:
                                    st.error(f"Resolution failed: {e.message}")

                with act_c2:
                    if is_reviewer:
                        if st.button("🤖 Send to Smart AI Assistant", key=f"smart_res_{selected_m.get('id')}", use_container_width=True, type="primary"):
                            st.session_state["selected_mention_id"] = selected_m.get("id")
                            st.session_state["active_nav"] = "Smart AI Assistant"
                            st.rerun()

                with act_c3:
                    if is_admin:
                        if st.button("🗑️ Delete Mention", key=f"del_m_{selected_m.get('id')}", use_container_width=True):
                            with st.spinner("Deleting mention..."):
                                try:
                                    client.delete_mention(selected_m.get("id"))
                                    st.success(f"Mention #{selected_m.get('id')} deleted!")
                                    st.rerun()
                                except ApiError as e:
                                    st.error(f"Failed to delete: {e.message}")

            else:
                st.info("No mentions found matching the current filters.")

        except ApiError as e:
            st.error(f"Failed to load mentions: {e.message}")

    # ------------------------------------------------------------------
    # TAB 2: Ingest New Mention
    # ------------------------------------------------------------------
    with tab_create:
        if not is_reviewer:
            st.warning("Only users with the **reviewer** or **admin** role can manually ingest mentions.")
        else:
            st.markdown("##### ➕ Manually Register New Mention")
            with st.form("create_mention_form", clear_on_submit=True):
                m_text = st.text_input("Mention Entity Text *", placeholder="e.g. Magnolia Lantern Bakery")
                m_source_text = st.text_area(
                    "Full Source Review Text",
                    placeholder="e.g. During our stay in Savannah, we visited Magnolia Lantern Bakery at 308 Abercorn Street, Savannah, Georgia. The pastries were fantastic.",
                    height=100,
                )
                mc1, mc2 = st.columns(2)
                with mc1:
                    m_source_type = st.selectbox("Source Type", options=["review"], index=0)
                with mc2:
                    m_source_id = st.text_input("Source ID (Optional)", placeholder="e.g. yelp_review_10492")

                create_m_submit = st.form_submit_button("Create Mention", type="primary", use_container_width=True)

            if create_m_submit:
                if not m_text.strip():
                    st.error("Mention text is required.")
                else:
                    with st.spinner("Ingesting mention..."):
                        try:
                            created = client.create_mention(
                                text=m_text.strip(),
                                source_text=m_source_text.strip() if m_source_text else None,
                                source_type=m_source_type,
                                source_id=m_source_id.strip() if m_source_id else None,
                            )
                            st.success(f"Mention created successfully with ID #{created.get('id')}!")
                        except ApiError as e:
                            st.error(f"Failed to create mention: {e.message}")
