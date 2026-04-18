import streamlit as st
from logic.manager import Manager
import time


st.set_page_config(page_title="Shifts Planner for EMS", layout="wide")


class Homepage:
    def __init__(self):
        self.manager = Manager()


    def render_login(self):
        """Renders the manual login form."""
        st.title("EMS Administration Login")
        with st.form("login_form", width="content"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                success, role = self.manager.verify_login(username, password)
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
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            if st.form_submit_button("Register SUPER Admin"):
                success, message = self.manager.register_super_admin(username, password, confirm_password)
                if success:
                    st.success(message)
                    st.info("Registration successful. Please log in with your new credentials.")
                    time.sleep(1.5)
                    st.rerun()
                else:
                    st.error(message)


    def run(self):
        """Handles the main logic flow for the Log in/Registration process, including access control and rendering."""
        if st.session_state.get("logged_in"):
            pages = []
            # Super admin gets the Control Panel added first
            if st.session_state.get("role") == "super":
                pages.append(st.Page("pages/1_admin.py", title="Admin Control Panel"))
            
            # Both roles get these pages
            pages.append(st.Page("pages/2_employees.py", title="Staff Management"))
            pages.append(st.Page("pages/3_shifts.py", title="Shift Management"))
            pg = st.navigation(pages)
            pg.run()
        else:
            if self.manager.admins_exist():
                pg = st.navigation([st.Page(self.render_login, title="Log In")])
            else:
                pg = st.navigation([st.Page(self.render_registration, title="First-Time Setup")])
            pg.run()


if __name__ == "__main__":
    homepage = Homepage()
    homepage.run() 