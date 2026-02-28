import streamlit as st
import pandas as pd
from logic.manager import Manager

class Homepage:
    def __init__(self):
        self.manager = Manager()
        st.set_page_config(page_title="Shifts Planner for EMS", layout="wide")


    def render_main_area(self):
        """Handles the title, general info, and emptyy database button"""
        st.title("Shifts Planner for EMS")
        st.write("Use this tool to manage your staff and generate weekly plans.")




    def add_employee_section(self):
        """Handles all inputs and logic in the sidebar"""
        st.sidebar.header("Employee Registration")
        
        name = st.sidebar.text_input("Employee Name")
        qualification = st.sidebar.selectbox("Role", ["Paramedic", "Assistant"])
        contract_type = st.sidebar.selectbox("Contract Type", ["Full-Time", "Part-Time", "Flexible"])
        
        if st.sidebar.button("Add to System"):
            if self.manager.add_employee(name, qualification, contract_type):
                st.sidebar.success("Employee has been added.")
            else:
                st.sidebar.error("Failed to add employee. Check console for details.")


    def add_shift_section(self):
        """Handles the input and display logic for Shifts"""
        st.sidebar.markdown("---")
        st.sidebar.header("Shift Management")

        shift_name = st.sidebar.text_input("Shift Name")
        shift_start = st.sidebar.time_input("Start Time", value=None)
        shift_end = st.sidebar.time_input("End Time", value=None)
        shift_duration = st.sidebar.number_input("Shift Duration (hours)", max_value=12.0, step=0.5)

        if st.sidebar.button("Add Shift"):
            if self.manager.add_shift(shift_name, shift_start, shift_end, shift_duration):
                st.sidebar.success("Shift has been added.")
                st.rerun() 
            else:
                st.sidebar.error("Failed to add shift. Check console for details.")


    def add_employees_bulk(self):
        """Handles bulk upload of employees via CSV"""
        st.header("Upload CSV Employee File")

        uploaded_file = st.file_uploader("Upload CSV", type=["csv"], key="emp_bulk_upload")
        
        if uploaded_file is not None:
            if st.button("Process File"):
                try:
                    df = pd.read_csv(uploaded_file)
                    success_count = 0

                    for _, row in df.iterrows():
                        if self.manager.add_employee(row['name'], row['qualification'], row['contract_type']):
                            success_count += 1
                    
                    st.success(f"Success: {success_count}/{len(df)} employees added successfully.")
                except Exception as e:
                    st.error(f"Error processing file: {e}")


    def display_personnel(self):
        """Handles fetching and displaying the employee table"""
        st.header("Available Personnel")
        
        # Button to empty the employees database for testing purposes
        if st.button("Empty Employees Database"):
            if self.manager.empty_employee_database():
                st.success("All employee data has been cleared.")
            else:
                st.error("Failed to clear database. Check console for details.")
        
        # Fetch employee data and display in editable table
        personnel = self.manager.get_all_employees()
        if personnel.empty:
            st.info("No staff registered yet. Use the sidebar to add employees.")
            return

        # Configure the columns to use dropdowns (SelectboxColumn)
        column_config = {
            "id": st.column_config.NumberColumn("ID"),
            "name": st.column_config.TextColumn("Name"),
            "qualification": st.column_config.SelectboxColumn(
                "Role",
                options=["Paramedic", "Assistant"],
                required=True
            ),
            "contract_type": st.column_config.SelectboxColumn(
                "Contract Type",
                options=["Full-Time", "Part-Time", "Flexible"],
                required=True
            )
        }
        edited_df = st.data_editor(
            personnel,
            column_config=column_config,
            width='stretch',
            height=450,
            hide_index=True,
            key="employees_table_UI",
            disabled=["id"]
        )
        # The "Save Changes" button to commit edits to the database
        if st.button("Save Employee Changes"):
            if self.manager.update_employees(edited_df):
                st.success("Employee data updated successfully.")
                st.rerun()
            else:
                st.error("An error occurred while updating. Please check the console logs.")


    def display_shifts(self):
        """Handles fetching and displaying the shifts table"""

        st.header("Shifts")

        # Button to empty the shifts database for testing purposes
        if st.button("Empty Shifts Database"):
            if self.manager.empty_shifts_database():
                st.success("All shift data has been cleared.")
            else:
                st.error("Failed to clear database. Check console for details.")

        # Fetch shifts data and display in editable table
        shifts = self.manager.get_all_shifts()
        if shifts.empty:
            st.info("No shifts defined yet. Use the sidebar to add shifts.")
            return
        
        # Configure the columns to use appropriate types (e.g., TimeColumn for time fields)
        column_config = {
            "id": st.column_config.NumberColumn("ID"),
            "shift_name": st.column_config.TextColumn("Shift Name"),
            "shift_start": st.column_config.TimeColumn("Start Time", format="HH:mm"),
            "shift_end": st.column_config.TimeColumn("End Time", format="HH:mm"),
            "shift_duration": st.column_config.NumberColumn("Duration minus breaks(hrs)")
        }
        edited_df = st.data_editor(
            shifts,
            column_config=column_config,
            width='stretch',
            hide_index=True,
            key="shifts_table_UI",
            disabled=["id"]
        )
        # The "Save Changes" button to commit edits to the database
        if st.button("Save Shift Changes"):
            if self.manager.update_shifts(edited_df):
                st.success("Shift data updated successfully.")
                st.rerun()
            else:
                st.error("An error occurred while updating. Please check the console logs.")


    def run(self):
        """The main entry point that calls all other methods in order"""
        self.add_employee_section()
        self.add_shift_section()
        
        # Top row 50/50 split between main area and bulk upload of employees
        col_top_left, col_top_right = st.columns(2)
        with col_top_left:
            self.render_main_area()
            st.write("")
            st.write("")
            self.add_employees_bulk()
        with col_top_right:
            self.display_shifts()

        self.display_personnel()


if __name__ == "__main__":
    homepage = Homepage()
    homepage.run() 