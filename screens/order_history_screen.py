from kivy.uix.screenmanager import Screen
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.metrics import dp, sp
from kivy.app import App
from kivy.logger import Logger
from datetime import datetime, timedelta
import csv
import os

class OrderHistoryScreen(Screen):

    def on_pre_enter(self):
        self.load_order_history()

    def load_order_history(self, filter_period='Show All'):
        container = self.ids.order_history_container
        container.clear_widgets()
        db = App.get_running_app().db

        try:
            orders = db.get_all_orders()

            # Filter by period if needed
            if filter_period != 'Show All':
                if filter_period == 'Today':
                    orders = [o for o in orders if self._is_today(o['created_at'])]
                elif filter_period == 'Last 7 Days':
                    orders = [o for o in orders if self._is_within_days(o['created_at'], 7)]
                elif filter_period == 'This Month':
                    orders = [o for o in orders if self._is_this_month(o['created_at'])]

            if not orders:
                no_data_label = Label(
                    text="No order history found.",
                    font_size=sp(20),
                    halign='center',
                    valign='middle',
                    size_hint_y=None,
                    height=dp(100),
                    color=(0.5, 0.1, 0.1, 1)
                )
                no_data_label.bind(size=no_data_label.setter('text_size'))
                container.add_widget(no_data_label)

            for order in orders:
                order_id = order['id']
                timestamp = str(order.get('created_at', 'Unknown'))
                user = order.get('user_name', 'Unknown')
                order_items = db.get_items_by_order_id(order_id)

                total = sum(item['price'] * item['quantity'] for item in order_items)

                order_box = BoxLayout(orientation='vertical', size_hint_y=None, padding=dp(5), spacing=dp(5))
                order_box.bind(minimum_height=order_box.setter('height'))

                order_box.add_widget(Label(
                    text=f"[b]Order #{order_id}[/b] | {timestamp} | {user}",
                    markup=True,
                    size_hint_y=None,
                    height=dp(30),
                    color=(0, 0, 0, 1),
                    font_size=sp(16)
                ))

                for item in order_items:
                    order_box.add_widget(Label(
                        text=f"{item['name']} x{item['quantity']} - ${item['price']:.2f}",
                        size_hint_y=None,
                        height=dp(25),
                        color=(0.2, 0.2, 0.2, 1),
                        font_size=sp(14)
                    ))

                order_box.add_widget(Label(
                    text=f"[i]Total: ${total:.2f}[/i]",
                    markup=True,
                    size_hint_y=None,
                    height=dp(25),
                    color=(0.1, 0.4, 0.1, 1),
                    font_size=sp(14)
                ))

                order_box.add_widget(Label(
                    text="-" * 50,
                    size_hint_y=None,
                    height=dp(10),
                    color=(0.5, 0.5, 0.5, 1),
                    font_size=sp(12)
                ))

                container.add_widget(order_box)

        except Exception as e:
            container.add_widget(Label(text=f"Error loading order history: {str(e)}", font_size=sp(16)))
            Logger.error(f"Error loading order history: {e}")

    def export_order_history_to_csv(self):
        db = App.get_running_app().db
        try:
            orders = db.get_all_orders()
            if not orders:
                return

            folder_path = 'data/excel_receipts'
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)

            filename = os.path.join(folder_path, 'order_history.csv')

            print("Exported CSV path:", filename)

            with open(filename, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(['Order ID', 'Timestamp', 'User', 'Item Name', 'Quantity', 'Price'])

                for order in orders:
                    items = db.get_items_by_order_id(order['id'])
                    for item in items:
                        writer.writerow([
                            order['id'],
                            order['created_at'],
                            order.get('user_name', 'Unknown'),
                            item['name'],
                            item['quantity'],
                            item['price']
                        ])
            print(f"Exported to {filename}")

        except Exception as e:
            Logger.error(f"CSV Export Failed: {e}")

    def confirm_clear_order_history(self):
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        content.add_widget(Label(text="Are you sure you want to clear ALL order history?", font_size=sp(16)))

        btns = BoxLayout(spacing=10, size_hint_y=None, height=dp(40))
        yes_btn = Button(text="Yes", font_size=sp(16))
        cancel_btn = Button(text="Cancel", font_size=sp(16))
        btns.add_widget(yes_btn)
        btns.add_widget(cancel_btn)
        content.add_widget(btns)

        popup = Popup(title="Confirm", content=content, size_hint=(0.75, 0.4))
        yes_btn.bind(on_press=lambda *args: self._clear_orders_and_refresh(popup))
        cancel_btn.bind(on_press=popup.dismiss)
        popup.open()

    def _clear_orders_and_refresh(self, popup):
        try:
            App.get_running_app().db.clear_all_orders()
            popup.dismiss()
            self.load_order_history()
        except Exception as e:
            Logger.error(f"Clear history failed: {e}")

    def filter_order_history(self, value):
        self.load_order_history(filter_period=value)

    def _is_today(self, ts):
        try:
            date = datetime.fromisoformat(str(ts))
            return date.date() == datetime.today().date()
        except:
            return False

    def _is_within_days(self, ts, days):
        try:
            date = datetime.fromisoformat(str(ts))
            return datetime.today() - date <= timedelta(days=days)
        except:
            return False

    def _is_this_month(self, ts):
        try:
            date = datetime.fromisoformat(str(ts))
            now = datetime.today()
            return date.month == now.month and date.year == now.year
        except:
            return False
