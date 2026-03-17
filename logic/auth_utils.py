import streamlit as st

def ensure_authenticated(role_required=None):
    """
    Ensures the user is logged in and has the necessary permissions.
    """
    if not st.session_state.get("logged_in"):
        st.error("Session expired or you are not logged in. Please go to the home page.")
        if st.button("Go to Login"):
            st.rerun()
        st.stop()
    
    if role_required and st.session_state.get("role") != role_required:
        st.error(f"Access Denied: This page requires {role_required} permissions.")
        if st.button("Back"):
            st.switch_page("pages/2_employees.py")
        st.stop()