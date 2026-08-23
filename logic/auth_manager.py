from repository.dao import DatabaseAccess
import bcrypt
import re


class AuthManager:
    def __init__(self):
        self.dao = DatabaseAccess()


    def admins_exist(self):
        """Checks if there are any admins in the database."""
        return self.dao.admins_exist()


    def register_super_admin(self, username, password, confirm_password):
        """Registers a new super admin if the username is unique and passwords match."""
        if not username or not password or not confirm_password:
            return False, "All fields are required."
        if password != confirm_password:
            return False, "Passwords do not match."
        if not self.is_password_strong(password):
            return False, "Password must be at least 8 characters long, and include at least one uppercase letter and one symbol."
        if self.dao.get_admin_details(username)[0] is not None:
            return False, "Username already exists."

        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        success = self.dao.add_super_admin(username, hashed_pw, role='super')
        if success:
            return True, "Super Admin registered successfully."
        else:
            return False, "Error registering Super Admin. Please try again."


    def register_basic_admin(self, username, password, confirm_password, role):
        """Registers a new basic admin if the username is unique and passwords match, through the admin control panel."""
        if not username or not password or not confirm_password or not role:
            return False, "All fields are required."
        if password != confirm_password:
            return False, "Passwords do not match."
        if not self.is_password_strong(password):
            return False, "Password must be at least 8 characters long, and include at least one uppercase letter and one symbol."

        if self.dao.get_admin_details(username)[0] is not None:
            return False, "Username already exists."
        
        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        success = self.dao.add_basic_admin(username, hashed_pw, role=role)
        if success:
            return True, "Basic admin registered successfully."
        else:
            return False, "Error registering basic admin. Please try again."


    def get_all_admins(self):
        """Pass-through to DAO."""
        return self.dao.get_all_admins()


    def delete_admin(self, admin_id):
        if self.dao.delete_admin(admin_id):
            return True, f"Admin with ID {admin_id} has been deleted."
        return False, "Failed to delete admin. Please check the ID and try again."


    def verify_login(self, username, password):
        """
        Verifies user credentials and returns their role on success.
        Returns: (bool: success, str: role or None)
        """
        password_hash, role = self.dao.get_admin_details(username)
        if password_hash:
            if bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8')):
                return True, role
        return False, None


    def is_password_strong(self, password):
        """
        Verifies if a password meets the security constraints.
        - At least 8 characters
        - At least one uppercase letter
        - At least one symbol
        Returns True if the password is strong, False otherwise.
        """
        if len(password) < 8:
            return False
        if not re.search(r'[A-Z]', password):
            return False
        if not re.search(r'[^a-zA-Z0-9]', password):
            return False
        return True