import streamlit as st
from logic.auth_utils import ensure_authenticated
from logic.manager import Manager
import pandas as pd
import time


class AdminPage:
    def __init__(self):
        ensure_authenticated(role_required='super')
        self.manager = Manager()


    def register_admin_section(self):
        """Section for adding new admins to the system."""
        st.header("Admin Registration")
        username = st.text_input("Admin Username")
        password = st.text_input("Password", type="password")
        role = st.selectbox("Role", ["basic"])
        
        if st.button("Add to System"):
            success, message = self.manager.register_basic_admin(username, password, role)
            if success:
                st.success(message)
                time.sleep(1.5)
                st.rerun()
            else:
                st.error(message)


    def bulk_upload_section(self):
        """Section for bulk uploading employees via Excel or CSV."""
        st.header("Bulk Employee Upload")
        st.info("Upload an Excel or CSV file with columns: Name, Role, Contract Type")
        uploaded_file = st.file_uploader("Choose a file", type=["xlsx", "xls", "csv"])
        
        if uploaded_file is not None:
            if st.button("Upload Data", use_container_width=True):
                try:
                    # Check the file extension to determine the correct pandas reading method
                    if uploaded_file.name.endswith('.csv'):
                        df = pd.read_csv(uploaded_file)
                    else:
                        df = pd.read_excel(uploaded_file)
                        
                    success, message = self.manager.upload_bulk_employees(df)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
                except Exception as e:
                    st.error(f"Error reading file: {e}")


    def display_admins_table(self):
        """Displays the admins with a custom layout and delete buttons."""
        st.header("Registered Admins")
        admins_df = self.manager.get_all_admins()
        
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
        st.header("Delete Admin Account")
        with st.form("delete_admin_form", clear_on_submit=True):
            id_to_delete = st.number_input("Admin ID", value=None, placeholder="Enter the ID of the admin to delete. 1 is not deletable.")
            submitted = st.form_submit_button("Delete Admin")
            if submitted:
                if id_to_delete == 1:
                    st.error("Cannot delete the default super admin.")
                    return
                
                success, message = self.manager.delete_admin(id_to_delete)
                if success:
                    st.success(message)
                    time.sleep(1.5)
                    st.rerun()
                else:
                    st.error(message)


    def render_page(self):
        st.sidebar.title(f"Welcome, {st.session_state['username']}!")
        
        st.sidebar.markdown("---")
        if st.sidebar.button("Refresh Data"):
            st.rerun()
        if st.sidebar.button("Logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

        # 2x2 Grid Layout Construction
        top_left, top_right = st.columns(2, gap="large")
        with top_left:
            with st.container(border=True):
                self.register_admin_section()
        with top_right:
            with st.container(border=True):
                self.bulk_upload_section()
                
        bottom_left, bottom_right = st.columns(2, gap="large")
        with bottom_left:
            with st.container(border=True):
                self.display_admins_table()
        with bottom_right:
            with st.container(border=True):
                self.delete_admin_section()


if __name__ == "__main__":
    page = AdminPage()
    page.render_page()