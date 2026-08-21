import streamlit as st
from logic.auth_manager import AuthManager
import time


st.set_page_config(page_title="Schedule Generator and EMS management", layout="wide")


class Homepage:
    def __init__(self):
        self.auth_manager = AuthManager()


    def render_login(self):
        """Renders the manual login form."""
        st.title("EMS Administration Login")
        with st.form("login_form", width="content"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                success, role = self.auth_manager.verify_login(username, password)
                if success:
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = username
                    st.session_state['role'] = role
                    st.rerun()
                else:
                    st.error("Invalid username or password.")


    def render_registration(self):
        """Renders the manual registration form."""
        st.title("Initial Admin Registration")
        st.info("No administrators found. Please create the first SUPER Admin account.")
        with st.form("registration_form", width="content"):
            st.caption("SUPER Admin Registration. This account will have full access to the system. NOTE: The password must be at least 8 characters long, and include at least one uppercase letter and one symbol.")
            username = st.text_input("Username", placeholder="Enter username")
            password = st.text_input("Password", type="password", placeholder="Enter password")
            confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm password")
            if st.form_submit_button("Register SUPER Admin"):
                success, message = self.auth_manager.register_super_admin(username, password, confirm_password)
                if success:
                    st.success(message)
                    st.info("Registration successful. Please log in with your new credentials.")
                    time.sleep(1.5)
                else:
                    st.error(message)


    def run(self):
        """Handles the main logic flow for the Log in/Registration process, including access control and rendering."""
        if st.session_state.get("logged_in"):
            pages = []
            # Super admin gets the Control Panel added first
            if st.session_state.get("role") == "super":
                pages.append(st.Page("pages/1_admin.py", title="Admin Configuration"))
            
            # Both roles get these pages
            pages.append(st.Page("pages/2_employees.py", title="EMS Staff Configuration"))
            pages.append(st.Page("pages/3_shifts.py", title="Shifts Configuration"))
            pages.append(st.Page("pages/4_constraints.py", title="Constraints Configuration"))
            pages.append(st.Page("pages/5_assignments.py", title="Schedule Configuration"))
            pages.append(st.Page("pages/9_developer.py", title="Dev Tools"))

            pg = st.navigation(pages, position="top")
            
            # Sidebar: Refresh & Logout 
            with st.sidebar:
                # User info bar (main area)
                st.caption(f"Logged in as {st.session_state['username']} ({st.session_state['role']})")
                if st.button("Refresh Data", use_container_width=True, key="sidebar_refresh"):
                    st.rerun()
                if st.button("Logout", use_container_width=True, key="sidebar_logout"):
                    for key in list(st.session_state.keys()):
                        del st.session_state[key]
                    st.rerun()
                st.divider()
            
            pg.run()
        else:
            if self.auth_manager.admins_exist():
                pg = st.navigation([st.Page(self.render_login, title="Log In")])
            else:
                pg = st.navigation([st.Page(self.render_registration, title="First-Time Setup")])
            pg.run()


if __name__ == "__main__":
    homepage = Homepage()
    homepage.run() 