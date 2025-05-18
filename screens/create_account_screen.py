from kivy.uix.screenmanager import Screen
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.app import App
from restaurant_pos.database import Database
from restaurant_pos.utils import hash_password



class CreateAccountScreen(Screen):
    def __init__(self, db=None, **kwargs):
        super().__init__(**kwargs)
        self.db = db  # ✅ Use the shared database instance

    def create_account(self):
        app = App.get_running_app()
        current_user = app.current_user

        if not current_user or current_user.get('role') != 'super_admin':
            self.show_popup("Access Denied", "Only super admin can create accounts.")
            return

        username = self.ids.username_input.text.strip()
        password = self.ids.password_input.text.strip()
        confirm_password = self.ids.confirm_password_input.text.strip()
        role = self.ids.role_spinner.text

        if role == 'superadmin':
            self.show_popup("Error", "You cannot create another super admin.")
            return

        if not username or not password or not confirm_password or role not in ['admin', 'user']:
            self.show_popup("Error", "Fill all fields and select a valid role.")
            return

        if password != confirm_password:
            self.show_popup("Error", "Passwords do not match.")
            return

        if self.db.get_user_by_username(username):
            self.show_popup("Error", "Username already exists.")
            return

        password_hash = hash_password(password)
        self.db.create_user(username, password_hash, role)
        self.show_popup("Success", f"{role.capitalize()} account created.")

        self.ids.username_input.text = ""
        self.ids.password_input.text = ""
        self.ids.confirm_password_input.text = ""
        self.ids.role_spinner.text = "Select Role"

    def show_popup(self, title, message):
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        content.add_widget(Label(text=message))
        close_button = Button(text='Close', size_hint_y=None, height='40dp')
        content.add_widget(close_button)

        popup = Popup(title=title, content=content,
                      size_hint=(None, None), size=(400, 200), auto_dismiss=False)
        close_button.bind(on_release=popup.dismiss)
        popup.open()




