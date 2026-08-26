"""Mention Extraction view using spaCy NLP to extract business entities from free-form text."""

import pandas as pd
import streamlit as st

from frontend.api_client import ApiError
from frontend.state import get_api_client, has_role
from frontend.utils.mock_data import SAMPLE_EXTRACTION_TEXTS
from frontend.utils.ui_helpers import render_header, render_metric_card


def render_extraction_view() -> None:
    """Render Mention Extraction interface."""
    render_header(
        title="Mention Extraction (NLP)",
        subtitle="Extract organization and business mentions from customer reviews and free-form writeups using spaCy NER",
        icon="🔍",
    )

    client = get_api_client()
    is_reviewer = has_role("reviewer", "admin")

    if not is_reviewer:
        st.warning("You have viewer access. Reviewer or Admin role is required to extract mentions.")
        return

    # Sample Prompts
    st.markdown("##### 💡 Load Sample Review")
    sample_cols = st.columns(len(SAMPLE_EXTRACTION_TEXTS))
    for idx, sample in enumerate(SAMPLE_EXTRACTION_TEXTS):
        with sample_cols[idx]:
            if st.button(sample["title"], key=f"sample_text_{idx}", use_container_width=True):
                st.session_state["extract_input_text"] = sample["text"]
                st.session_state["extract_source_id"] = sample["source_id"]
                st.rerun()

    # Form
    st.markdown("##### ✍️ Input Free-Form Review Text")
    default_text = st.session_state.get(
        "extract_input_text",
        "During our stay in Savannah, we visited Magnolia Lantern Bakery at 308 Abercorn Street, Savannah, Georgia. The pastries were fantastic.",
    )
    default_source_id = st.session_state.get("extract_source_id", "sample_rev_01")

    with st.form("extraction_form"):
        input_text = st.text_area(
            "Review or Document Text *",
            value=default_text,
            height=140,
            placeholder="Paste your text containing business names...",
        )

        ec1, ec2, ec3 = st.columns([1.5, 1.5, 2])
        with ec1:
            source_type = st.selectbox("Source Type", options=["review"], index=0)
        with ec2:
            source_id = st.text_input("Source ID", value=default_source_id)
        with ec3:
            save_mentions = st.checkbox(
                "Save extracted mentions into database",
                value=True,
                help="When enabled, new Mention rows will be created in the database for resolution.",
            )

        submit_btn = st.form_submit_button("🔍 Extract Business Mentions", type="primary", use_container_width=True)

    if submit_btn:
        if not input_text.strip():
            st.error("Please provide text to extract mentions from.")
        else:
            with st.spinner("Analyzing text with spaCy Named Entity Recognition..."):
                try:
                    resp = client.extract_mentions(
                        text=input_text.strip(),
                        source_type=source_type,
                        source_id=source_id.strip() if source_id else None,
                        save_mentions=save_mentions,
                    )
                    st.session_state["last_extraction_result"] = resp
                    st.session_state["last_extraction_raw_text"] = input_text
                    st.success("Entity extraction completed successfully!")
                except ApiError as e:
                    st.error(f"Extraction failed: {e.message}")
                except Exception as e:
                    st.error(f"Unexpected error: {str(e)}")

    # Display Results
    if "last_extraction_result" in st.session_state:
        res = st.session_state["last_extraction_result"]
        raw_text = st.session_state.get("last_extraction_raw_text", "")

        st.markdown("---")
        st.markdown("##### 📊 Extraction Summary")

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            render_metric_card("Total Extracted", res.get("total_extracted", 0), "Entities detected", "🏷️")
        with m2:
            render_metric_card("Created in DB", res.get("created_count", 0), "New mention rows", "✨")
        with m3:
            render_metric_card("Reused", res.get("reused_count", 0), "Existing records", "♻️")
        with m4:
            render_metric_card("Model Engine", res.get("model", "spacy"), "NER Pipeline", "🧠")

        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)

        mentions_list = res.get("mentions", [])
        if mentions_list:
            st.markdown("##### 🏢 Detected Business Entities")

            # Visual entity chips
            chips_html = '<div style="margin-bottom: 16px;">'
            for item in mentions_list:
                m_id_txt = f" (ID: #{item.get('mention_id')})" if item.get("mention_id") else ""
                chips_html += f'<span class="entity-chip"><b>{item.get("text")}</b> <small>[{item.get("label")}{m_id_txt}]</small></span>'
            chips_html += "</div>"
            st.markdown(chips_html, unsafe_allow_html=True)

            # Detail table
            t_rows = []
            for item in mentions_list:
                t_rows.append(
                    {
                        "Mention Text": item.get("text"),
                        "NER Label": item.get("label"),
                        "Start Char": item.get("start_char"),
                        "End Char": item.get("end_char"),
                        "DB Mention ID": item.get("mention_id") or "Not Saved",
                        "Created New": "Yes" if item.get("created") else "No / Reused",
                    }
                )
            st.dataframe(pd.DataFrame(t_rows), use_container_width=True, hide_index=True)

            # Quick resolution link
            saved_mentions = [m for m in mentions_list if m.get("mention_id")]
            if saved_mentions:
                st.markdown("###### 🚀 Immediate Resolution")
                res_col1, res_col2 = st.columns([2, 1])
                with res_col1:
                    sel_extract_m = st.selectbox(
                        "Choose extracted mention to resolve:",
                        options=[f"#{m.get('mention_id')} — {m.get('text')}" for m in saved_mentions],
                        key="extract_res_sel",
                    )
                    sel_id = int(sel_extract_m.split("—")[0].replace("#", "").strip())
                with res_col2:
                    st.write("")
                    if st.button("🤖 Open in Smart AI Assistant", type="primary", use_container_width=True):
                        st.session_state["selected_mention_id"] = sel_id
                        st.session_state["active_nav"] = "Smart AI Assistant"
                        st.rerun()

        else:
            st.info("No business entities were detected in the provided text.")
