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

ADMIN_HTML = """<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
<title>لوحة التحكم - 𝓙𝓸𝓴𝓮𝓻丨𝓜4</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:system-ui,'Segoe UI',sans-serif}
body{background:linear-gradient(145deg,#0a0a12 0%,#1a1a2e 100%);min-height:100vh;color:#fff;padding:20px}
.container{max-width:800px;margin:auto}
.header{text-align:center;padding:30px 20px;background:rgba(255,255,255,0.05);border-radius:20px;margin-bottom:25px;border:1px solid rgba(255,255,255,0.08)}
.header h1{font-size:28px;background:linear-gradient(135deg,#f7c948,#ff8a00);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.header p{color:#8899aa;margin-top:8px;font-size:14px}
.card{background:rgba(255,255,255,0.05);border-radius:16px;padding:20px;margin-bottom:20px;border:1px solid rgba(255,255,255,0.06)}
.card h3{color:#f7c948;margin-bottom:15px;font-size:18px}
.grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:20px}
.stat{background:rgba(255,255,255,0.05);padding:15px;border-radius:12px;text-align:center}
.stat .num{font-size:28px;font-weight:bold;color:#f7c948}
.stat .label{font-size:12px;color:#8899aa;margin-top:5px}
.login-box{background:rgba(255,255,255,0.05);border-radius:16px;padding:30px;text-align:center;border:1px solid rgba(255,255,255,0.06);max-width:350px;margin:50px auto}
.login-box h2{color:#f7c948;margin-bottom:20px}
input{width:100%;padding:14px 16px;border-radius:10px;border:1px solid rgba(255,255,255,0.12);background:rgba(255,255,255,0.08);color:#fff;font-size:15px;margin-bottom:12px;outline:none;transition:0.3s}
input:focus{border-color:#f7c948}
.btn{width:100%;padding:14px;border-radius:10px;border:none;background:linear-gradient(135deg,#f7c948,#ff8a00);color:#000;font-size:16px;font-weight:bold;cursor:pointer;transition:0.3s}
.btn:hover{transform:scale(1.02);opacity:0.9}
.btn-danger{background:linear-gradient(135deg,#ff4444,#cc0000);color:#fff;padding:8px 16px;border:none;border-radius:8px;cursor:pointer;font-size:13px}
.product-item{display:flex;justify-content:space-between;align-items:center;padding:12px 0;border-bottom:1px solid rgba(255,255,255,0.06)}
.product-item:last-child{border-bottom:none}
.product-info{flex:1}
.product-info .name{font-size:15px;color:#eee}
.product-info .meta{font-size:12px;color:#8899aa;margin-top:4px}
.logout-btn{background:none;border:1px solid rgba(255,255,255,0.15);color:#8899aa;padding:8px 20px;border-radius:8px;cursor:pointer;margin-top:20px;font-size:13px}
.hidden{display:none}
.order-item{padding:12px 0;border-bottom:1px solid rgba(255,255,255,0.06);font-size:14px}
.order-item:last-child{border-bottom:none}
.order-item .small{font-size:12px;color:#8899aa}
</style>
</head>
<body>
<div class="container" id="app">
<div id="loginScreen">
<div class="login-box">
<h2>🔐 لوحة التحكم</h2>
<p style="color:#8899aa;margin-bottom:20px;font-size:13px">تطوير: 𝓙𝓸𝓴𝓮𝓻丨𝓜4 - @VT_YC</p>
<input type="password" id="passwordInput" placeholder="كلمة السر" onkeydown="if(event.key==='Enter') login()">
<button class="btn" onclick="login()">دخول</button>
<div id="loginError" style="color:#ff4444;margin-top:12px;font-size:13px;display:none"></div>
</div>
</div>
<div id="adminPanel" class="hidden">
<div class="header">
<h1>🏪 لوحة التحكم</h1>
<p>𝓙𝓸𝓴𝓮𝓻丨𝓜4 • @VT_YC • كلمة السر: VT_YC</p>
</div>
<div class="grid" id="statsGrid">
<div class="stat"><div class="num" id="userCount">0</div><div class="label">المشتركين</div></div>
<div class="stat"><div class="num" id="orderCount">0</div><div class="label">المبيعات</div></div>
<div class="stat"><div class="num" id="totalStars">0</div><div class="label">إجمالي النجوم</div></div>
</div>
<div class="card">
<h3>📋 المنتجات</h3>
<div id="productsList"><p style="color:#8899aa">جاري التحميل...</p></div>
</div>
<div class="card">
<h3>📦 الطلبات الحديثة</h3>
<div id="ordersList"><p style="color:#8899aa">جاري التحميل...</p></div>
</div>
<div style="text-align:center">
<button class="logout-btn" onclick="logout()">🚪 تسجيل خروج</button>
</div>
</div>
</div>
<script>
let token = '';
async function login(){const p=document.getElementById('passwordInput').value;const e=document.getElementById('loginError');e.style.display='none'
try{const r=await fetch('/api/verify',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({password:p})});const d=await r.json()
if(d.admin){token=p;document.getElementById('loginScreen').classList.add('hidden');document.getElementById('adminPanel').classList.remove('hidden');loadData()}
else{e.textContent='❌ كلمة السر خطأ';e.style.display='block'}}
catch(x){e.textContent='❌ خطأ في الاتصال بالخادم';e.style.display='block'}}
async function loadData(){const h={'Authorization':token}
try{const s=await(await fetch('/api/stats',{headers:h})).json();if(s.status==='ok'){document.getElementById('userCount').textContent=s.users;document.getElementById('orderCount').textContent=s.sales_count;document.getElementById('totalStars').textContent=s.sales_total}}
catch(e){}
try{const p=await(await fetch('/api/products')).json();if(p.status==='ok'){let h='';if(p.products.length===0)h='<p style="color:#8899aa">لا توجد منتجات</p>'
else p.products.forEach(pr=>{h+='<div class="product-item"><div class="product-info"><div class="name">'+pr.name+'</div><div class="meta">🆔 '+pr.id+' • ⭐ '+pr.price+'</div></div></div>'});document.getElementById('productsList').innerHTML=h}}
catch(e){}
try{const o=await(await fetch('/api/orders',{headers:h})).json();if(o.status==='ok'){let h='';if(o.orders.length===0)h='<p style="color:#8899aa">لا توجد طلبات</p>'
else o.orders.slice(0,10).forEach(or=>{h+='<div class="order-item">📦 <b>'+or.product_name+'</b><br><span class="small">👤 ID: '+or.user_id+' • ⭐ '+or.price+' • '+or.created_at+'</span></div>'});document.getElementById('ordersList').innerHTML=h}}
catch(e){}}
function logout(){token='';document.getElementById('loginScreen').classList.remove('hidden');document.getElementById('adminPanel').classList.add('hidden');document.getElementById('passwordInput').value=''}
</script>
</body>
</html>"""

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

        elif self.path == "/admin" or self.path == "/admin/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(ADMIN_HTML.encode())
            return

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
