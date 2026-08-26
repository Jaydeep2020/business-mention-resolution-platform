"""Main Streamlit application entrypoint for Business Mention Resolution Platform."""

import sys
from pathlib import Path

# Ensure root workspace directory is in sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import streamlit as st

from frontend.config import AppConfig
from frontend.state import (
    get_api_client,
    get_current_user,
    get_user_role,
    init_session_state,
    is_authenticated,
    logout_user,
)
from frontend.utils.ui_helpers import (
    render_custom_css,
    render_role_badge,
)
from frontend.views.assistant_view import render_assistant_view
from frontend.views.businesses_view import render_businesses_view
from frontend.views.dashboard_view import render_dashboard_view
from frontend.views.documents_view import render_documents_view
from frontend.views.extraction_view import render_extraction_view
from frontend.views.login_view import render_login_view
from frontend.views.mentions_view import render_mentions_view
from frontend.views.qa_view import render_qa_view
from frontend.views.review_queue_view import render_review_queue_view

# Page Config
st.set_page_config(
    page_title=AppConfig.APP_TITLE,
    page_icon=AppConfig.APP_ICON,
    layout=AppConfig.PAGE_LAYOUT,
    initial_sidebar_state="expanded",
)

# Apply global styling
render_custom_css()

# Initialize session state
init_session_state()


def main() -> None:
    """Main routing and layout coordinator."""
    if not is_authenticated():
        render_login_view()
        return

    # User is authenticated: Build Sidebar & Routing
    user = get_current_user() or {}
    role = get_user_role()
    client = get_api_client()

    # ------------------------------------------------------------------
    # Sidebar
    # ------------------------------------------------------------------
    with st.sidebar:
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                <span style="font-size: 2rem;">{AppConfig.APP_ICON}</span>
                <div>
                    <h3 style="margin: 0; font-size: 1.1rem; font-weight: 700; color: #f8fafc;">BMRP Portal</h3>
                    <div style="font-size: 0.75rem; color: #94a3b8;">Mention Resolution v1.0</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # User Card
        st.markdown(
            f"""
            <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 10px 14px; margin-bottom: 15px;">
                <div style="font-size: 0.75rem; color: #94a3b8; text-transform: uppercase;">Logged In As</div>
                <div style="font-size: 0.95rem; font-weight: 600; color: #f1f5f9; margin-top: 2px;">👤 {user.get('username')}</div>
                <div style="margin-top: 5px;">Role: {render_role_badge(role)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Navigation Options
        nav_options = [
            "📊 Dashboard",
            "🏢 Businesses",
            "🏷️ Mentions",
            "🔍 Mention Extraction",
            "🤖 Smart AI Assistant",
            "⚖️ Human Review Queue",
            "💬 Catalog Q&A",
            "📄 Documents",
        ]

        current_nav = st.session_state.get("active_nav", "Dashboard")
        selected_index = 0
        for i, opt in enumerate(nav_options):
            if current_nav in opt:
                selected_index = i
                break

        chosen_nav = st.radio(
            "Navigation",
            options=nav_options,
            index=selected_index,
            label_visibility="collapsed",
        )

        # Extract clean nav name
        clean_nav = chosen_nav.split(" ", 1)[-1]
        st.session_state["active_nav"] = clean_nav

        st.markdown("---")

        # Backend Health & Service Endpoints
        with st.expander("⚙️ Service Settings"):
            catalog_input = st.text_input("Catalog Service", value=st.session_state["catalog_url"])
            doc_input = st.text_input("Document Service", value=st.session_state["document_url"])

            if st.button("Apply URLs"):
                st.session_state["catalog_url"] = catalog_input
                st.session_state["document_url"] = doc_input
                st.rerun()

            st.markdown("<hr style='margin: 8px 0;'>", unsafe_allow_html=True)
            cat_ok, _ = client.check_catalog_health()
            doc_ok, _ = client.check_document_health()
            st.markdown(
                f"""
                <div style="font-size: 0.8rem; line-height: 1.6;">
                    <b>Catalog (8000):</b> {'<span style="color: #34d399;">● Connected</span>' if cat_ok else '<span style="color: #f87171;">● Disconnected</span>'}<br>
                    <b>Document (8001):</b> {'<span style="color: #34d399;">● Connected</span>' if doc_ok else '<span style="color: #f87171;">● Disconnected</span>'}
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)

        if st.button("🚪 Sign Out", use_container_width=True):
            logout_user()
            st.rerun()

    # ------------------------------------------------------------------
    # Routing Body
    # ------------------------------------------------------------------
    active_view = st.session_state.get("active_nav", "Dashboard")

    if active_view == "Dashboard":
        render_dashboard_view()
    elif active_view == "Businesses":
        render_businesses_view()
    elif active_view == "Mentions":
        render_mentions_view()
    elif active_view == "Mention Extraction":
        render_extraction_view()
    elif active_view == "Smart AI Assistant":
        render_assistant_view()
    elif active_view == "Human Review Queue":
        render_review_queue_view()
    elif active_view == "Catalog Q&A":
        render_qa_view()
    elif active_view == "Documents":
        render_documents_view()
    else:
        render_dashboard_view()


if __name__ == "__main__":
    main()
