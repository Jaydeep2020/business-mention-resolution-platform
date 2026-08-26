"""Business Catalog view supporting pagination, search/filters, and role-based CRUD operations."""

import pandas as pd
import streamlit as st

from frontend.api_client import ApiError
from frontend.state import get_api_client, has_role
from frontend.utils.ui_helpers import (
    render_header,
    render_pagination_bar,
)


def render_businesses_view() -> None:
    """Render Business Catalog management interface."""
    render_header(
        title="Business Catalog",
        subtitle="Search, view, create, and manage business records across the enterprise catalog",
        icon="🏢",
    )

    client = get_api_client()
    is_admin = has_role("admin")
    is_reviewer = has_role("reviewer", "admin")

    # Tabs for main browsing vs creating / managing categories
    tab_list, tab_create, tab_categories = st.tabs(
        ["📋 Browse Businesses", "➕ Create Business" if is_admin else "ℹ️ Create (Admin Only)", "🏷️ Categories"]
    )

    # ------------------------------------------------------------------
    # TAB 1: Browse Businesses
    # ------------------------------------------------------------------
    with tab_list:
        # Search & Filter bar
        st.markdown("##### 🔍 Search & Filters")
        f_col1, f_col2, f_col3, f_col4 = st.columns([2, 1.5, 1.5, 1])

        with f_col1:
            search_query = st.text_input(
                "Search by Name / Keyword",
                placeholder="e.g. Starbucks, Pizza, Bakery...",
                key="biz_search_input",
            )
        with f_col2:
            city_filter = st.text_input(
                "Filter by City",
                placeholder="e.g. Santa Barbara, Philadelphia...",
                key="biz_city_input",
            )
        with f_col3:
            # Load categories for filter dropdown
            cat_options = {"All Categories": None}
            try:
                cats_resp = client.get_categories(page=1, page_size=100)
                for cat in cats_resp.get("items", []):
                    cat_options[f"{cat.get('name')} (ID: {cat.get('id')})"] = cat.get("id")
            except Exception:
                pass

            selected_cat_label = st.selectbox(
                "Category",
                options=list(cat_options.keys()),
                key="biz_cat_select",
            )
            selected_cat_id = cat_options[selected_cat_label]

        with f_col4:
            verified_filter_choice = st.selectbox(
                "Verified",
                options=["All", "Verified Only", "Unverified Only"],
                key="biz_verified_select",
            )
            is_verified_param = None
            if verified_filter_choice == "Verified Only":
                is_verified_param = True
            elif verified_filter_choice == "Unverified Only":
                is_verified_param = False

        # Page controls in session state
        if "biz_page" not in st.session_state:
            st.session_state["biz_page"] = 1

        p_col1, p_col2 = st.columns([3, 1])
        with p_col2:
            page_size = st.selectbox(
                "Page Size",
                options=[10, 20, 50],
                index=1,
                key="biz_page_size",
            )

        # Query API
        try:
            with st.spinner("Loading businesses..."):
                resp = client.get_businesses(
                    page=st.session_state["biz_page"],
                    page_size=page_size,
                    search=search_query.strip() if search_query else None,
                    city=city_filter.strip() if city_filter else None,
                    category_id=selected_cat_id,
                    is_verified=is_verified_param,
                )

                items = resp.get("items", [])
                total = resp.get("total", 0)
                total_pages = resp.get("total_pages", 1)
                current_page = resp.get("page", 1)

            st.markdown(f"**Found {total:,} businesses** (Page {current_page} of {max(1, total_pages)})")

            if items:
                table_data = []
                for b in items:
                    cat_names = ", ".join([c.get("name") for c in b.get("categories", [])])
                    table_data.append(
                        {
                            "DB ID": b.get("id"),
                            "Catalog ID": b.get("business_id"),
                            "Name": b.get("name"),
                            "City": b.get("city") or "—",
                            "State": b.get("state") or "—",
                            "Address": b.get("address") or "—",
                            "Verified": "✅ Yes" if b.get("is_verified") else "❌ No",
                            "Categories": cat_names or "—",
                        }
                    )

                st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)

                # Pagination
                new_page = render_pagination_bar(
                    current_page=current_page,
                    total_pages=total_pages,
                    key_prefix="biz_pag",
                )
                if new_page != current_page:
                    st.session_state["biz_page"] = new_page
                    st.rerun()

                # Business Detail / Edit / Delete Sub-Section
                st.markdown("---")
                st.markdown("##### 🔍 View / Edit / Delete Business")
                detail_col1, detail_col2 = st.columns([1, 2])

                biz_lookup_dict = {f"#{b.get('id')} - {b.get('name')} ({b.get('city') or 'No City'})": b for b in items}
                with detail_col1:
                    selected_biz_str = st.selectbox(
                        "Select a business from current page:",
                        options=list(biz_lookup_dict.keys()),
                        key="selected_biz_inspect",
                    )
                    selected_biz = biz_lookup_dict[selected_biz_str]

                with detail_col2:
                    st.markdown(
                        f"""
                        <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; padding: 14px;">
                            <h4 style="margin: 0; color: #60a5fa;">{selected_biz.get('name')}</h4>
                            <p style="margin: 4px 0; color: #94a3b8; font-size: 0.9rem;">
                                <b>DB ID:</b> {selected_biz.get('id')} | <b>Catalog ID:</b> {selected_biz.get('business_id')} | 
                                <b>Verified:</b> {'✅ Yes' if selected_biz.get('is_verified') else '❌ No'}
                            </p>
                            <p style="margin: 4px 0; color: #cbd5e1; font-size: 0.9rem;">
                                <b>Address:</b> {selected_biz.get('address') or 'N/A'}, {selected_biz.get('city') or ''}, {selected_biz.get('state') or ''} {selected_biz.get('postal_code') or ''}
                            </p>
                            <p style="margin: 4px 0; color: #94a3b8; font-size: 0.85rem;">
                                <b>Coordinates:</b> Lat: {selected_biz.get('latitude') or 'N/A'}, Lon: {selected_biz.get('longitude') or 'N/A'}
                            </p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                # Edit form (Admin) & Delete (Admin/Reviewer)
                if is_admin:
                    with st.expander(f"✏️ Edit Business #{selected_biz.get('id')} ({selected_biz.get('name')})"):
                        with st.form(f"edit_biz_form_{selected_biz.get('id')}"):
                            edit_name = st.text_input("Business Name", value=selected_biz.get("name") or "")
                            edit_address = st.text_input("Address", value=selected_biz.get("address") or "")
                            ec1, ec2, ec3 = st.columns(3)
                            with ec1:
                                edit_city = st.text_input("City", value=selected_biz.get("city") or "")
                            with ec2:
                                edit_state = st.text_input("State", value=selected_biz.get("state") or "")
                            with ec3:
                                edit_zip = st.text_input("Postal Code", value=selected_biz.get("postal_code") or "")

                            ec4, ec5, ec6 = st.columns(3)
                            with ec4:
                                edit_lat = st.number_input(
                                    "Latitude",
                                    value=float(selected_biz.get("latitude") or 0.0),
                                    format="%.6f",
                                )
                            with ec5:
                                edit_lon = st.number_input(
                                    "Longitude",
                                    value=float(selected_biz.get("longitude") or 0.0),
                                    format="%.6f",
                                )
                            with ec6:
                                edit_verified = st.checkbox(
                                    "Is Verified",
                                    value=bool(selected_biz.get("is_verified")),
                                )

                            update_btn = st.form_submit_button("Save Changes", type="primary")

                        if update_btn:
                            with st.spinner("Updating business..."):
                                try:
                                    update_payload = {
                                        "name": edit_name.strip() if edit_name else None,
                                        "address": edit_address.strip() if edit_address else None,
                                        "city": edit_city.strip() if edit_city else None,
                                        "state": edit_state.strip() if edit_state else None,
                                        "postal_code": edit_zip.strip() if edit_zip else None,
                                        "latitude": edit_lat if edit_lat != 0.0 else None,
                                        "longitude": edit_lon if edit_lon != 0.0 else None,
                                        "is_verified": edit_verified,
                                    }
                                    client.update_business(selected_biz.get("id"), update_payload)
                                    st.success(f"Business #{selected_biz.get('id')} updated successfully!")
                                    st.rerun()
                                except ApiError as e:
                                    st.error(f"Failed to update business: {e.message}")

                if is_reviewer:
                    with st.expander(f"🗑️ Delete Business #{selected_biz.get('id')}"):
                        st.warning(f"Are you sure you want to delete **{selected_biz.get('name')}** (ID: {selected_biz.get('id')})? This action cannot be undone.")
                        if st.button("Confirm Delete", key=f"del_biz_btn_{selected_biz.get('id')}", type="primary"):
                            with st.spinner("Deleting business..."):
                                try:
                                    client.delete_business(selected_biz.get("id"))
                                    st.success(f"Business #{selected_biz.get('id')} deleted successfully!")
                                    st.rerun()
                                except ApiError as e:
                                    st.error(f"Failed to delete business: {e.message}")
            else:
                st.info("No businesses matched your search query or filter criteria.")

        except ApiError as e:
            st.error(f"Failed to load businesses: {e.message}")
        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")

    # ------------------------------------------------------------------
    # TAB 2: Create Business
    # ------------------------------------------------------------------
    with tab_create:
        if not is_admin:
            st.warning("Only users with the **admin** role are permitted to create businesses.")
        else:
            st.markdown("##### ➕ Register New Business in Catalog")
            with st.form("create_business_form", clear_on_submit=True):
                c_id = st.text_input("Business Catalog ID *", placeholder="e.g. BIZ_NYC_8892 (unique string)")
                c_name = st.text_input("Business Name *", placeholder="e.g. Magnolia Lantern Bakery")
                c_address = st.text_input("Street Address", placeholder="e.g. 308 Abercorn Street")

                cc1, cc2, cc3 = st.columns(3)
                with cc1:
                    c_city = st.text_input("City", placeholder="e.g. Savannah")
                with cc2:
                    c_state = st.text_input("State", placeholder="e.g. GA")
                with cc3:
                    c_postal = st.text_input("Postal Code", placeholder="e.g. 31401")

                cc4, cc5, cc6 = st.columns(3)
                with cc4:
                    c_lat = st.number_input("Latitude", value=0.0, format="%.6f")
                with cc5:
                    c_lon = st.number_input("Longitude", value=0.0, format="%.6f")
                with cc6:
                    c_verified = st.checkbox("Is Verified", value=True)

                # Category multi-select
                all_cats = []
                try:
                    cats_r = client.get_categories(page=1, page_size=100)
                    all_cats = cats_r.get("items", [])
                except Exception:
                    pass

                cat_id_map = {c.get("name"): c.get("id") for c in all_cats}
                selected_cat_names = st.multiselect("Associated Categories", options=list(cat_id_map.keys()))
                cat_ids = [cat_id_map[name] for name in selected_cat_names if name in cat_id_map]

                create_submit = st.form_submit_button("Create Business", type="primary", use_container_width=True)

            if create_submit:
                if not c_id.strip() or not c_name.strip():
                    st.error("Business Catalog ID and Name are required.")
                else:
                    payload = {
                        "business_id": c_id.strip(),
                        "name": c_name.strip(),
                        "address": c_address.strip() if c_address else None,
                        "city": c_city.strip() if c_city else None,
                        "state": c_state.strip() if c_state else None,
                        "postal_code": c_postal.strip() if c_postal else None,
                        "latitude": c_lat if c_lat != 0.0 else None,
                        "longitude": c_lon if c_lon != 0.0 else None,
                        "is_verified": c_verified,
                        "category_ids": cat_ids,
                    }
                    with st.spinner("Creating business..."):
                        try:
                            created = client.create_business(payload)
                            st.success(f"Business **{created.get('name')}** created successfully with DB ID #{created.get('id')}!")
                        except ApiError as e:
                            st.error(f"Failed to create business: {e.message}")

    # ------------------------------------------------------------------
    # TAB 3: Categories Management
    # ------------------------------------------------------------------
    with tab_categories:
        st.markdown("##### 🏷️ Category Management")

        cat_col1, cat_col2 = st.columns([2, 1])

        with cat_col1:
            try:
                cats_data = client.get_categories(page=1, page_size=100)
                cats_items = cats_data.get("items", [])
                if cats_items:
                    st.dataframe(pd.DataFrame(cats_items), use_container_width=True, hide_index=True)
                else:
                    st.info("No categories exist in the database.")
            except ApiError as e:
                st.error(f"Failed to load categories: {e.message}")

        with cat_col2:
            if is_admin:
                st.markdown("###### Add New Category")
                with st.form("create_cat_form", clear_on_submit=True):
                    new_cat_name = st.text_input("Category Name", placeholder="e.g. Italian Restaurant")
                    add_cat_btn = st.form_submit_button("Add Category", type="primary", use_container_width=True)

                if add_cat_btn:
                    if not new_cat_name.strip():
                        st.error("Category name cannot be empty.")
                    else:
                        with st.spinner("Adding category..."):
                            try:
                                client.create_category(new_cat_name.strip())
                                st.success(f"Category '{new_cat_name.strip()}' added!")
                                st.rerun()
                            except ApiError as e:
                                st.error(f"Failed to add category: {e.message}")
            else:
                st.info("Only administrators can add new categories.")
