from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.properties import StringProperty, ListProperty, NumericProperty, BooleanProperty
from kivy.clock import Clock
from restaurant_pos.screens.edit_menu_screen import EditMenuScreen
from restaurant_pos.screens.order_screen import OrderScreen
from restaurant_pos.screens.inventory_screen import InventoryScreen
from restaurant_pos.screens.order_history_screen import OrderHistoryScreen
from restaurant_pos.screens.user_login_screen import UserLoginScreen
from restaurant_pos.screens.superadmin_login_screen import SuperAdminLoginScreen
from restaurant_pos.screens.admin_login_screen import AdminLoginScreen
from restaurant_pos.screens.create_account_screen import CreateAccountScreen
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from restaurant_pos.screens.manage_accounts_screen import ManageAccountsScreen
from kivy.clock import Clock
from kivy.metrics import Metrics
from kivy.utils import platform

import json
import threading
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'data'))
from database import Database
import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Set window size for tablet (you can adjust this)
Window.size = (1024, 600)
Builder.load_file("main.kv")


class SplashScreen(Screen):
    def on_enter(self):
        threading.Thread(target=self.load_app).start()

    def load_app(self):
        try:
            app = App.get_running_app()
            app.db.initialize()  # ✅ Already in place
            app.load_settings()  # ✅ Loads JSON
            app.create_required_folders()  # ✅ Checks folders
        except Exception as e:
            print(f"❌ Error during splash loading: {e}")
        finally:
            Clock.schedule_once(self.go_to_next_screen, 2)  # slight delay for user experience

    def go_to_next_screen(self, dt=None):
        app = App.get_running_app()
        target_screen = app.settings.get("startup_screen", "login")
        self.manager.current = target_screen



class LoginScreen(Screen):
    invalid = BooleanProperty(False)
    error_message = StringProperty("")

    def login_as(self, role):
        if role == 'user':
            self.manager.current = 'user_login_screen'
        elif role == 'admin':
            self.manager.current = 'admin_login_screen'
        elif role == 'super_admin':
            self.manager.current = 'superadmin_login'

class HomeScreen(Screen):
    username = StringProperty("Guest")
    print(Window.dpi)  # See what your DPI is to adjust sp()

    def on_pre_enter(self):
        app = App.get_running_app()
        if app.current_user:
            self.username = app.current_user['username']
            role = app.current_user['role']

            # Enable/disable buttons by role
            self.ids.edit_menu_btn.disabled = role not in ['admin', 'super_admin']
            self.ids.inventory_btn.disabled = role not in ['admin', 'super_admin']
            self.ids.order_history_btn.disabled = role not in ['admin', 'super_admin']
        else:
            self.username = "Guest"

    def open_user_menu(self):
        app = App.get_running_app()
        layout = BoxLayout(orientation='vertical', spacing=10, padding=10)

        popup = Popup(
            title='Account Menu',
            content=layout,
            size_hint=(None, None),
            size=(300, 200),
            auto_dismiss=True
        )

        if app.current_user and app.current_user['role'] == 'super_admin':
            create_btn = Button(text='Create New Account', size_hint_y=None, height=40)
            create_btn.bind(on_release=lambda x: self.go_to_register(popup))
            layout.add_widget(create_btn)

            manage_btn = Button(text='Manage Accounts', size_hint_y=None, height=40)
            manage_btn.bind(on_release=lambda x: self.go_to_manage_accounts(popup))
            layout.add_widget(manage_btn)

        logout_btn = Button(text='Logout', size_hint_y=None, height=40)
        logout_btn.bind(on_release=lambda x: self.logout(popup))
        layout.add_widget(logout_btn)

        popup.open()

    def go_to_manage_accounts(self, popup):
        popup.dismiss()
        self.manager.current = 'manage_accounts_screen'

    def go_to_register(self, popup):
        popup.dismiss()
        self.manager.current = 'create_account_screen'

    def logout(self, popup):
        popup.dismiss()
        App.get_running_app().current_user = None
        self.manager.current = 'login'

if platform == 'android':
    from plyer import permission
else:
    permission = None

class RestaurantApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db = Database()
        self.current_user = None  # ✅ Initialize current_user here
        self.settings = {}  # <-- we'll store loaded settings here

    def load_settings(self):
        try:
            with open("data/settings.json", "r") as f:
                self.settings = json.load(f)
            print("✅ Settings loaded:", self.settings)
        except Exception as e:
            print("⚠️ Could not load settings:", e)
            self.settings = {
                "theme": "light",
                "language": "en",
                "company_name": "My POS Restaurant"
            }
    def build(self):
        print("Density:", Metrics.density)
        print("DPI:", Metrics.dpi)
        print("Screen Size:", Window.size[0], "x", Window.size[1])


        self.create_default_superadmin()
        # Create screen manager with proper transition
        self.sm = ScreenManager(transition=SlideTransition())

        self.sm.add_widget(SplashScreen(name='splash'))


        # Add screens
        screens = [
            LoginScreen(name='login'),
            HomeScreen(name='home'),
            EditMenuScreen(name='edit_menu'),
            OrderScreen(name='order_screen'),
            InventoryScreen(name='inventory'),
            OrderHistoryScreen(name='order_history'),
            SuperAdminLoginScreen(name='superadmin_login'),
            UserLoginScreen(name='user_login_screen'),
            AdminLoginScreen(name='admin_login_screen'),
            CreateAccountScreen(name='create_account_screen', db=self.db),
            ManageAccountsScreen(name='manage_accounts_screen')
        ]

        for screen in screens:
            self.sm.add_widget(screen)

            # Start from the splash screen
            self.sm.current = 'splash'



        Clock.schedule_once(self.request_storage_permission, 1)
        return self.sm

    def create_default_superadmin(self):
        conn = self.db.conn
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", ('Tristan',))
        if not cursor.fetchone():
            self.db.create_user('Tristan', hash_password('malupit123'), 'super_admin')

    def on_stop(self):
        # Close database connection when app stops
        self.db.close()

    def has_permission(self, screen_name):
        if not self.current_user:
            return False
        role = self.current_user['role']
        access = {
            'user': ['OrderScreen', 'OrderHistoryScreen'],
            'admin': ['OrderScreen', 'OrderHistoryScreen', 'EditMenuScreen', 'InventoryScreen'],
            'super_admin': ['OrderScreen', 'OrderHistoryScreen', 'EditMenuScreen', 'InventoryScreen',
                            'CreateAccountScreen']
        }
        return screen_name in access.get(role, [])

    def create_required_folders(self):
        folders = [
            "data/images",
            "data/backups"
            "data/excel_receipts"
        ]
        for folder in folders:
            os.makedirs(folder, exist_ok=True)
        print("📁 Required folders checked/created.")

    def request_storage_permission(self, dt):
        if permission:
            if not permission.check_permission("android.permission.WRITE_EXTERNAL_STORAGE"):
                permission.request_permissions(["android.permission.WRITE_EXTERNAL_STORAGE"])
            else:
                print("Storage permission already granted")
        else:
            print("Not on Android - no need to request storage permission")

if __name__ == '__main__':
    # Create data directory if it doesn't exist
    if not os.path.exists('data'):
        os.makedirs('data')

    RestaurantApp().run()



