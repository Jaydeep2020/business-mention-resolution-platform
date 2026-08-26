"""Session state management and authentication helper functions."""

from typing import Any, Dict, Optional
import streamlit as st

from frontend.api_client import ApiClient
from frontend.config import AppConfig


def init_session_state() -> None:
    """Initialize all Streamlit session state keys with default values."""
    if "token" not in st.session_state:
        st.session_state["token"] = None

    if "user" not in st.session_state:
        st.session_state["user"] = None

    if "catalog_url" not in st.session_state:
        st.session_state["catalog_url"] = AppConfig.DEFAULT_CATALOG_URL

    if "document_url" not in st.session_state:
        st.session_state["document_url"] = AppConfig.DEFAULT_DOCUMENT_URL

    if "active_nav" not in st.session_state:
        st.session_state["active_nav"] = "Dashboard"

    if "selected_mention_id" not in st.session_state:
        st.session_state["selected_mention_id"] = None

    if "api_client" not in st.session_state:
        st.session_state["api_client"] = ApiClient(
            catalog_url=st.session_state["catalog_url"],
            document_url=st.session_state["document_url"],
            token=st.session_state["token"],
        )
    else:
        # Keep client URLs and token in sync
        client: ApiClient = st.session_state["api_client"]
        client.catalog_url = st.session_state["catalog_url"].rstrip("/")
        client.document_url = st.session_state["document_url"].rstrip("/")
        client.set_token(st.session_state["token"])


def get_api_client() -> ApiClient:
    """Get the initialized ApiClient from session state."""
    init_session_state()
    return st.session_state["api_client"]


def is_authenticated() -> bool:
    """Return True if user is logged in with a valid token and user profile."""
    init_session_state()
    return bool(st.session_state.get("token") and st.session_state.get("user"))


def get_current_user() -> Optional[Dict[str, Any]]:
    """Return current user dict or None."""
    init_session_state()
    return st.session_state.get("user")


def get_user_role() -> str:
    """Return the normalized role string for the current user (e.g. 'admin', 'reviewer', 'viewer')."""
    user = get_current_user()
    if not user:
        return "guest"
    return str(user.get("role", "viewer")).lower()


def has_role(*allowed_roles: str) -> bool:
    """Check if current user matches any of the specified roles."""
    current_role = get_user_role()
    if current_role == "admin":
        return True
    return current_role in [r.lower() for r in allowed_roles]


def login_user(token: str, user: Dict[str, Any]) -> None:
    """Store credentials and user profile in session state."""
    st.session_state["token"] = token
    st.session_state["user"] = user
    get_api_client().set_token(token)


def logout_user() -> None:
    """Clear credentials and session data."""
    st.session_state["token"] = None
    st.session_state["user"] = None
    st.session_state["selected_mention_id"] = None
    get_api_client().set_token(None)
