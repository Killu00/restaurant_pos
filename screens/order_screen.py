from kivy.uix.screenmanager import Screen
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.metrics import dp, sp  # ✅ Added sp
from kivy.app import App
from kivy.properties import DictProperty, NumericProperty, StringProperty
from datetime import datetime


class OrderItemBox(BoxLayout):
    def __init__(self, item, quantity, on_remove, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = dp(50)
        self.spacing = dp(10)
        self.padding = [dp(5), 0]

        self.add_widget(Label(text=item['name'], size_hint_x=0.4, font_size=sp(16)))
        self.add_widget(Label(text=f"x{quantity}", size_hint_x=0.2, font_size=sp(16)))
        self.add_widget(Label(text=f"${item['price'] * quantity:.2f}", size_hint_x=0.3, font_size=sp(16)))

        remove_btn = Button(
            text='Remove',
            size_hint_x=0.1,
            size_hint_y=0.8,
            font_size=sp(14),
            on_press=lambda x: on_remove(item['id'])
        )
        self.add_widget(remove_btn)


class OrderScreen(Screen):
    current_category = NumericProperty(None)
    order = DictProperty({})
    current_category_name = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_order = []
        self.bind(on_pre_enter=self._load_data)

    def _load_data(self, *args):
        self.current_order = []
        self.refresh_categories()
        self.update_order_summary()

    def load_categories(self):
        categories_container = self.ids.categories_container
        categories_container.clear_widgets()

        try:
            categories = App.get_running_app().db.get_categories()
            if not categories:
                self.ids.current_category_label.text = ""
                return

            for cat in categories:
                btn = self.create_category_button(cat)
                categories_container.add_widget(btn)

            self.show_category_items(categories[0])
        except Exception as e:
            print(f"Error loading categories: {e}")
            self.ids.current_category_label.text = "Error loading categories"

    def create_category_button(self, category):
        return Button(
            text=category['name'],
            size_hint_y=None,
            height=dp(50),
            font_size=sp(16),
            background_color=(0.2, 0.6, 0.8, 1),
            on_press=lambda x, c=category: self.show_category_items(c)
        )

    def show_category_items(self, category):
        self.current_category = category['id']
        self.current_category_name = category['name']
        items_container = self.ids.items_container
        items_container.clear_widgets()

        try:
            items = App.get_running_app().db.get_menu_items_by_category(category['id'])
            if not items:
                items_container.add_widget(Label(text="No items in this category", font_size=sp(16)))
                return

            for item in items:
                items_container.add_widget(self.create_item_button(item))

        except Exception as e:
            print(f"Error loading items: {e}")
            items_container.add_widget(Label(text="Error loading items", font_size=sp(16)))

    def create_item_button(self, item):
        db = App.get_running_app().db
        inventory = db.get_inventory_by_menu_item_id(item['id'])
        out_of_stock = inventory is None or inventory.get('quantity', 0) <= 0

        return Button(
            text=f"{item['name']} - Out of Stock" if out_of_stock else f"{item['name']} - ${item['price']:.2f}",
            size_hint_y=None,
            height=dp(50),
            font_size=sp(16),
            background_color=(0.7, 0.7, 0.7, 1) if out_of_stock else (0.3, 0.6, 1, 1),
            disabled=out_of_stock,
            on_press=lambda x, i=item: self.add_to_order(i['name'], i['price'])
        )

    def add_to_order(self, item_name, item_price):
        db = App.get_running_app().db
        menu_item = db.get_menu_item_by_name(item_name)
        if not menu_item:
            raise ValueError(f"Menu item '{item_name}' not found")

        for entry in self.current_order:
            if entry['item']['id'] == menu_item['id']:
                entry['quantity'] += 1
                self.update_order_summary()
                return

        self.current_order.append({'item': menu_item, 'quantity': 1})
        self.update_order_summary()

    def update_order_summary(self):
        summary_box = self.ids.order_summary
        total_label = self.ids.total_label

        summary_box.clear_widgets()
        total = 0.0

        for entry in self.current_order:
            item = entry['item']
            quantity = entry['quantity']
            item_total = item['price'] * quantity

            order_item_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40), spacing=dp(10))

            order_item_box.add_widget(Label(text=str(item['name']), size_hint_x=0.3, color=(0, 0, 0, 1), font_size=sp(15)))
            order_item_box.add_widget(Label(text=f"x{quantity}", size_hint_x=0.2, color=(0, 0, 0, 1), font_size=sp(15)))
            order_item_box.add_widget(Label(text=f"${item_total:.2f}", size_hint_x=0.2, color=(0, 0, 0, 1), font_size=sp(15)))

            dec_btn = Button(text="-", size_hint_x=0.1, font_size=sp(14),
                             on_press=lambda x, item_id=item['id']: self.decrease_quantity(item_id))
            del_btn = Button(text="Delete", size_hint_x=0.2, font_size=sp(14),
                             on_press=lambda x, item_id=item['id']: self.remove_item_from_order(item_id))

            order_item_box.add_widget(dec_btn)
            order_item_box.add_widget(del_btn)

            summary_box.add_widget(order_item_box)
            total += item_total

        total_label.text = f"Total: ${round(total, 2):.2f}"

    def submit_order(self):
        if not self.current_order:
            self.show_message("Error", "Cannot submit empty order!")
            return

        try:
            app = App.get_running_app()
            db = app.db

            if not hasattr(app, 'current_user') or not app.current_user:
                raise ValueError("Please login to submit orders")

            for item in self.current_order:
                menu_item_id = item['item']['id']
                requested_qty = item['quantity']
                inventory = db.get_inventory_by_menu_item_id(menu_item_id)

                if not inventory:
                    self.show_message("Error", f"No inventory record for {item['item']['name']}")
                    return

                available_qty = inventory.get('quantity', 0)
                if available_qty < requested_qty:
                    self.show_message("Out of Stock",
                        f"Not enough stock for '{item['item']['name']}'. Available: {available_qty}, Requested: {requested_qty}")
                    return

            user_id = app.current_user['id']
            order_id = db.create_order(user_id)

            if not order_id:
                self.show_message("Error", "Order creation failed (no ID returned)")
                return

            for item in self.current_order:
                menu_item = item['item']
                quantity = item['quantity']
                db.add_item_to_order(order_id=order_id, menu_item_id=menu_item['id'], quantity=quantity)
                db.reduce_inventory_by_menu_item_id(menu_item['id'], quantity)

            self.print_receipt(order_id)
            self.current_order = []
            self.update_order_summary()
            self.show_message("Success", f"Order #{order_id} submitted!")

        except Exception as e:
            self.show_message("Error", f"Failed to submit order: {str(e)}")

        self.refresh_categories()

    def print_receipt(self, order_id):
        print(f"Printing receipt for order #{order_id}")
        receipt_lines = [
            f"Order #{order_id}",
            f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "----------------------------"
        ]

        for item in self.current_order:
            receipt_lines.append(
                f"{item['item']['name']} x{item['quantity']} @ ${item['item']['price']:.2f}"
            )

        receipt_lines.extend([
            "----------------------------",
            f"TOTAL: ${self.calculate_order_total():.2f}",
            "Thank you!"
        ])

        print("\n".join(receipt_lines))

    def calculate_order_total(self):
        return sum(item['item']['price'] * item['quantity'] for item in self.current_order)

    def show_message(self, title, message):
        from kivy.uix.popup import Popup
        Popup(
            title=title,
            content=Label(text=message, font_size=sp(16)),
            size_hint=(0.6, 0.3)
        ).open()

    def remove_item_from_order(self, item_id):
        self.current_order = [entry for entry in self.current_order if entry['item']['id'] != item_id]
        self.update_order_summary()

    def decrease_quantity(self, item_id):
        for entry in self.current_order:
            if entry['item']['id'] == item_id:
                entry['quantity'] -= 1
                if entry['quantity'] <= 0:
                    self.remove_item_from_order(item_id)
                break
        self.update_order_summary()

    def refresh_categories(self):
        self.load_categories()
