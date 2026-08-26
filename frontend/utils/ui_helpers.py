"""UI helper functions, reusable widgets, custom CSS, badges, and formatting utilities."""

from typing import Any, Dict, List, Optional
import streamlit as st


def render_custom_css() -> None:
    """Inject custom modern CSS for clean typography, cards, badges, and layout."""
    st.markdown(
        """
        <style>
            /* Main container polish */
            .block-container {
                padding-top: 2rem;
                padding-bottom: 3rem;
                max-width: 95%;
            }

            /* Metric card styling */
            .metric-card {
                background: linear-gradient(135deg, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.02));
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                padding: 18px 20px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
                transition: transform 0.2s ease, border-color 0.2s ease;
            }
            .metric-card:hover {
                transform: translateY(-2px);
                border-color: rgba(66, 153, 225, 0.4);
            }
            .metric-title {
                font-size: 0.85rem;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.05em;
                color: #8892b0;
                margin-bottom: 6px;
            }
            .metric-value {
                font-size: 1.8rem;
                font-weight: 700;
                color: #e2e8f0;
                line-height: 1.2;
            }
            .metric-subtitle {
                font-size: 0.78rem;
                color: #718096;
                margin-top: 4px;
            }

            /* Custom badges */
            .badge {
                display: inline-block;
                padding: 3px 10px;
                font-size: 0.78rem;
                font-weight: 600;
                border-radius: 9999px;
                text-transform: uppercase;
                letter-spacing: 0.03em;
            }
            .badge-pending {
                background-color: rgba(160, 174, 192, 0.2);
                color: #cbd5e0;
                border: 1px solid rgba(160, 174, 192, 0.4);
            }
            .badge-auto_resolved {
                background-color: rgba(66, 153, 225, 0.2);
                color: #63b3ed;
                border: 1px solid rgba(66, 153, 225, 0.4);
            }
            .badge-sent_for_reviewer {
                background-color: rgba(236, 159, 39, 0.2);
                color: #f6ad55;
                border: 1px solid rgba(236, 159, 39, 0.4);
            }
            .badge-approved {
                background-color: rgba(72, 187, 120, 0.2);
                color: #68d391;
                border: 1px solid rgba(72, 187, 120, 0.4);
            }
            .badge-rejected {
                background-color: rgba(245, 101, 101, 0.2);
                color: #fc8181;
                border: 1px solid rgba(245, 101, 101, 0.4);
            }
            .badge-admin {
                background-color: rgba(159, 122, 234, 0.25);
                color: #d6bcfa;
                border: 1px solid rgba(159, 122, 234, 0.5);
            }
            .badge-reviewer {
                background-color: rgba(56, 178, 172, 0.25);
                color: #81e6d9;
                border: 1px solid rgba(56, 178, 172, 0.5);
            }
            .badge-viewer {
                background-color: rgba(160, 174, 192, 0.2);
                color: #a0aec0;
                border: 1px solid rgba(160, 174, 192, 0.3);
            }

            /* Info Card */
            .info-box {
                background: rgba(30, 41, 59, 0.5);
                border-left: 4px solid #3b82f6;
                padding: 14px 18px;
                border-radius: 0 8px 8px 0;
                margin: 10px 0;
            }

            /* Entity Chip */
            .entity-chip {
                background: rgba(59, 130, 246, 0.15);
                border: 1px solid rgba(59, 130, 246, 0.4);
                color: #93c5fd;
                border-radius: 6px;
                padding: 4px 10px;
                display: inline-flex;
                align-items: center;
                gap: 6px;
                font-weight: 500;
                margin: 3px;
            }

            /* Step Card */
            .step-card {
                display: flex;
                align-items: flex-start;
                gap: 12px;
                padding: 10px 14px;
                background: rgba(255, 255, 255, 0.02);
                border-left: 3px solid #10b981;
                margin-bottom: 8px;
                border-radius: 0 6px 6px 0;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header(title: str, subtitle: Optional[str] = None, icon: str = "🏢") -> None:
    """Render a clean, modern page header."""
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; gap: 14px; margin-bottom: 20px; border-bottom: 1px solid rgba(255, 255, 255, 0.08); padding-bottom: 14px;">
            <div style="font-size: 2.2rem; background: rgba(59, 130, 246, 0.15); border-radius: 12px; width: 56px; height: 56px; display: flex; align-items: center; justify-content: center; border: 1px solid rgba(59, 130, 246, 0.3);">{icon}</div>
            <div>
                <h1 style="margin: 0; font-size: 1.8rem; font-weight: 700; color: #f8fafc;">{title}</h1>
                {f'<p style="margin: 2px 0 0 0; color: #94a3b8; font-size: 0.95rem;">{subtitle}</p>' if subtitle else ''}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_status_badge(status_str: Optional[str]) -> str:
    """Return HTML markup for a styled resolution status badge."""
    if not status_str:
        return '<span class="badge badge-pending">Unknown</span>'

    status_clean = str(status_str).lower().replace(" ", "_")
    display_text = status_clean.replace("_", " ").title()

    return f'<span class="badge badge-badge-{status_clean} badge-{status_clean}">{display_text}</span>'


def render_role_badge(role_str: Optional[str]) -> str:
    """Return HTML markup for a user role badge."""
    if not role_str:
        return '<span class="badge badge-viewer">Guest</span>'

    role_clean = str(role_str).lower()
    return f'<span class="badge badge-{role_clean}">{role_clean.title()}</span>'


def render_score_pill(score: Optional[float]) -> str:
    """Format confidence score into a colored pill."""
    if score is None:
        return '<span style="color: #64748b;">N/A</span>'

    pct = round(score * 100, 1)
    if score >= 0.75:
        color = "#34d399"
        bg = "rgba(52, 211, 153, 0.15)"
    elif score >= 0.50:
        color = "#fbbf24"
        bg = "rgba(251, 191, 36, 0.15)"
    else:
        color = "#f87171"
        bg = "rgba(248, 113, 113, 0.15)"

    return f'<span style="background: {bg}; color: {color}; padding: 3px 8px; border-radius: 6px; font-weight: 600; font-size: 0.85rem;">{pct}% ({score:.4f})</span>'


def render_metric_card(title: str, value: Any, subtitle: Optional[str] = None, icon: str = "📊") -> None:
    """Render an attractive custom metric tile."""
    st.markdown(
        f"""
        <div class="metric-card">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <div class="metric-title">{title}</div>
                    <div class="metric-value">{value}</div>
                    {f'<div class="metric-subtitle">{subtitle}</div>' if subtitle else ''}
                </div>
                <div style="font-size: 1.6rem; opacity: 0.85;">{icon}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_pagination_bar(current_page: int, total_pages: int, key_prefix: str) -> int:
    """Render clean pagination controls (Previous, Current/Total, Next, Jump)."""
    if total_pages <= 1:
        return 1

    col1, col2, col3, col4, col5 = st.columns([1, 2, 2, 2, 1])

    with col1:
        if st.button("◀ Prev", key=f"{key_prefix}_prev", disabled=(current_page <= 1)):
            return max(1, current_page - 1)

    with col2:
        st.markdown(
            f"<div style='text-align: center; line-height: 2.2rem; font-weight: 500; color: #94a3b8;'>"
            f"Page <b style='color: #f8fafc;'>{current_page}</b> of <b>{total_pages}</b>"
            f"</div>",
            unsafe_allow_html=True,
        )

    with col3:
        if st.button("Next ▶", key=f"{key_prefix}_next", disabled=(current_page >= total_pages)):
            return min(total_pages, current_page + 1)

    with col4:
        jump_page = st.number_input(
            "Jump to page",
            min_value=1,
            max_value=total_pages,
            value=current_page,
            key=f"{key_prefix}_jump_val",
            label_visibility="collapsed",
        )

    with col5:
        if st.button("Go", key=f"{key_prefix}_jump_btn"):
            return jump_page

    return current_page
