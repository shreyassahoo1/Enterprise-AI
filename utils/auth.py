"""
utils/auth.py
-------------
Simple username/password authentication with role-based access.
Credentials are read from .env via Config. Two roles: "admin" and "user".
"""

import logging
from typing import Optional

import streamlit as st

from config import Config

logger = logging.getLogger(__name__)


def check_credentials(username: str, password: str) -> Optional[str]:
    """
    Validate credentials against Config values.

    Returns:
        "admin", "user", or None if invalid.
    """
    if username == Config.ADMIN_USERNAME and password == Config.ADMIN_PASSWORD:
        return "admin"
    if username == Config.USER_USERNAME and password == Config.USER_PASSWORD:
        return "user"
    return None


def require_auth(allowed_roles: tuple = ("admin", "user")) -> None:
    """
    Gate page access behind authentication.

    - If not authenticated, renders a centered login form and calls st.stop().
    - If authenticated but role not in allowed_roles, shows "Access restricted."
      and calls st.stop().
    - Otherwise returns normally so the rest of the page can render.
    """
    # Initialize auth state
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if "role" not in st.session_state:
        st.session_state["role"] = None
    if "auth_username" not in st.session_state:
        st.session_state["auth_username"] = ""

    # Already authenticated — check role
    if st.session_state["authenticated"]:
        if st.session_state["role"] not in allowed_roles:
            st.markdown(
                '<div style="text-align:center; margin-top:100px; '
                'font-family:Lora,serif; font-size:1.4rem; color:#1C3D2E;">'
                "Access restricted.</div>",
                unsafe_allow_html=True,
            )
            st.stop()
        return

    # Not authenticated — render login form
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown("<h2>Sign in</h2>", unsafe_allow_html=True)
    st.markdown(
        '<p class="login-subtitle">Enterprise Chatbot</p>',
        unsafe_allow_html=True,
    )

    username = st.text_input("Username", key="login_username", placeholder="Username")
    password = st.text_input(
        "Password", type="password", key="login_password", placeholder="Password"
    )

    if st.button("Sign in", use_container_width=True, key="btn_sign_in"):
        role = check_credentials(username, password)
        if role:
            st.session_state["authenticated"] = True
            st.session_state["role"] = role
            st.session_state["auth_username"] = username
            logger.info("User '%s' authenticated with role '%s'", username, role)
            st.rerun()
        else:
            st.markdown(
                '<p style="color:#C0392B; text-align:center; font-size:13px; '
                'margin-top:8px;">Invalid credentials.</p>',
                unsafe_allow_html=True,
            )

    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()


def render_sign_out() -> None:
    """Render a 'Sign out' button in the sidebar that clears auth state."""
    if st.session_state.get("authenticated"):
        if st.button("Sign out", use_container_width=True, key="btn_sign_out"):
            st.session_state["authenticated"] = False
            st.session_state["role"] = None
            st.session_state["auth_username"] = ""
            st.rerun()
