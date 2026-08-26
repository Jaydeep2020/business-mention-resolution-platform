"""Documents view integrating with Document Service (port 8001) for PDF reports and summaries."""

from datetime import datetime
import pandas as pd
import streamlit as st

from frontend.api_client import ApiError
from frontend.state import get_api_client, has_role
from frontend.utils.ui_helpers import (
    render_header,
    render_metric_card,
    render_pagination_bar,
)


def render_documents_view() -> None:
    """Render Document Management and PDF Reports interface."""
    render_header(
        title="Document Management & Reports",
        subtitle="Access generated PDF resolution summaries, trigger monthly aggregate reports, and download audit documents",
        icon="📄",
    )

    client = get_api_client()
    is_reviewer = has_role("reviewer", "admin")

    tab_list, tab_gen_summary, tab_gen_monthly = st.tabs(
        ["📑 Documents Repository", "⚡ Generate Resolution Summary", "📅 Generate Monthly Report"]
    )

    # ------------------------------------------------------------------
    # TAB 1: Documents Repository
    # ------------------------------------------------------------------
    with tab_list:
        f_col1, f_col2 = st.columns([2, 1])
        with f_col1:
            doc_type_filter = st.selectbox(
                "Filter by Document Type",
                options=["All", "summary", "monthly_report"],
                key="doc_type_filter",
            )
        with f_col2:
            page_size = st.selectbox("Page Size", options=[10, 20, 50], index=1, key="doc_page_size")

        if "doc_page" not in st.session_state:
            st.session_state["doc_page"] = 1

        try:
            with st.spinner("Fetching documents from Document Service (8001)..."):
                resp = client.get_documents(
                    page=st.session_state["doc_page"],
                    page_size=page_size,
                    document_type=doc_type_filter if doc_type_filter != "All" else None,
                )

                items = resp.get("items", [])
                total = resp.get("total", 0)
                total_pages = resp.get("total_pages", 1)
                current_page = resp.get("page", 1)

            st.markdown(f"**Found {total:,} generated documents** (Page {current_page} of {max(1, total_pages)})")

            if items:
                table_rows = []
                for d in items:
                    gen_time = d.get("generated_at")
                    if gen_time:
                        try:
                            gen_time = datetime.fromisoformat(str(gen_time)).strftime("%Y-%m-%d %H:%M:%S")
                        except Exception:
                            pass

                    table_rows.append(
                        {
                            "ID": d.get("id"),
                            "Document Type": str(d.get("type", "")).replace("_", " ").title(),
                            "Target Month": d.get("month") or "—",
                            "Generated At": gen_time or "—",
                            "File Path": d.get("file_path"),
                        }
                    )

                st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)

                # Pagination
                new_page = render_pagination_bar(current_page=current_page, total_pages=total_pages, key_prefix="doc_pag")
                if new_page != current_page:
                    st.session_state["doc_page"] = new_page
                    st.rerun()

                # Download Section
                st.markdown("---")
                st.markdown("##### 📥 Download Document File")
                d_options = {f"Doc #{d.get('id')} — [{d.get('type')}] {d.get('file_path')}": d.get("id") for d in items}

                dl_col1, dl_col2 = st.columns([2, 1])
                with dl_col1:
                    sel_doc_str = st.selectbox("Select document to download:", options=list(d_options.keys()), key="doc_dl_select")
                    target_doc_id = d_options[sel_doc_str]

                with dl_col2:
                    st.write("")
                    try:
                        file_bytes, filename = client.download_document(target_doc_id)
                        st.download_button(
                            label=f"⬇️ Download {filename}",
                            data=file_bytes,
                            file_name=filename,
                            mime="application/pdf",
                            use_container_width=True,
                            type="primary",
                        )
                    except ApiError as e:
                        st.error(f"Download unavailable: {e.message}")

            else:
                st.info("No documents found in repository.")

        except ApiError as e:
            st.error(f"Failed to fetch documents: {e.message}")

    # ------------------------------------------------------------------
    # TAB 2: Generate Resolution Summary
    # ------------------------------------------------------------------
    with tab_gen_summary:
        if not is_reviewer:
            st.warning("Reviewer or Admin role is required to generate resolution summary PDFs.")
        else:
            st.markdown("##### ⚡ Generate Single Mention Resolution Summary PDF")
            st.markdown("Create a formal audit PDF document for a resolved or reviewed mention.")

            with st.form("gen_summary_form"):
                target_mention_id = st.number_input(
                    "Mention ID to Summarize",
                    min_value=1,
                    value=1,
                    step=1,
                    help="The Mention must already have candidate results recorded.",
                )
                gen_sum_btn = st.form_submit_button("Generate PDF Summary", type="primary", use_container_width=True)

            if gen_sum_btn:
                with st.spinner(f"Generating PDF for Mention #{target_mention_id}..."):
                    try:
                        doc_resp = client.generate_resolution_summary(mention_id=int(target_mention_id))
                        st.success(f"Resolution Summary PDF generated successfully! (Document ID #{doc_resp.get('id')})")
                        st.session_state["doc_page"] = 1
                        st.rerun()
                    except ApiError as e:
                        st.error(f"Failed to generate summary: {e.message}")

    # ------------------------------------------------------------------
    # TAB 3: Generate Monthly Report
    # ------------------------------------------------------------------
    with tab_gen_monthly:
        if not is_reviewer:
            st.warning("Reviewer or Admin role is required to generate monthly reports.")
        else:
            st.markdown("##### 📅 Generate Platform Monthly Audit Report")
            st.markdown("Calculates monthly mention volumes, auto-resolution match rates, review reasons, and produces a PDF report.")

            current_month_str = datetime.now().strftime("%Y-%m")

            with st.form("gen_monthly_form"):
                month_input = st.text_input(
                    "Target Month (YYYY-MM)",
                    value=current_month_str,
                    placeholder="e.g. 2026-08",
                    help="Format must be YYYY-MM",
                )
                gen_month_btn = st.form_submit_button("Generate Monthly Report", type="primary", use_container_width=True)

            if gen_month_btn:
                if not month_input.strip():
                    st.error("Please enter a valid month string (YYYY-MM).")
                else:
                    with st.spinner(f"Aggregating monthly metrics and rendering PDF report for {month_input.strip()}..."):
                        try:
                            month_resp = client.generate_monthly_report(month=month_input.strip())
                            st.success(f"Monthly report for **{month_input.strip()}** generated successfully!")

                            # Display report stats breakdown
                            rep_data = month_resp.get("report", {})
                            if rep_data:
                                st.markdown("###### 📊 Generated Report Summary")
                                rc1, rc2, rc3, rc4 = st.columns(4)
                                with rc1:
                                    render_metric_card("Processed", rep_data.get("mentions_processed", 0), "Total mentions", "🏷️")
                                with rc2:
                                    render_metric_card("Auto Resolved", rep_data.get("auto_resolved", 0), "High confidence", "⚡")
                                with rc3:
                                    render_metric_card("Approved", rep_data.get("reviewer_approved", 0), "Human approved", "✅")
                                with rc4:
                                    match_pct = round(rep_data.get("match_rate", 0) * 100, 1)
                                    render_metric_card("Match Rate", f"{match_pct}%", "Overall success", "📈")

                            st.session_state["doc_page"] = 1
                        except ApiError as e:
                            st.error(f"Failed to generate monthly report: {e.message}")
