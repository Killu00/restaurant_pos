from kivy.uix.screenmanager import Screen
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.properties import NumericProperty
from kivy.metrics import dp
from kivy.app import App


class CategoryButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_color = (0.2, 0.6, 0.8, 1)
        self.size_hint_y = None
        self.height = dp(50)
        self.font_size = dp(18)


class MenuItemBox(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = dp(50)
        self.spacing = dp(5)


class EditMenuScreen(Screen):
    current_category = NumericProperty(None, allownone=True)

    def on_enter(self):
        self.load_categories()

    def load_categories(self):
        self.ids.categories_container.clear_widgets()
        categories = App.get_running_app().db.get_categories()
        for cat in categories:
            btn = CategoryButton(
                text=cat['name'],
                on_press=lambda x, cat=cat: self.show_category_items(cat)
            )
            self.ids.categories_container.add_widget(btn)

    def show_category_items(self, category):
        self.current_category = category['id']
        self.ids.current_category_label.text = category['name']
        self.ids.items_container.clear_widgets()
        items = App.get_running_app().db.get_menu_items_by_category(category['id'])
        for item in items:
            self.add_item_to_layout(item)

    def add_item_to_layout(self, item):
        box = MenuItemBox()

        name_input = TextInput(
            text=item.get('name', 'Unnamed'),
            size_hint_x=0.5,
            font_size=dp(18),
            readonly=True,
            background_color=(0.9, 0.9, 0.9, 1)
        )

        price_input = TextInput(
            text=f"{item['price']:.2f}",
            size_hint_x=0.3,
            font_size=dp(18),
            input_filter='float',
            readonly=True,
            background_color=(1, 1, 1, 1)
        )

        del_btn = Button(
            text='Delete',
            size_hint_x=0.2,
            background_color=(0.8, 0.2, 0.2, 1),
            on_press=lambda x, i=item: self.delete_item(i['id'])
        )

        box.add_widget(name_input)
        box.add_widget(price_input)
        box.add_widget(del_btn)
        self.ids.items_container.add_widget(box)

    def show_add_category_popup(self):
        content = BoxLayout(orientation='vertical', spacing=dp(10))
        name_input = TextInput(hint_text='Category Name', size_hint_y=None, height=dp(50))
        content.add_widget(name_input)

        btn_layout = BoxLayout(size_hint_y=None, height=dp(50))
        popup = Popup(title='Add New Category', size_hint=(0.6, 0.3))
        btn_layout.add_widget(Button(text='Cancel', on_press=popup.dismiss))
        btn_layout.add_widget(Button(text='Add', on_press=lambda x: self.add_category(name_input.text)))
        content.add_widget(btn_layout)

        popup.content = content
        popup.open()

    def add_category(self, name):
        if not name:
            return
        db = App.get_running_app().db
        if db.add_category(name):
            self.load_categories()

    def show_add_item_popup(self):
        if not self.current_category:
            return

        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))

        name_input = TextInput(hint_text='Item Name', size_hint_y=None, height=dp(50))
        price_input = TextInput(hint_text='Price', input_filter='float', size_hint_y=None, height=dp(50))

        content.add_widget(Label(text='Add New Item to Category', size_hint_y=None, height=dp(30)))
        content.add_widget(name_input)
        content.add_widget(price_input)

        popup = Popup(title='Add New Menu Item', size_hint=(0.7, 0.5))

        def on_add_pressed(_):
            self.add_item(name_input.text.strip(), price_input.text.strip())
            popup.dismiss()

        btn_layout = BoxLayout(size_hint_y=None, height=dp(50))
        btn_layout.add_widget(Button(text='Cancel', on_press=popup.dismiss))
        btn_layout.add_widget(Button(text='Add', on_press=on_add_pressed))
        content.add_widget(btn_layout)

        popup.content = content
        popup.open()

    def add_item(self, name, price):
        if not name:
            print("Name is required.")
            return

        try:
            price = float(price)
        except ValueError:
            print("Invalid price.")
            return

        db = App.get_running_app().db
        if not self.current_category:
            print("No category selected.")
            return

        success = db.add_menu_item( price, self.current_category, name)
        if success:
            print("Menu item added.")
            category = {'id': self.current_category, 'name': self.ids.current_category_label.text}
            self.show_category_items(category)
        else:
            print("Failed to add menu item.")

    def delete_item(self, item_id):
        db = App.get_running_app().db
        if db.delete_menu_item(item_id):
            category = {'id': self.current_category, 'name': self.ids.current_category_label.text}
            self.show_category_items(category)

    def delete_current_category(self):
        if not self.current_category:
            return

        db = App.get_running_app().db
        # Call the delete_category method, which will handle both category and its items
        db.delete_category(self.current_category)

        # Reset current category and UI elements
        self.current_category = None
        self.ids.current_category_label.text = ''
        self.ids.items_container.clear_widgets()

        # Reload categories after deletion
        self.load_categories()

        # Refresh the order screen if needed
        order_screen = self.manager.get_screen('order_screen')
        order_screen.refresh_categories()
