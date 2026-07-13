#!/usr/bin/env python3
import http.server, json, sqlite3, os, sys, time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "bot.db")
ADMIN_PASS = "VT_YC"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS products (id TEXT PRIMARY KEY, category_id TEXT NOT NULL, name TEXT NOT NULL, price INTEGER NOT NULL, description TEXT, code TEXT NOT NULL, image TEXT);
        CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, product_id TEXT NOT NULL, price INTEGER NOT NULL, status TEXT DEFAULT 'paid', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT, joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS discounts (id INTEGER PRIMARY KEY AUTOINCREMENT, product_id TEXT, discount_percent INTEGER NOT NULL, expires_at TIMESTAMP NOT NULL, active INTEGER DEFAULT 1);
        CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT);
    """)
    conn.commit(); conn.close()

init_db()

HTML = """<!DOCTYPE html>
<html dir="rtl">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<title>JOKER Admin</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a12;color:#eee;font-family:system-ui,sans-serif;padding:15px;direction:rtl}
.container{max-width:800px;margin:auto}
h1{background:linear-gradient(135deg,#f7c948,#ff8a00);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-size:24px}
.sub{color:#667;font-size:13px;margin:5px 0 20px}
.card{background:rgba(255,255,255,0.04);border-radius:14px;padding:18px;margin-bottom:18px;border:1px solid rgba(255,255,255,0.06)}
.card h3{color:#f7c948;font-size:16px;margin-bottom:12px}
input,textarea,select{width:100%;padding:12px;border-radius:8px;border:1px solid #333;background:#151528;color:#eee;font-size:14px;margin-bottom:10px;outline:none;font-family:inherit;box-sizing:border-box}
textarea{resize:vertical;min-height:60px}
input:focus,textarea:focus{border-color:#f7c948}
label{display:block;font-size:13px;color:#889;margin-bottom:4px}
.btn{padding:12px 24px;border-radius:8px;border:none;background:linear-gradient(135deg,#f7c948,#ff8a00);color:#000;font-weight:700;font-size:14px;cursor:pointer;transition:0.2s;display:inline-block;margin:3px}
.btn:hover{opacity:.85;transform:scale(1.02)}
.btn-sm{padding:6px 14px;font-size:12px}
.btn-green{background:#2ecc71;color:#fff}
.btn-red{background:#e74c3c;color:#fff}
.btn-blue{background:#3498db;color:#fff}
.btn-outline{background:transparent;border:1px solid #444;color:#889}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:10px;margin-bottom:10px}
.stat{padding:14px;background:rgba(255,255,255,0.03);border-radius:10px;text-align:center}
.stat .num{font-size:28px;color:#f7c948;font-weight:700}
.stat .lbl{font-size:11px;color:#667;margin-top:3px}
.item{display:flex;justify-content:space-between;align-items:center;padding:10px 0;border-bottom:1px solid rgba(255,255,255,0.05);gap:8px;flex-wrap:wrap}
.item:last-child{border:0}
.item-info{flex:1;min-width:150px;text-align:right}
.item-name{font-size:14px;font-weight:600}
.item-meta{font-size:11px;color:#667;margin-top:2px}
.item-actions{display:flex;gap:4px;flex-wrap:wrap}
.tabs{display:flex;gap:4px;margin-bottom:18px;flex-wrap:wrap}
.tab{padding:10px 18px;border-radius:8px;border:none;background:rgba(255,255,255,0.04);color:#667;font-size:13px;cursor:pointer;transition:0.2s}
.tab.active{background:linear-gradient(135deg,#f7c948,#ff8a00);color:#000;font-weight:700}
.tab:hover{background:rgba(255,255,255,0.08)}
.page{display:none}
.page.active{display:block}
.login-box{max-width:350px;margin:60px auto;text-align:center}
.login-box input{margin-bottom:12px}
.toast{position:fixed;bottom:20px;right:20px;background:#2ecc71;color:#fff;padding:14px 24px;border-radius:10px;font-size:14px;z-index:999;display:none;animation:slideUp .3s}
.toast.error{background:#e74c3c}
@keyframes slideUp{from{transform:translateY(20px);opacity:0}to{transform:translateY(0);opacity:1}}
.empty{color:#667;font-size:13px;text-align:center;padding:20px}
.modal{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.7);display:none;align-items:center;justify-content:center;z-index:999;padding:20px}
.modal-content{background:#1a1a2e;border-radius:14px;padding:24px;max-width:450px;width:100%;max-height:80vh;overflow-y:auto}
.modal h3{color:#f7c948;margin-bottom:15px}
.code-box{background:#0a0a12;border-radius:6px;padding:10px;font-family:monospace;font-size:12px;direction:ltr;text-align:left;word-break:break-all;margin:5px 0;color:#2ecc71}
.status-badge{display:inline-block;padding:2px 10px;border-radius:20px;font-size:11px;background:rgba(46,204,113,.15);color:#2ecc71}
</style>
</head>
<body>
<div class="container" id="loginScreen">
<div class="login-box card">
<h1>🏪 JOKER STORE</h1>
<p class="sub">𝓙𝓸𝓴𝓮𝓻丨𝓜4 • @VT_YC</p>
<h3 style="margin-bottom:15px">🔐 دخول الأدمن</h3>
<input type="password" id="pwd" placeholder="كلمة السر" onkeydown="if(event.key==='Enter')login()">
<button class="btn" onclick="login()" style="width:100%">دخول</button>
<div id="loginError" style="color:#e74c3c;font-size:13px;margin-top:10px;display:none"></div>
</div>
</div>
<div id="panel" class="hidden">
<h1>🏪 JOKER STORE</h1>
<p class="sub">𝓙𝓸𝓴𝓮𝓻丨𝓜4 • @VT_YC • <a href="#" onclick="logout()" style="color:#e74c3c;text-decoration:none">🚪 خروج</a></p>
<div class="tabs" id="tabs">
<button class="tab active" onclick="showTab('dashboard')">📊 لوحة</button>
<button class="tab" onclick="showTab('products')">📦 منتجات</button>
<button class="tab" onclick="showTab('add')">➕ إضافة</button>
<button class="tab" onclick="showTab('orders')">📋 طلبات</button>
<button class="tab" onclick="showTab('users')">👥 مستخدمين</button>
</div>
<div id="page-dashboard" class="page active"><div class="card"><div id="stats"><p class="empty">جاري التحميل...</p></div></div></div>
<div id="page-products" class="page"><div class="card"><h3>📦 المنتجات</h3><div id="prodsList"><p class="empty">جاري التحميل...</p></div></div></div>
<div id="page-add" class="page">
<div class="card"><h3>➕ إضافة منتج جديد</h3>
<label>اسم المنتج</label><input id="addName" placeholder="مثال: كود حساسية v1">
<label>الوصف</label><textarea id="addDesc" placeholder="وصف المنتج"></textarea>
<label>السعر (نجوم)</label><input id="addPrice" type="number" placeholder="50">
<label>الكود</label><textarea id="addCode" placeholder="الكود اللي يوصله المشتري"></textarea>
<button class="btn" onclick="addProduct()" style="width:100%;margin-top:5px">💾 حفظ المنتج</button>
</div></div>
<div id="page-orders" class="page"><div class="card"><h3>📋 جميع الطلبات</h3><div id="ordsList"><p class="empty">جاري التحميل...</p></div></div></div>
<div id="page-users" class="page"><div class="card"><h3>👥 المستخدمين</h3><div id="usersList"><p class="empty">جاري التحميل...</p></div></div></div>
</div>
<div id="editModal" class="modal" onclick="if(event.target==this)closeEdit()"><div class="modal-content">
<h3 id="editTitle">✏️ تعديل المنتج</h3>
<input id="editId" type="hidden">
<label>الاسم</label><input id="editName">
<label>الوصف</label><textarea id="editDesc"></textarea>
<label>السعر</label><input id="editPrice" type="number">
<label>الكود</label><textarea id="editCode"></textarea>
<button class="btn" onclick="saveEdit()">💾 حفظ</button>
<button class="btn btn-outline" onclick="closeEdit()">إلغاء</button>
</div></div>
<div id="toast" class="toast"></div>
<script>
var token='', PASS='VT_YC';
function toast(m,t){var e=document.getElementById('toast');e.textContent=m;e.className='toast'+(t||'');e.style.display='block';setTimeout(function(){e.style.display='none'},3000)}
async function login(){
  var p=document.getElementById('pwd').value,e=document.getElementById('loginError');e.style.display='none'
  try{
    var r=await fetch('/api/verify',{method:'POST',body:JSON.stringify({password:p})});
    if((await r.json()).admin){token=p;document.getElementById('loginScreen').classList.add('hidden');document.getElementById('panel').classList.remove('hidden');loadAll()}
    else{e.textContent='❌ كلمة السر خطأ';e.style.display='block'}
  }catch(x){e.textContent='❌ خطأ في الاتصال';e.style.display='block'}
}
function logout(){token='';document.getElementById('loginScreen').classList.remove('hidden');document.getElementById('panel').classList.add('hidden');document.getElementById('pwd').value=''}
function showTab(t){document.querySelectorAll('.tab').forEach(function(e){e.classList.remove('active')});document.querySelectorAll('.page').forEach(function(e){e.classList.remove('active')});document.querySelector('.tab[onclick*=\"'+t+'\"]').classList.add('active');document.getElementById('page-'+t).classList.add('active');if(t!='dashboard')loadTab(t)}
function loadTab(t){if(t=='products')loadProducts();if(t=='orders')loadOrders();if(t=='users')loadUsers()}
async function loadAll(){try{var r=await(await fetch('/api/stats',{headers:{Authorization:token}})).json();if(r.status=='ok')document.getElementById('stats').innerHTML='<div class=grid><div class=stat><div class=num>'+r.users+'</div><div class=lbl>المشتركين</div></div><div class=stat><div class=num>'+r.sales_count+'</div><div class=lbl>المبيعات</div></div><div class=stat><div class=num>'+r.sales_total+'</div><div class=lbl>النجوم</div></div></div>'}catch(e){};loadProducts();loadOrders();loadUsers()}
async function loadProducts(){
  try{
    var r=await(await fetch('/api/products')).json();
    if(r.status!='ok')return;var h='';
    if(r.products.length==0)h='<p class=empty>لا توجد منتجات</p>';
    else r.products.forEach(function(p){h+='<div class=item><div class=item-info><div class=item-name>📦 '+p.name+'</div><div class=item-meta>⭐ '+p.price+' | 🆔 '+p.id+(p.code?' | 🔑 '+p.code:'')+'</div></div><div class=item-actions><button class="btn btn-sm btn-blue" onclick="editProd(\''+p.id+'\')">✏️</button><button class="btn btn-sm btn-red" onclick="delProd(\''+p.id+'\')">🗑</button></div></div>'});
    document.getElementById('prodsList').innerHTML=h
  }catch(e){}
}
async function loadOrders(){
  try{
    var r=await(await fetch('/api/orders',{headers:{Authorization:token}})).json();
    if(r.status!='ok')return;var h='';
    if(r.orders.length==0)h='<p class=empty>لا توجد طلبات</p>';
    else r.orders.forEach(function(o){h+='<div class=item><div class=item-info><div class=item-name>📦 '+(o.product_name||'منتج محذوف')+'</div><div class=item-meta>👤 '+o.user_id+' | ⭐ '+o.price+' | 🕐 '+o.created_at+'</div></div><span class=status-badge>مدفوع ✓</span></div>'});
    document.getElementById('ordsList').innerHTML=h
  }catch(e){}
}
async function loadUsers(){
  try{
    var r=await(await fetch('/api/users',{headers:{Authorization:token}})).json();
    if(r.status!='ok')return;var h='';
    if(r.users.length==0)h='<p class=empty>لا يوجد مستخدمين</p>';
    else r.users.forEach(function(u){h+='<div class=item><div class=item-info><div class=item-name>👤 '+u.first_name+'</div><div class=item-meta>🆔 '+u.user_id+(u.username?' | @'+u.username:'')+'</div></div></div>'});
    document.getElementById('usersList').innerHTML=h
  }catch(e){}
}
async function addProduct(){
  var n=document.getElementById('addName').value,d=document.getElementById('addDesc').value,p=document.getElementById('addPrice').value,c=document.getElementById('addCode').value;
  if(!n||!p||!c){toast('❌ اسم, سعر وكود مطلوبين',' error');return}
  try{
    var r=await(await fetch('/api/products/add',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:n,description:d,price:parseInt(p),code:c})})).json();
    if(r.status=='ok'){toast('✅ تم إضافة المنتج');document.getElementById('addName').value='';document.getElementById('addDesc').value='';document.getElementById('addPrice').value='';document.getElementById('addCode').value='';loadProducts()}
    else toast('❌ فشل الإضافة',' error')
  }catch(e){toast('❌ خطأ',' error')}
}
async function delProd(id){
  if(!confirm('⚠️ تأكيد حذف المنتج '+id+'؟'))return;
  try{
    var r=await(await fetch('/api/products/delete',{method:'POST',headers:{'Content-Type':'application/json',Authorization:token},body:JSON.stringify({id:id})})).json();
    if(r.status=='ok'){toast('✅ تم حذف المنتج');loadProducts()}else toast('❌ فشل الحذف',' error')
  }catch(e){toast('❌ خطأ',' error')}
}
async function editProd(id){
  try{
    var r=await(await fetch('/api/products/'+id)).json();
    if(r.status!='ok')return;
    document.getElementById('editId').value=r.product.id;
    document.getElementById('editName').value=r.product.name;
    document.getElementById('editDesc').value=r.product.description||'';
    document.getElementById('editPrice').value=r.product.price;
    document.getElementById('editCode').value=r.product.code||'';
    document.getElementById('editModal').style.display='flex'
  }catch(e){toast('❌ خطأ',' error')}
}
function closeEdit(){document.getElementById('editModal').style.display='none'}
async function saveEdit(){
  var id=document.getElementById('editId').value,n=document.getElementById('editName').value,d=document.getElementById('editDesc').value,p=document.getElementById('editPrice').value,c=document.getElementById('editCode').value;
  try{
    var r=await(await fetch('/api/products/update',{method:'POST',headers:{'Content-Type':'application/json',Authorization:token},body:JSON.stringify({id:id,name:n,description:d,price:parseInt(p),code:c})})).json();
    if(r.status=='ok'){toast('✅ تم التحديث');closeEdit();loadProducts()}else toast('❌ فشل التحديث',' error')
  }catch(e){toast('❌ خطأ',' error')}
}
</script>
</body>
</html>"""

class H(http.server.BaseHTTPRequestHandler):
    def auth(self):
        return self.headers.get("Authorization", "") == ADMIN_PASS

    def json_resp(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False, default=str).encode())

    def json_body(self):
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length)) if length else {}

    def do_GET(self):
        if self.path in ("/", "/admin"):
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML.encode())
            return
        if self.path == "/api/verify":
            d = {"password": self.headers.get("X-Password", "")}
            if self.headers.get("Content-Length", "0") != "0":
                d = self.json_body()
            ok = d.get("password") == ADMIN_PASS
            self.json_resp({"status":"ok" if ok else "error","admin":ok}, 200 if ok else 401)
            return
        if self.path.startswith("/api/products/") and len(self.path) > 14:
            pid = self.path.split("/api/products/")[1]
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT * FROM products WHERE id=?", (pid,))
            row = c.fetchone()
            conn.close()
            if row:
                self.json_resp({"status":"ok","product":dict(row)})
            else:
                self.json_resp({"error":"not found"}, 404)
            return
        if self.path == "/api/products":
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT * FROM products ORDER BY name")
            rows = [dict(r) for r in c.fetchall()]
            conn.close()
            self.json_resp({"status":"ok","products":rows})
            return
        if self.path == "/api/stats":
            if not self.auth(): self.json_resp({"error":"unauthorized"}, 401); return
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM users"); users = c.fetchone()[0]
            c.execute("SELECT COUNT(*), COALESCE(SUM(price),0) FROM orders WHERE status='paid'"); r = c.fetchone()
            conn.close()
            self.json_resp({"status":"ok","users":users,"sales_count":r[0],"sales_total":r[1]})
            return
        if self.path == "/api/orders":
            if not self.auth(): self.json_resp({"error":"unauthorized"}, 401); return
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT o.*,p.name as product_name FROM orders o LEFT JOIN products p ON o.product_id=p.id ORDER BY o.created_at DESC")
            rows = [dict(r) for r in c.fetchall()]
            conn.close()
            self.json_resp({"status":"ok","orders":rows})
            return
        if self.path == "/api/users":
            if not self.auth(): self.json_resp({"error":"unauthorized"}, 401); return
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT * FROM users ORDER BY joined_at DESC")
            rows = [dict(r) for r in c.fetchall()]
            conn.close()
            self.json_resp({"status":"ok","users":rows})
            return
        self.json_resp({"error":"not found"}, 404)

    def do_POST(self):
        if self.path == "/api/verify":
            d = self.json_body()
            ok = d.get("password") == ADMIN_PASS
            self.json_resp({"status":"ok" if ok else "error","admin":ok}, 200 if ok else 401)
            return
        if self.path == "/api/products/add":
            if not self.auth(): self.json_resp({"error":"unauthorized"}, 401); return
            d = self.json_body()
            pid = f"p_{int(time.time()*1000)}"
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("INSERT INTO products (id,category_id,name,price,description,code,image) VALUES (?,?,?,?,?,?,?)",
                      (pid, "0", d["name"], int(d.get("price",0)), d.get("description",""), d.get("code",""), None))
            conn.commit()
            conn.close()
            self.json_resp({"status":"ok","product_id":pid})
            return
        if self.path == "/api/products/delete":
            if not self.auth(): self.json_resp({"error":"unauthorized"}, 401); return
            d = self.json_body()
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("DELETE FROM products WHERE id=?", (d["id"],))
            conn.commit()
            conn.close()
            self.json_resp({"status":"ok"})
            return
        if self.path == "/api/products/update":
            if not self.auth(): self.json_resp({"error":"unauthorized"}, 401); return
            d = self.json_body()
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("UPDATE products SET name=?,price=?,description=?,code=? WHERE id=?",
                      (d["name"], int(d.get("price",0)), d.get("description",""), d.get("code",""), d["id"]))
            conn.commit()
            conn.close()
            self.json_resp({"status":"ok"})
            return
        self.json_resp({"error":"not found"}, 404)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Password")
        self.end_headers()

    def log_message(self, format, *args): pass

if __name__ == "__main__":
    port = int(os.getenv("PORT", 9090))
    srv = http.server.HTTPServer(("0.0.0.0", port), H)
    print(f"✅ Admin Server on port {port}")
    srv.serve_forever()
