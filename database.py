import sqlite3
import os
from kivy.logger import Logger
import bcrypt
from datetime import datetime

class Database:
    def __init__(self, db_name='data/restaurant.db'):
        if not os.path.exists('data'):
            os.makedirs('data')
        self.db_name = db_name
        self.conn = self._connect()
        self.cursor = self.conn.cursor()
        self.create_tables()

    def _connect(self):
        try:
            conn = sqlite3.connect(self.db_name)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")  # ✅ Now conn is defined
            return conn
        except sqlite3.Error as e:
            Logger.error(f"Database connection error: {e}")
            raise

    def initialize(self):
        print("Initializing database...")
        self.create_tables()
        
    def create_user(self, username, password_hash, role):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (username, password_hash, role)
        )
        self.conn.commit()

    def create_tables(self):
        try:
            self.cursor.executescript('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'user' CHECK(role IN ('user', 'admin', 'super_admin'))
                );

                CREATE TABLE IF NOT EXISTS inventory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE,
                    quantity INTEGER,
                    menu_item_id INTEGER UNIQUE,
                    FOREIGN KEY (menu_item_id) REFERENCES menu_items(id)
                );

                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS menu_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    price REAL NOT NULL,
                    category_id INTEGER,
                    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE

                );

                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    status TEXT DEFAULT 'open',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                );
                CREATE TABLE IF NOT EXISTS order_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER,
                    menu_item_id INTEGER,
                    quantity INTEGER DEFAULT 1,
                    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
                    FOREIGN KEY (menu_item_id) REFERENCES menu_items(id) ON DELETE CASCADE
                );

            ''')
            self._create_default_admin_user()
            self._create_indexes()
            self.conn.commit()
        except sqlite3.Error as e:
            Logger.error(f"Error creating tables: {e}")
            raise

    def _create_default_admin_user(self):
        try:
            hashed_password = bcrypt.hashpw('password'.encode('utf-8'), bcrypt.gensalt())
            self.cursor.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)",
                                ('admin', hashed_password, 'admin'))
            self.conn.commit()
        except sqlite3.Error as e:
            Logger.error(f"Error inserting admin user: {e}")

    def _create_indexes(self):
        try:
            self.cursor.executescript('''
                CREATE INDEX IF NOT EXISTS idx_menu_items_category_id ON menu_items(category_id);
                CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
                CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);
            ''')
            self.conn.commit()
        except sqlite3.Error as e:
            Logger.error(f"Error creating indexes: {e}")

    # --- User Management ---

    def authenticate_user(self, username, password):
        try:
            self.cursor.execute("SELECT id, username, password, role FROM users WHERE username = ?", (username,))
            user = self.cursor.fetchone()
            if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
                return {'id': user['id'], 'username': user['username'], 'role': user['role']}
            return None
        except sqlite3.Error as e:
            Logger.error(f"Error authenticating user: {e}")
            return None

    def username_exists(self, username):
        try:
            self.cursor.execute("SELECT 1 FROM users WHERE username = ?", (username,))
            return self.cursor.fetchone() is not None
        except sqlite3.Error as e:
            Logger.error(f"Error checking username existence: {e}")
            return False

    def get_user_by_username(self, username):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        return user

    def register_user(self, username, password, role="user"):
        try:
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            self.cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                                (username, hashed_password, role))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            Logger.warning(f"Username {username} already exists.")
            return False
        except sqlite3.Error as e:
            Logger.error(f"Error registering user: {e}")
            return False

    def get_user(self, username):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, username, password, role FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        if row:
            return {
                'id': row[0],
                'username': row[1],
                'password': row[2],
                'role': row[3]
            }
        return None

    def get_all_users(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, username, role FROM users")
        rows = cursor.fetchall()
        return [{'id': row[0], 'username': row[1], 'role': row[2]} for row in rows]

    def delete_user(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        self.conn.commit()

    # --- Category and Menu Management ---

    def get_categories(self):
        try:
            self.cursor.execute("SELECT id, name FROM categories ORDER BY name")
            return [dict(row) for row in self.cursor.fetchall()]
        except sqlite3.Error as e:
            Logger.error(f"Error fetching categories: {e}")
            return []

    def add_category(self, name):
        try:
            self.cursor.execute("INSERT INTO categories (name) VALUES (?)", (name,))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            Logger.error(f"Error adding category {name}: {e}")
            return False

    def add_menu_item(self, price, category_id, custom_name=None, inventory_name=None):
        try:
            if not custom_name and not inventory_name:
                raise ValueError("Item must have a name or be linked to inventory.")

            # Use the inventory name as the menu item name if no custom name
            name = custom_name or inventory_name

            # Insert into menu_items
            self.cursor.execute("""
                INSERT INTO menu_items (name, price, category_id)
                VALUES (?, ?, ?)
            """, (name, price, category_id))

            menu_item_id = self.cursor.lastrowid

            # If linking to inventory, update the inventory row
            if inventory_name:
                self.cursor.execute("""
                    UPDATE inventory SET menu_item_id = ?
                    WHERE name = ?
                """, (menu_item_id, inventory_name))

            self.conn.commit()
            return True
        except Exception as e:
            Logger.error(f"Add menu item error: {e}")
            return False

    def get_menu_items(self):
        try:
            self.cursor.execute('''
                SELECT menu_items.id, menu_items.name, menu_items.price, categories.name AS category
                FROM menu_items
                LEFT JOIN categories ON menu_items.category_id = categories.id
                ORDER BY menu_items.name
            ''')
            return [dict(row) for row in self.cursor.fetchall()]
        except sqlite3.Error as e:
            Logger.error(f"Error fetching menu items: {e}")
            return []

    def get_menu_item_by_name(self, name):
        try:
            self.cursor.execute("SELECT id, name, price FROM menu_items WHERE name = ?", (name,))
            row = self.cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            Logger.error(f"Error fetching menu item: {e}")
            return None

    def get_menu_items_by_category(self, category_id):
        try:
            self.cursor.execute("""
                SELECT m.id AS menu_item_id,
                       m.name AS menu_item_name,
                       m.price,
                       i.id AS inventory_id,
                       i.name AS inventory_name
                FROM menu_items m
                LEFT JOIN inventory i ON i.menu_item_id = m.id
                WHERE m.category_id = ?
            """, (category_id,))

            return [
                {
                    'id': row[0],
                    'name': row[1],
                    'price': row[2],
                    'inventory_id': row[3],
                    'inventory_name': row[4]
                }
                for row in self.cursor.fetchall()
            ]
        except sqlite3.Error as e:
            Logger.error(f"Error fetching menu items for category {category_id}: {e}")
            return []

    def delete_menu_item(self, item_id):
        try:
            # Delete inventory tied to the menu item
            self.cursor.execute("DELETE FROM inventory WHERE menu_item_id = ?", (item_id,))
            # Then delete the menu item itself
            self.cursor.execute("DELETE FROM menu_items WHERE id = ?", (item_id,))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            Logger.error(f"Database: Failed to delete menu item: {e}")
            return False

    def delete_category(self, category_id):
        try:
            # First, delete menu items related to the category
            self.conn.execute("DELETE FROM menu_items WHERE category_id = ?", (category_id,))

            # Now, delete the category itself
            self.conn.execute("DELETE FROM categories WHERE id = ?", (category_id,))
            self.conn.commit()
            print(f"Category {category_id} and its items deleted successfully.")
            return True
        except sqlite3.Error as e:
            print(f"Error deleting category: {e}")
            return False

    def link_inventory_to_menu_item(self, inventory_id, menu_item_id):
        try:
            self.cursor.execute('''
                UPDATE inventory SET menu_item_id = ? WHERE id = ?
            ''', (menu_item_id, inventory_id))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            Logger.error(f"Error linking inventory to menu item: {e}")
            return False

    # --- Inventory Management ---

    def add_or_update_inventory_item(self, name, quantity):
        try:
            self.cursor.execute("SELECT id FROM menu_items WHERE name = ?", (name,))
            menu_item = self.cursor.fetchone()
            if not menu_item:
                Logger.warning(f"No matching menu item found for inventory name: {name}")
                return

            menu_item_id = menu_item['id']
            self.cursor.execute('''
                INSERT INTO inventory (name, quantity, menu_item_id)
                VALUES (?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET quantity = quantity + excluded.quantity
            ''', (name, quantity, menu_item_id))
            self.conn.commit()
        except sqlite3.Error as e:
            Logger.error(f"Error updating inventory: {e}")

    def get_inventory_items(self):
        try:
            self.cursor.execute('SELECT name, quantity FROM inventory')
            return [dict(row) for row in self.cursor.fetchall()]
        except sqlite3.Error as e:
            Logger.error(f"Error fetching inventory items: {e}")
            return []

    def reduce_inventory_by_id(self, item_id, quantity):
        try:
            self.cursor.execute('''
                UPDATE inventory
                SET quantity = quantity - ?
                WHERE id = ? AND quantity >= ?
            ''', (quantity, item_id, quantity))
            if self.cursor.rowcount == 0:
                Logger.warning(f"Not enough inventory for item ID {item_id}")
                return False
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            Logger.error(f"Error reducing inventory by ID: {e}")
            return False

    def get_available_menu_items(self):
        try:
            self.cursor.execute('''
                SELECT menu_items.name, menu_items.price, inventory.quantity
                FROM menu_items
                JOIN inventory ON menu_items.name = inventory.name
            ''')
            return [dict(row) for row in self.cursor.fetchall()]
        except sqlite3.Error as e:
            Logger.error(f"Error fetching available menu items: {e}")
            return []

    def get_inventory_by_menu_item_id(self, menu_item_id):
        try:
            self.cursor.execute('''
                SELECT inventory.id, inventory.name, inventory.quantity
                FROM inventory
                JOIN menu_items ON inventory.name = menu_items.name
                WHERE menu_items.id = ?
            ''', (menu_item_id,))
            row = self.cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            Logger.error(f"Error fetching inventory by menu item ID: {e}")
            return None

    def reduce_inventory_by_menu_item_id(self, menu_item_id, quantity):
        try:
            # Try reducing by menu_item_id first
            self.cursor.execute('''
                UPDATE inventory
                SET quantity = quantity - ?
                WHERE menu_item_id = ? AND quantity >= ?
            ''', (quantity, menu_item_id, quantity))

            if self.cursor.rowcount == 0:
                # Fallback: Try matching by name if menu_item_id is not set
                self.cursor.execute('SELECT name FROM menu_items WHERE id = ?', (menu_item_id,))
                row = self.cursor.fetchone()
                if row:
                    name = row['name']
                    self.cursor.execute('''
                        UPDATE inventory
                        SET quantity = quantity - ?
                        WHERE name = ? AND quantity >= ?
                    ''', (quantity, name, quantity))

            if self.cursor.rowcount == 0:
                Logger.warning(f"Not enough inventory for menu_item_id {menu_item_id}")
                return False

            self.conn.commit()
            return True
        except sqlite3.Error as e:
            Logger.error(f"Error reducing inventory: {e}")
            return False

    def delete_inventory_item(self, name):
        try:
            self.cursor.execute("DELETE FROM inventory WHERE name = ?", (name,))
            self.conn.commit()
        except sqlite3.Error as e:
            Logger.error(f"Error deleting inventory item: {e}")

    def set_inventory_quantity(self, name, new_quantity):
        try:
            self.cursor.execute('UPDATE inventory SET quantity = ? WHERE name = ?', (new_quantity, name))
            self.conn.commit()
        except sqlite3.Error as e:
            Logger.error(f"Error setting inventory quantity: {e}")

    # --- Orders Management ---

    def create_order(self, user_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO orders (user_id) VALUES (?)", (user_id,))
            self.conn.commit()
            order_id = cursor.lastrowid
            print(f"[DEBUG] Created order_id: {order_id}")
            return order_id
        except sqlite3.Error as e:
            print(f"[ERROR] Failed to create order: {e}")
            return None

    def add_item_to_order(self, order_id, menu_item_id, quantity=1):
        try:
            self.cursor.execute('''
                INSERT INTO order_items (order_id, menu_item_id, quantity)
                VALUES (?, ?, ?)
            ''', (order_id, menu_item_id, quantity))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            Logger.error(f"Error adding item to order: {e}")
            return False

    def add_order_item(self, order_id, item_name, quantity):
        try:
            self.cursor.execute("SELECT id FROM menu_items WHERE name = ?", (item_name,))
            row = self.cursor.fetchone()
            if row:
                return self.add_item_to_order(order_id, row['id'], quantity)
            return False
        except sqlite3.Error as e:
            Logger.error(f"Error adding order item: {e}")
            return False

    def get_active_orders(self):
        try:
            self.cursor.execute('''
                SELECT o.id, u.username, o.created_at, o.status
                FROM orders o
                JOIN users u ON o.user_id = u.id
                WHERE o.status != 'closed'
                ORDER BY o.created_at DESC
            ''')
            return [{
                'id': row['id'],
                'username': row['username'],
                'time': datetime.strptime(row['created_at'], '%Y-%m-%d %H:%M:%S').strftime('%b %d, %I:%M %p'),
                'status': row['status']
            } for row in self.cursor.fetchall()]
        except sqlite3.Error as e:
            Logger.error(f"Error fetching active orders: {e}")
            return []

    # --- Order History ---

    def get_all_orders(self):
        try:
            self.cursor.execute("""
                SELECT o.id, o.created_at, u.username AS user_name
                FROM orders o
                JOIN users u ON o.user_id = u.id
                ORDER BY o.created_at DESC
            """)
            orders = [dict(row) for row in self.cursor.fetchall()]
            Logger.info(f"Fetched orders: {orders}")  # Log the fetched orders for debugging
            return orders
        except sqlite3.Error as e:
            Logger.error(f"Error fetching all orders: {e}")
            return []

    def get_items_by_order_id(self, order_id):
        try:
            self.cursor.execute("""
                SELECT m.name, oi.quantity, m.price
                FROM order_items oi
                JOIN menu_items m ON oi.menu_item_id = m.id
                WHERE oi.order_id = ?
            """, (order_id,))
            return [dict(row) for row in self.cursor.fetchall()]
        except sqlite3.Error as e:
            Logger.error(f"Error fetching items for order {order_id}: {e}")
            return []

    def clear_all_orders(self):
        cursor = self.conn.cursor()

        # Delete all records from order_items and orders tables
        cursor.execute("DELETE FROM order_items")
        cursor.execute("DELETE FROM orders")

        self.conn.commit()

    # --- Clean-up ---

    def close(self):
        import traceback
        try:
            print("🔴 DB connection closed! Called from:")
            traceback.print_stack()
            self.conn.close()
        except sqlite3.Error as e:
            print(f"❌ Error closing database connection: {e}")

