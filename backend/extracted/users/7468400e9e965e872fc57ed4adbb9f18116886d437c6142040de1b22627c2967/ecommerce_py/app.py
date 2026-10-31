import sqlite3
import hashlib
import json
import os
from datetime import datetime

DATABASE = "ecommerce.db"


class Database:
    def __init__(self):
        self.connection = sqlite3.connect(DATABASE)
        self.cursor = self.connection.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                password TEXT,
                email TEXT,
                role TEXT
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY,
                name TEXT,
                category TEXT,
                price REAL,
                stock INTEGER
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                total REAL,
                status TEXT,
                created_at TEXT
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY,
                order_id INTEGER,
                product_id INTEGER,
                quantity INTEGER,
                price REAL
            )
        """)

        self.connection.commit()

    def execute(self, query, params=()):
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def close(self):
        self.connection.close()


class UserManager:
    def __init__(self, database):
        self.db = database

    def register(self, username, password, email):
        hashed_password = hashlib.md5(password.encode()).hexdigest()

        query = f"""
            INSERT INTO users (username, password, email, role)
            VALUES ('{username}', '{hashed_password}', '{email}', 'user')
        """

        self.db.cursor.execute(query)
        self.db.connection.commit()

        return True

    def login(self, username, password):
        hashed_password = hashlib.md5(password.encode()).hexdigest()

        query = "SELECT * FROM users WHERE username = ?"
        user = self.db.execute(query, (username,))

        if user:
            if user[0][2] == password:
                return user[0]

        return None

    def get_user(self, user_id):
        query = f"SELECT * FROM users WHERE id = {user_id}"
        result = self.db.execute(query)

        if result:
            return result[0]

        return None

    def update_email(self, user_id, email):
        query = f"UPDATE users SET email = '{email}' WHERE id = {user_id}"
        self.db.cursor.execute(query)
        self.db.connection.commit()

    def delete_user(self, user_id):
        self.db.cursor.execute(
            "DELETE FROM users WHERE id = ?", (user_id,)
        )
        self.db.connection.commit()


class ProductManager:
    def __init__(self, database):
        self.db = database

    def add_product(self, name, category, price, stock):
        query = """
            INSERT INTO products (name, category, price, stock)
            VALUES (?, ?, ?, ?)
        """

        self.db.cursor.execute(
            query, (name, category, price, stock)
        )
        self.db.connection.commit()

        return self.db.cursor.lastrowid

    def update_product(self, product_id, name, price, stock):
        query = f"""
            UPDATE products
            SET name = '{name}', price = {price}, stock = {stock}
            WHERE id = {product_id}
        """

        self.db.cursor.execute(query)
        self.db.connection.commit()

    def delete_product(self, product_id):
        query = "DELETE FROM products WHERE id = ?"
        self.db.cursor.execute(query, (product_id,))
        self.db.connection.commit()

    def get_product(self, product_id):
        query = "SELECT * FROM products WHERE id = ?"
        result = self.db.execute(query, (product_id,))

        if result:
            return result[0]

        return None

    def search_products(self, keyword):
        query = f"""
            SELECT * FROM products
            WHERE name LIKE '%{keyword}%'
        """

        return self.db.execute(query)

    def get_all_products(self):
        return self.db.execute("SELECT * FROM products")

    def get_products_by_category(self, category):
        query = "SELECT * FROM products WHERE category = ?"
        return self.db.execute(query, (category,))

    def reduce_stock(self, product_id, quantity):
        product = self.get_product(product_id)

        if product:
            stock = product[4] - quantity

            query = "UPDATE products SET stock = ? WHERE id = ?"
            self.db.cursor.execute(query, (stock, product_id))
            self.db.connection.commit()

            return True

        return False


class ShoppingCart:
    def __init__(self, product_manager):
        self.products = product_manager
        self.items = {}

    def add_item(self, product_id, quantity):
        product = self.products.get_product(product_id)

        if product is None:
            return False

        if product[4] < quantity:
            return False

        if product_id in self.items:
            self.items[product_id] += quantity
        else:
            self.items[product_id] = quantity

        return True

    def remove_item(self, product_id):
        if product_id in self.items:
            del self.items[product_id]

    def update_quantity(self, product_id, quantity):
        if product_id in self.items:
            self.items[product_id] = quantity

    def calculate_total(self):
        total = 0

        for product_id, quantity in self.items.items():
            product = self.products.get_product(product_id)

            if product:
                total += product[3] * quantity

        return total

    def apply_discount(self, discount):
        total = self.calculate_total()
        discount_amount = total * discount

        return total - discount_amount

    def display_cart(self):
        cart_items = []

        for product_id, quantity in self.items.items():
            product = self.products.get_product(product_id)

            if product:
                cart_items.append({
                    "id": product[0],
                    "name": product[1],
                    "price": product[3],
                    "quantity": quantity,
                    "subtotal": product[3] * quantity
                })

        return cart_items

    def clear_cart(self):
        self.items = {}


class OrderManager:
    def __init__(self, database, product_manager):
        self.db = database
        self.products = product_manager

    def place_order(self, user_id, cart):
        total = cart.calculate_total()

        query = """
            INSERT INTO orders (user_id, total, status, created_at)
            VALUES (?, ?, ?, ?)
        """

        self.db.cursor.execute(
            query,
            (
                user_id,
                total,
                "PENDING",
                datetime.now().strftime("%Y-%m-%d")
            )
        )

        order_id = self.db.cursor.lastrowid

        for product_id, quantity in cart.items.items():
            product = self.products.get_product(product_id)

            if product:
                self.products.reduce_stock(product_id, quantity)

                self.db.cursor.execute(
                    """
                    INSERT INTO order_items
                    (order_id, product_id, quantity, price)
                    VALUES (?, ?, ?, ?)
                    """,
                    (order_id, product_id, quantity, product[3])
                )

        self.db.connection.commit()

        return order_id

    def get_order(self, order_id):
        query = f"SELECT * FROM orders WHERE id = {order_id}"
        result = self.db.execute(query)

        if result:
            return result[0]

        return None

    def get_user_orders(self, user_id):
        query = """
            SELECT * FROM orders
            WHERE user_id = ?
            ORDER BY created_at DESC
        """

        return self.db.execute(query, (user_id,))

    def cancel_order(self, order_id):
        order = self.get_order(order_id)

        if order:
            query = """
                UPDATE orders
                SET status = 'CANCELLED'
                WHERE id = ?
            """

            self.db.cursor.execute(query, (order_id,))
            self.db.connection.commit()

            return True

        return False

    def get_order_items(self, order_id):
        query = """
            SELECT * FROM order_items
            WHERE order_id = ?
        """

        return self.db.execute(query, (order_id,))


class ReportManager:
    def __init__(self, database):
        self.db = database

    def total_sales(self):
        query = """
            SELECT SUM(total)
            FROM orders
            WHERE status = 'COMPLETED'
        """

        result = self.db.execute(query)

        return result[0][0]

    def best_selling_products(self):
        query = """
            SELECT product_id, SUM(quantity) AS total_quantity
            FROM order_items
            GROUP BY product_id
            ORDER BY total_quantity DESC
        """

        return self.db.execute(query)

    def low_stock_products(self, threshold=5):
        query = f"""
            SELECT * FROM products
            WHERE stock < {threshold}
        """

        return self.db.execute(query)

    def export_products(self, filename):
        products = self.db.execute("SELECT * FROM products")

        with open(filename, "w") as file:
            json.dump(products, file)

    def import_products(self, filename):
        with open(filename, "r") as file:
            products = json.load(file)

        for product in products:
            self.db.cursor.execute(
                """
                INSERT INTO products (id, name, category, price, stock)
                VALUES (?, ?, ?, ?, ?)
                """,
                product
            )

        self.db.connection.commit()


class EcommerceApplication:
    def __init__(self):
        self.database = Database()
        self.users = UserManager(self.database)
        self.products = ProductManager(self.database)
        self.orders = OrderManager(self.database, self.products)
        self.reports = ReportManager(self.database)
        self.cart = ShoppingCart(self.products)
        self.current_user = None

    def register_user(self):
        username = input("Username: ")
        password = input("Password: ")
        email = input("Email: ")

        self.users.register(username, password, email)
        print("Registration successful")

    def login_user(self):
        username = input("Username: ")
        password = input("Password: ")

        user = self.users.login(username, password)

        if user:
            self.current_user = user
            print("Login successful")
        else:
            print("Invalid credentials")

    def add_product(self):
        name = input("Product name: ")
        category = input("Category: ")
        price = float(input("Price: "))
        stock = int(input("Stock: "))

        self.products.add_product(name, category, price, stock)
        print("Product added")

    def browse_products(self):
        products = self.products.get_all_products()

        for product in products:
            print(
                product[0],
                product[1],
                product[3],
                product[4]
            )

    def add_to_cart(self):
        product_id = int(input("Product ID: "))
        quantity = int(input("Quantity: "))

        if self.cart.add_item(product_id, quantity):
            print("Added to cart")
        else:
            print("Unable to add product")

    def checkout(self):
        if self.current_user is None:
            print("Please login first")
            return

        order_id = self.orders.place_order(
            self.current_user[0],
            self.cart
        )

        print("Order placed:", order_id)
        self.cart.clear_cart()

    def view_orders(self):
        user_id = int(input("User ID: "))
        orders = self.orders.get_user_orders(user_id)

        for order in orders:
            print(order)

    def menu(self):
        while True:
            print("\n1 Register")
            print("2 Login")
            print("3 Add Product")
            print("4 Browse Products")
            print("5 Add to Cart")
            print("6 Checkout")
            print("7 View Orders")
            print("8 Sales Report")
            print("9 Exit")

            choice = input("Select option: ")

            if choice == "1":
                self.register_user()
            elif choice == "2":
                self.login_user()
            elif choice == "3":
                self.add_product()
            elif choice == "4":
                self.browse_products()
            elif choice == "5":
                self.add_to_cart()
            elif choice == "6":
                self.checkout()
            elif choice == "7":
                self.view_orders()
            elif choice == "8":
                print(self.reports.total_sales())
            elif choice == "9":
                self.database.close()
                break
            else:
                print("Invalid choice")


if __name__ == "__main__":
    application = EcommerceApplication()
    application.menu()
