"""Login and Registration view with JWT session storage."""

import streamlit as st

from frontend.api_client import ApiError
from frontend.state import get_api_client, login_user
from frontend.utils.ui_helpers import render_custom_css, render_header


def render_login_view() -> None:
    """Render Login and Registration screen."""
    render_custom_css()

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        render_header(
            title="Business Mention Resolution",
            subtitle="Sign in to access catalog resolution, smart AI assistant & review workflows",
            icon="🏢",
        )

        tab_login, tab_register = st.tabs(["🔐 Sign In", "📝 Create Account"])

        client = get_api_client()

        with tab_login:
            st.markdown("##### Enter your credentials")

            with st.form("login_form", clear_on_submit=False):
                username = st.text_input("Username", value="admin", placeholder="e.g. admin", key="login_username")
                password = st.text_input(
                    "Password",
                    value="admin",
                    type="password",
                    placeholder="Enter password",
                    key="login_password",
                )

                submit_btn = st.form_submit_button("Sign In", use_container_width=True, type="primary")

            if submit_btn:
                if not username.strip() or not password:
                    st.error("Please provide both username and password.")
                else:
                    with st.spinner("Authenticating..."):
                        try:
                            token_resp = client.login(username=username.strip(), password=password)
                            token = token_resp.get("access_token")

                            if not token:
                                st.error("Authentication failed: No token returned.")
                            else:
                                client.set_token(token)
                                me_resp = client.get_me()
                                login_user(token=token, user=me_resp)
                                st.success(f"Welcome back, **{me_resp.get('username')}**!")
                                st.rerun()

                        except ApiError as e:
                            st.error(f"Authentication failed: {e.message}")
                        except Exception as e:
                            st.error(f"Unexpected error: {str(e)}")

            st.markdown(
                """
                <div style="margin-top: 15px; padding: 10px 14px; background: rgba(59, 130, 246, 0.1); border-radius: 8px; font-size: 0.85rem; color: #94a3b8;">
                    💡 <b>Default credentials:</b> Username <code>admin</code> / Password <code>admin</code> (Role: <b>admin</b>)
                </div>
                """,
                unsafe_allow_html=True,
            )

        with tab_register:
            st.markdown("##### Register a new account")

            with st.form("register_form", clear_on_submit=True):
                reg_username = st.text_input("New Username", placeholder="Choose a username", key="reg_username")
                reg_password = st.text_input(
                    "New Password",
                    type="password",
                    placeholder="Enter a strong password",
                    key="reg_password",
                )
                reg_role = st.selectbox(
                    "Role",
                    options=["viewer", "reviewer", "admin"],
                    index=0,
                    help="Admin has full CRUD permissions, Reviewer can review/resolve, Viewer has read-only access.",
                )

                reg_submit = st.form_submit_button("Register Account", use_container_width=True)

            if reg_submit:
                if not reg_username.strip() or not reg_password:
                    st.error("Please provide both username and password.")
                elif len(reg_password) < 4:
                    st.error("Password must be at least 4 characters long.")
                else:
                    with st.spinner("Creating account..."):
                        try:
                            user_resp = client.register(
                                username=reg_username.strip(),
                                password=reg_password,
                                role=reg_role,
                            )
                            st.success(
                                f"Account **{user_resp.get('username')}** ({user_resp.get('role')}) created successfully! Please sign in."
                            )
                        except ApiError as e:
                            st.error(f"Registration failed: {e.message}")
                        except Exception as e:
                            st.error(f"Unexpected error: {str(e)}")
