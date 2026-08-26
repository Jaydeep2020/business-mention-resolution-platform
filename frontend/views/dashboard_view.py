"""Dashboard view with high-level system metrics, service health, and quick actions."""

import pandas as pd
import streamlit as st

from frontend.api_client import ApiError
from frontend.state import get_api_client
from frontend.utils.ui_helpers import (
    render_header,
    render_metric_card,
    render_score_pill,
    render_status_badge,
)


def render_dashboard_view() -> None:
    """Render main platform overview and status dashboard."""
    render_header(
        title="Platform Dashboard",
        subtitle="Real-time monitoring of businesses, mention resolutions, review queue, and documents",
        icon="📊",
    )

    client = get_api_client()

    # ------------------------------------------------------------------
    # 1. Microservice Health Status
    # ------------------------------------------------------------------
    st.markdown("##### 🔌 Microservice Connectivity")
    col_h1, col_h2, col_h3 = st.columns([1, 1, 2])

    catalog_ok, catalog_msg = client.check_catalog_health()
    doc_ok, doc_msg = client.check_document_health()

    with col_h1:
        cat_badge = (
            '<span style="color: #34d399; font-weight: 600;">● Online</span>'
            if catalog_ok
            else f'<span style="color: #f87171; font-weight: 600;">● {catalog_msg}</span>'
        )
        st.markdown(
            f"""
            <div class="metric-card" style="padding: 12px 16px;">
                <div style="font-size: 0.8rem; color: #94a3b8;">CATALOG SERVICE (8000)</div>
                <div style="font-size: 1.1rem; margin-top: 4px;">{cat_badge}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_h2:
        doc_badge = (
            '<span style="color: #34d399; font-weight: 600;">● Online</span>'
            if doc_ok
            else f'<span style="color: #f87171; font-weight: 600;">● {doc_msg}</span>'
        )
        st.markdown(
            f"""
            <div class="metric-card" style="padding: 12px 16px;">
                <div style="font-size: 0.8rem; color: #94a3b8;">DOCUMENT SERVICE (8001)</div>
                <div style="font-size: 1.1rem; margin-top: 4px;">{doc_badge}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_h3:
        if st.button("🔄 Refresh System Stats", use_container_width=True):
            st.rerun()

    st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)

    # ------------------------------------------------------------------
    # 2. Fetch Data from APIs
    # ------------------------------------------------------------------
    businesses_count = "—"
    mentions_count = "—"
    review_queue_count = "—"
    documents_count = "—"
    recent_mentions = []
    status_counts = {"pending": 0, "auto_resolved": 0, "sent_for_reviewer": 0, "approved": 0, "rejected": 0}

    with st.spinner("Fetching platform metrics..."):
        # Fetch business count
        try:
            b_resp = client.get_businesses(page=1, page_size=1)
            businesses_count = f"{b_resp.get('total', 0):,}"
        except Exception:
            pass

        # Fetch mentions count & items
        try:
            m_resp = client.get_mentions(page=1, page_size=50)
            mentions_count = f"{m_resp.get('total', 0):,}"
            recent_mentions = m_resp.get("items", [])

            # Compute status distribution
            for m in recent_mentions:
                st_key = str(m.get("resolution_status", "")).lower()
                if st_key in status_counts:
                    status_counts[st_key] += 1
        except Exception:
            pass

        # Fetch review queue count
        try:
            rq_resp = client.get_review_queue(page=1, page_size=1)
            review_queue_count = f"{rq_resp.get('total', 0):,}"
        except Exception:
            pass

        # Fetch document count
        try:
            d_resp = client.get_documents(page=1, page_size=1)
            documents_count = f"{d_resp.get('total', 0):,}"
        except Exception:
            pass

    # ------------------------------------------------------------------
    # 3. High-level KPI Cards
    # ------------------------------------------------------------------
    st.markdown("##### 📈 Core Metrics")
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

    with kpi_col1:
        render_metric_card("Total Businesses", businesses_count, "Catalog database", "🏢")
    with kpi_col2:
        render_metric_card("Total Mentions", mentions_count, "Ingested text mentions", "🏷️")
    with kpi_col3:
        render_metric_card("Review Queue", review_queue_count, "Awaiting human review", "⚖️")
    with kpi_col4:
        render_metric_card("Documents", documents_count, "Reports & summaries", "📄")

    st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

    # ------------------------------------------------------------------
    # 4. Status Distribution & Quick Actions
    # ------------------------------------------------------------------
    col_chart, col_actions = st.columns([3, 2])

    with col_chart:
        st.markdown("##### 🎯 Mention Resolution Status Breakdown")
        if recent_mentions:
            status_df = pd.DataFrame(
                [
                    {"Status": "Pending", "Count": status_counts["pending"]},
                    {"Status": "Auto-Resolved", "Count": status_counts["auto_resolved"]},
                    {"Status": "Sent for Review", "Count": status_counts["sent_for_reviewer"]},
                    {"Status": "Approved", "Count": status_counts["approved"]},
                    {"Status": "Rejected", "Count": status_counts["rejected"]},
                ]
            )
            st.bar_chart(status_df.set_index("Status"), color="#3b82f6", use_container_width=True)
        else:
            st.info("No mentions found yet to build the status chart.")

    with col_actions:
        st.markdown("##### 🚀 Quick Actions")
        st.markdown(
            """
            <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; padding: 16px;">
                <p style="color: #94a3b8; font-size: 0.9rem; margin-bottom: 12px;">Jump directly into any workflow:</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        qa_c1, qa_c2 = st.columns(2)
        with qa_c1:
            if st.button("🏷️ Extract Mentions", use_container_width=True):
                st.session_state["active_nav"] = "Mention Extraction"
                st.rerun()
            if st.button("🤖 AI Assistant", use_container_width=True):
                st.session_state["active_nav"] = "Smart AI Assistant"
                st.rerun()

        with qa_c2:
            if st.button("⚖️ Review Queue", use_container_width=True):
                st.session_state["active_nav"] = "Human Review Queue"
                st.rerun()
            if st.button("💬 Catalog Q&A", use_container_width=True):
                st.session_state["active_nav"] = "Catalog Q&A"
                st.rerun()

    st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)

    # ------------------------------------------------------------------
    # 5. Recent Mentions Table
    # ------------------------------------------------------------------
    st.markdown("##### 📋 Recent Mentions")
    if recent_mentions:
        table_rows = []
        for m in recent_mentions[:10]:
            table_rows.append(
                {
                    "ID": m.get("id"),
                    "Mention Text": m.get("text"),
                    "Status": m.get("resolution_status", "").upper(),
                    "Confidence": f"{round(m.get('confidence_score') * 100, 1)}%" if m.get("confidence_score") else "—",
                    "Resolved Business ID": m.get("resolved_business_id") or "—",
                    "Source Text Preview": (m.get("source_text") or "—")[:80] + ("..." if len(m.get("source_text") or "") > 80 else ""),
                }
            )
        st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)
    else:
        st.info("No recent mentions available.")
