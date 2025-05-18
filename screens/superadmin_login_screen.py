from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty
from kivy.app import App
import bcrypt  # make sure this is at the top of your file

class SuperAdminLoginScreen(Screen):
    username = StringProperty("")
    password = StringProperty("")
    error_message = StringProperty("")

    def login(self):
        """Handle superadmin login logic."""
        app = App.get_running_app()

        # Read values directly from the input widgets using their ids
        entered_username = self.ids.username.text.strip()
        entered_password = self.ids.password.text.strip()

        if not entered_username or not entered_password:
            self.error_message = "Username and password are required"
            return

        user = app.db.get_user(entered_username)

        if user and user['role'] == 'super_admin' and bcrypt.checkpw(entered_password.encode(), user['password'].encode()):
            app.current_user = {
                'id': user['id'],  # ✅ Add this line
                'username': entered_username,
                'role': 'super_admin'
            }
            self.manager.current = 'home'

        else:
            print("Setting error message:", self.error_message)
