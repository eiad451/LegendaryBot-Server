#!/usr/bin/env python3
import os, sys, json, logging, sqlite3, threading, time
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram.ext import Application

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "bot.db")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "5548005854"))
ADMIN_PASS = "VT_YC"

DEV_NAME = "\U0001d59b\U0001d4f8\U0001d4f4\U0001d4f2\U0001d4f9\U0001d4ea\U0001d4c4\U0001d4d4"
DEV_USER = "@VT_YC"

from bot import (
    init_db, get_all_products, get_user_count, get_total_sales,
    get_user_orders, add_order, save_product, delete_product, get_product,
    CATEGORIES, CATEGORY_PRODUCTS
)

class APIHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())

    def get_post_data(self):
        length = int(self.headers.get("Content-Length", 0))
        if length:
            return json.loads(self.rfile.read(length))
        return {}

    def check_auth(self):
        auth = self.headers.get("Authorization", "")
        return auth == ADMIN_PASS or auth == f"Bearer {ADMIN_PASS}"

    def do_GET(self):
        if self.path == "/api/stats":
            if not self.check_auth():
                return self.send_json({"error": "unauthorized"}, 401)
            users = get_user_count()
            sales = get_total_sales()
            self.send_json({
                "status": "ok",
                "users": users,
                "sales_count": sales["count"],
                "sales_total": sales["total"],
                "developer": DEV_NAME,
                "username": DEV_USER
            })

        elif self.path == "/api/products":
            products = get_all_products()
            self.send_json({"status": "ok", "products": products})

        elif self.path.startswith("/api/products/"):
            pid = self.path.replace("/api/products/", "")
            product = get_product(pid)
            if product:
                self.send_json({"status": "ok", "product": product})
            else:
                self.send_json({"error": "not found"}, 404)

        elif self.path == "/api/orders":
            if not self.check_auth():
                return self.send_json({"error": "unauthorized"}, 401)
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT o.*, p.name as product_name FROM orders o LEFT JOIN products p ON o.product_id = p.id ORDER BY o.created_at DESC")
            orders = [dict(r) for r in c.fetchall()]
            conn.close()
            self.send_json({"status": "ok", "orders": orders})

        elif self.path == "/api/":
            self.send_json({
                "status": "ok",
                "app": "LegendaryBot Server",
                "developer": DEV_NAME,
                "username": DEV_USER,
                "version": "2.0",
                "endpoints": [
                    "GET /api/ - this help",
                    "GET /api/stats - statistics (auth required)",
                    "GET /api/products - list all products",
                    "GET /api/products/{id} - get product",
                    "GET /api/orders - list orders (auth required)",
                    "POST /api/products/add - add product (auth required)",
                    "POST /api/products/delete - delete product (auth required)",
                    "POST /api/verify - verify admin password"
                ]
            })
        else:
            self.send_json({"error": "not found"}, 404)

    def do_POST(self):
        data = self.get_post_data()

        if self.path == "/api/verify":
            if data.get("password") == ADMIN_PASS:
                self.send_json({"status": "ok", "admin": True, "user": DEV_USER})
            else:
                self.send_json({"status": "error", "admin": False}, 401)

        elif self.path == "/api/products/add":
            if not self.check_auth():
                return self.send_json({"error": "unauthorized"}, 401)
            name = data.get("name", "")
            desc = data.get("description", "")
            price = int(data.get("price", 0))
            code = data.get("code", "")
            pid = f"p_{int(time.time())}"
            save_product(pid, "0", name, price, desc, code, None)
            self.send_json({"status": "ok", "product_id": pid})

        elif self.path == "/api/products/delete":
            if not self.check_auth():
                return self.send_json({"error": "unauthorized"}, 401)
            pid = data.get("id", "")
            delete_product(pid)
            self.send_json({"status": "ok"})

        else:
            self.send_json({"error": "not found"}, 404)

def run_api():
    port = int(os.getenv("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), APIHandler)
    logger.info(f"API Server running on port {port}")
    print(f"API Server: http://0.0.0.0:{port}")
    server.serve_forever()

if __name__ == "__main__":
    init_db()
    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()
    print(f"البوتサーバ ᴊᴏᴋᴇʀ丨ᴍ4 - @VT_YC")
    print(f"Admin Password: {ADMIN_PASS}")
    print("اضغط Ctrl+C للايقاف")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("تم الايقاف")
