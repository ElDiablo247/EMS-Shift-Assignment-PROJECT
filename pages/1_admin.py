import streamlit as st
from logic.auth_utils import ensure_authenticated
from logic.auth_manager import AuthManager
import time


class AdminPage:
    def __init__(self):
        ensure_authenticated(role_required='super')
        self.auth_manager = AuthManager()


    def register_admin_section(self):
        st.caption("Enter admin details for registration.")
        with st.form("register_admin_form", clear_on_submit=True):
            username = st.text_input("Admin Username", placeholder="Enter username")
            password = st.text_input("Password", type="password", placeholder="Enter password", help="Password must be at least 8 characters long, and include at least one uppercase letter and one symbol.")
            confirm_password = st.text_input("Confirm Password", type="password", placeholder="Re-enter password", help="Re-enter the password for confirmation.")
            submitted = st.form_submit_button("Add to System")
            if submitted:
                success, message = self.auth_manager.register_basic_admin(username, password, confirm_password, "basic")
                if success:
                    st.success(message)
                    time.sleep(2.0)
                    st.rerun()
                else:
                    st.error(message)


    def display_admins_table(self):
        """Displays the admins in a table."""
        st.header("Registered Admins")
        admins_df = self.auth_manager.get_all_admins()
        
        if admins_df.empty:
            st.info("No admins found.")
            return
        column_config = {
            "id": st.column_config.NumberColumn("ID"),
            "username": st.column_config.TextColumn("Username"),
            "password_hash": None, # Hide this column completely
            "role": st.column_config.TextColumn("Role")
        }
        st.dataframe(
            admins_df,
            column_config=column_config,
            width='stretch',
            hide_index=True
        )


    def delete_admin_section(self):
        st.caption("Enter the admin ID you wish to delete.")
        with st.form("delete_admin_form", clear_on_submit=True):
            id_to_delete = st.number_input("Admin ID", min_value=1, value=None, placeholder="Admin ID to delete", help="Note: The default super admin (ID 1) cannot be deleted.")
            submitted = st.form_submit_button("Delete Admin")
            if submitted:
                if id_to_delete is None:
                    st.error("Please enter an Admin ID to delete.")
                elif id_to_delete == 1:
                    st.error("Cannot delete the default super admin.")
                else:
                    success, message = self.auth_manager.delete_admin(id_to_delete)
                    if success:
                        st.success(message)
                        time.sleep(2.0)
                        st.rerun()
                    else:
                        st.error(message)


    def render_page(self):
        # Sidebar: Action widgets with expanders
        with st.sidebar:
            with st.expander("Register Admin", expanded=True):
                self.register_admin_section()
            with st.expander("Delete Admin", expanded=False):
                self.delete_admin_section()
        
        # Main area: Display only 
        with st.container(border=True, width='content'):
            self.display_admins_table()


if __name__ == "__main__":
    page = AdminPage()
    page.render_page()