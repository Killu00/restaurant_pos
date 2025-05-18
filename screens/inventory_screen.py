from kivy.uix.screenmanager import Screen
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.metrics import dp, sp


class InventoryScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def submit_inventory_item(self):
        name = self.ids.item_name_input.text.strip()
        quantity_text = self.ids.item_quantity_input.text.strip()

        try:
            quantity = int(quantity_text)
            app = App.get_running_app()
            app.db.add_or_update_inventory_item(name, quantity)
            self.ids.item_name_input.text = ''
            self.ids.item_quantity_input.text = ''
            self.update_inventory_display()
        except ValueError:
            print("Invalid quantity entered.")

    def update_inventory_display(self):
        container = self.ids.inventory_list
        container.clear_widgets()

        app = App.get_running_app()
        items = app.db.get_inventory_items()

        for item in items:
            name = item['name']
            quantity = item['quantity']

            row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(10))
            row.add_widget(Label(text=name, size_hint_x=0.5, color=(0, 0, 0, 1), font_size=sp(18)))
            row.add_widget(Label(text=str(quantity), size_hint_x=0.2, color=(0, 0, 0, 1), font_size=sp(18)))

            edit_button = Button(text="Edit", size_hint_x=0.3, font_size=sp(16))
            edit_button.bind(on_press=lambda btn, n=name, q=quantity: self.open_edit_popup(n, q))
            row.add_widget(edit_button)

            container.add_widget(row)

    def open_edit_popup(self, item_name, current_quantity):
        layout = BoxLayout(orientation='vertical', spacing=10, padding=10)

        qty_input = TextInput(text=str(current_quantity), multiline=False, input_filter='int', font_size=sp(16))
        layout.add_widget(Label(text=f"Edit quantity for '{item_name}':", font_size=sp(18)))
        layout.add_widget(qty_input)

        btn_layout = BoxLayout(size_hint_y=0.3, spacing=10)

        save_btn = Button(text="Save", font_size=sp(16))
        delete_btn = Button(text="Delete", background_color=(1, 0.3, 0.3, 1), font_size=sp(16))
        cancel_btn = Button(text="Cancel", font_size=sp(16))

        btn_layout.add_widget(save_btn)
        btn_layout.add_widget(delete_btn)
        btn_layout.add_widget(cancel_btn)

        layout.add_widget(btn_layout)

        popup = Popup(title="Edit Inventory", content=layout, size_hint=(0.7, 0.4))

        def save_changes(instance):
            try:
                new_qty = int(qty_input.text)
                App.get_running_app().db.set_inventory_quantity(item_name, new_qty)
                popup.dismiss()
                self.update_inventory_display()
            except ValueError:
                print("Invalid quantity")

        def delete_item(instance):
            App.get_running_app().db.delete_inventory_item(item_name)
            popup.dismiss()
            self.update_inventory_display()

        save_btn.bind(on_press=save_changes)
        delete_btn.bind(on_press=delete_item)
        cancel_btn.bind(on_press=lambda *args: popup.dismiss())
        popup.open()

    def on_pre_enter(self):
        self.update_inventory_display()
