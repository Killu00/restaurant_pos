from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.app import App
from kivy.metrics import sp  # Import this for scalable font sizes

class ManageAccountsScreen(Screen):
    def on_pre_enter(self):
        self.display_users()

    def display_users(self):
        self.ids.user_list.clear_widgets()
        app = App.get_running_app()
        users = app.db.get_all_users()

        for user in users:
            if user['role'] != 'super_admin':
                box = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=10)

                box.add_widget(Label(text=user['username'], size_hint_x=0.4, font_size=sp(18)))
                box.add_widget(Label(text=user['role'], size_hint_x=0.3, font_size=sp(18)))

                delete_btn = Button(
                    text='Delete',
                    size_hint_x=0.3,
                    background_color=(1, 0, 0, 1),
                    font_size=sp(18)
                )
                delete_btn.bind(on_release=lambda btn, u=user: self.confirm_delete(u))
                box.add_widget(delete_btn)

                self.ids.user_list.add_widget(box)

    def confirm_delete(self, user):
        layout = BoxLayout(orientation='vertical', spacing=10, padding=10)
        layout.add_widget(Label(text=f"Are you sure you want to delete '{user['username']}'?", font_size=sp(18)))

        btn_layout = BoxLayout(size_hint_y=None, height=40, spacing=10)
        yes_btn = Button(text='Yes', font_size=sp(16))
        no_btn = Button(text='No', font_size=sp(16))
        btn_layout.add_widget(yes_btn)
        btn_layout.add_widget(no_btn)

        layout.add_widget(btn_layout)

        popup = Popup(title='Confirm Delete', content=layout, size_hint=(None, None), size=(400, 200))
        yes_btn.bind(on_release=lambda x: self.delete_user(user, popup))
        no_btn.bind(on_release=popup.dismiss)
        popup.open()

    def delete_user(self, user, popup):
        App.get_running_app().db.delete_user(user['id'])
        popup.dismiss()
        self.display_users()
