from kivy.uix.screenmanager import Screen
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.properties import ObjectProperty
from kivy.app import App
from kivy.app import StringProperty
import sqlite3
import bcrypt

class AdminLoginScreen(Screen):
    username_input = ObjectProperty(None)
    password_input = ObjectProperty(None)
    error_message = StringProperty("")

    def login(self):
        username = self.ids.username.text
        password = self.ids.password.text

        import os
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(BASE_DIR, "..", "data", "restaurant.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT id, username, password, role FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        conn.close()

        if result:
            user_id, db_username, hashed_pw, role = result
            if bcrypt.checkpw(password.encode(), hashed_pw.encode()):
                if role == "admin":
                    app = App.get_running_app()
                    app.current_user = {
                        'id': user_id,
                        'username': db_username,
                        'role': 'admin'
                    }
                    self.manager.current = "home"
                else:
                    self.show_error("Access denied: Not an admin.")
            else:
                self.show_error("Incorrect password.")
        else:
            self.show_error("User not found.")

    def show_error(self, message):
        self.error_message = message
