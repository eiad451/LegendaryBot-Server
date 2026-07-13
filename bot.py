#!/usr/bin/env python3
import os, sys, logging, sqlite3, json
from datetime import datetime, timedelta
from telegram import Update, LabeledPrice, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    PreCheckoutQueryHandler, ConversationHandler, ContextTypes, filters
)

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "bot.db")
IMAGE_PATH = os.getenv("IMAGE_PATH", os.path.join(BASE_DIR, "images"))

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "5548005854"))
DEV_NAME = "𝓙𝓸𝓴𝓮𝓻丨𝓜4"
DEV_USER = "@VT_YC"

CATEGORIES = {
    "1": {"name": "🟣 اكواد حساسية 95% هيدشوت", "hex": "#9B59B6"},
    "2": {"name": "🟣 حل مشكلة انتشار الطلق", "hex": "#9B59B6"},
    "3": {"name": "🔴 سر الثبات الاسطوري 85%", "hex": "#E74C3C"},
    "4": {"name": "🟢 إحتراف المواجهات القريبة", "hex": "#2ECC71"},
    "5": {"name": "🟢 إعدادات رفع الهيدشوت", "hex": "#2ECC71"},
}

CATEGORY_PRODUCTS = {
    "1": [
        {"id": "s1", "name": "🔥 كود حساسية 95% هيدشوت v1", "price": 50, "desc": "كود حساسية 95% هيدشوت - الاصدار الاول\nيدعم جميع الاجهزة\nاحترافية تامة"},
        {"id": "s2", "name": "🔥 كود حساسية 95% هيدشوت v2", "price": 80, "desc": "كود حساسية 95% هيدشوت - الاصدار الثاني\nتطوير جديد + ثبات"},
    ],
    "2": [
        {"id": "sp1", "name": "🔥 كود حل انتشار الطلق", "price": 60, "desc": "حل مشكلة انتشار الطلق نهائياً\nتحكم كامل بالركل"},
    ],
    "3": [
        {"id": "st1", "name": "🔥 سر الثبات الاسطوري 85%", "price": 100, "desc": "سر الثبات الاسطوري 85%\nثبات خرافي - اقوى كود"},
    ],
    "4": [
        {"id": "cl1", "name": "🔥 كود المواجهات القريبة", "price": 70, "desc": "احتراف المواجهات القريبة\nتسديد سريع + دقة"},
    ],
    "5": [
        {"id": "hs1", "name": "🔥 اعدادات رفع الهيدشوت", "price": 90, "desc": "اعدادات رفع الهيدشوت\nنسبة هيدشوت 99%"},
    ],
}

CATEGORY_MAP = {
    "🟣 اكواد حساسية 95% هيدشوت – مدفوع": "1",
    "🟣 حل مشكلة انتشار الطلق – مدفوع": "2",
    "🔴 سر الثبات الاسطوري 85% – مدفوع": "3",
    "🟢 إحتراف المواجهات القريبة – مدفوع": "4",
    "🟢 إعدادات رفع الهيدشوت – مدفوع": "5",
}

# ─── Conversation States ───
(ADD_NAME, ADD_DESC, ADD_PRICE, ADD_CODE, ADD_IMAGE,
 DEL_ID, PRICE_ID, PRICE_VAL, IMAGE_ID, IMAGE_FILE, DESC_ID, DESC_TEXT,
 DISCOUNT_PROD, DISCOUNT_PERCENT, DISCOUNT_HOURS) = range(15)

# ═══════════════════════════════════════════
# DATABASE
# ═══════════════════════════════════════════

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS products (
            id TEXT PRIMARY KEY, category_id TEXT NOT NULL, name TEXT NOT NULL,
            price INTEGER NOT NULL, description TEXT, code TEXT NOT NULL, image TEXT
        );
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
            product_id TEXT NOT NULL, price INTEGER NOT NULL,
            status TEXT DEFAULT 'paid', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS discounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, product_id TEXT,
            discount_percent INTEGER NOT NULL, expires_at TIMESTAMP NOT NULL, active INTEGER DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT);
    """)
    conn.commit()
    conn.close()

def get_setting(key, default=None):
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key=?", (key,))
    row = c.fetchone(); conn.close()
    return row["value"] if row else default

def set_setting(key, value):
    conn = get_conn(); c = conn.cursor()
    c.execute("REPLACE INTO settings (key, value) VALUES (?,?)", (key, value))
    conn.commit(); conn.close()

def add_user(user_id, username, first_name):
    conn = get_conn(); c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?,?,?)",
              (user_id, username, first_name))
    conn.commit(); conn.close()

def get_user_count():
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    r = c.fetchone()[0]; conn.close()
    return r

def get_total_sales():
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT COUNT(*), COALESCE(SUM(price),0) FROM orders WHERE status='paid'")
    r = c.fetchone(); conn.close()
    return {"count": r[0], "total": r[1]}

def save_product(product_id, category_id, name, price, description, code, image=None):
    conn = get_conn(); c = conn.cursor()
    c.execute("REPLACE INTO products (id, category_id, name, price, description, code, image) VALUES (?,?,?,?,?,?,?)",
              (product_id, category_id, name, price, description, code, image))
    conn.commit(); conn.close()

def get_product(product_id):
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT * FROM products WHERE id=?", (product_id,))
    r = c.fetchone(); conn.close()
    return dict(r) if r else None

def get_category_products(category_id):
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT * FROM products WHERE category_id=?", (category_id,))
    rows = [dict(r) for r in c.fetchall()]; conn.close()
    return rows

def get_all_products():
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT * FROM products")
    rows = [dict(r) for r in c.fetchall()]; conn.close()
    return rows

def delete_product(product_id):
    conn = get_conn(); c = conn.cursor()
    c.execute("DELETE FROM products WHERE id=?", (product_id,))
    conn.commit(); conn.close()

def add_order(user_id, product_id, price):
    conn = get_conn(); c = conn.cursor()
    c.execute("INSERT INTO orders (user_id, product_id, price) VALUES (?,?,?)",
              (user_id, product_id, price))
    conn.commit(); conn.close()

def get_user_orders(user_id):
    conn = get_conn(); c = conn.cursor()
    c.execute("""SELECT o.*, p.name as product_name, p.code FROM orders o
                  LEFT JOIN products p ON o.product_id = p.id
                  WHERE o.user_id=? AND o.status='paid' ORDER BY o.created_at DESC""", (user_id,))
    rows = [dict(r) for r in c.fetchall()]; conn.close()
    return rows

def set_discount(product_id, percent, hours):
    expires = (datetime.now() + timedelta(hours=hours)).isoformat()
    conn = get_conn(); c = conn.cursor()
    c.execute("INSERT INTO discounts (product_id, discount_percent, expires_at) VALUES (?,?,?)",
              (product_id, percent, expires))
    conn.commit(); conn.close()

def get_active_discounts():
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT * FROM discounts WHERE active=1 AND expires_at > datetime('now')")
    rows = [dict(r) for r in c.fetchall()]; conn.close()
    return rows

def get_product_discount(product_id):
    now = datetime.now().isoformat()
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT * FROM discounts WHERE product_id=? AND active=1 AND expires_at > ? ORDER BY expires_at DESC LIMIT 1",
              (product_id, now))
    r = c.fetchone(); conn.close()
    return dict(r) if r else None

def deactivate_expired_discounts():
    conn = get_conn(); c = conn.cursor()
    c.execute("UPDATE discounts SET active=0 WHERE expires_at < datetime('now')")
    conn.commit(); conn.close()

# ═══════════════════════════════════════════
# KEYBOARDS
# ═══════════════════════════════════════════

def main_reply_keyboard():
    keyboard = [
        [KeyboardButton("💳 شحن نقاط في البوت (تلقائي)"), KeyboardButton("📊 إحصائيات البوت")],
        [KeyboardButton("🟣 اكواد حساسية 95% هيدشوت – مدفوع")],
        [KeyboardButton("🟣 حل مشكلة انتشار الطلق – مدفوع")],
        [KeyboardButton("🔴 سر الثبات الاسطوري 85% – مدفوع")],
        [KeyboardButton("🟢 إحتراف المواجهات القريبة – مدفوع")],
        [KeyboardButton("🟢 إعدادات رفع الهيدشوت – مدفوع")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def main_menu_text():
    return "🎯 مرحباً بك في متجر الأكواد الرسمي 🎯\n\n👑 المطور: 𝓙𝓸𝓴𝓮𝓻丨𝓜4\n🆔 اليوزر: @VT_YC\n\n📌 اختر القسم المناسب من الازرار ادناه:"

def category_keyboard(cat_id):
    products = CATEGORY_PRODUCTS.get(cat_id, [])
    keyboard = [[InlineKeyboardButton(f"{p['name']} - ⭐{p['price']} نجمة", callback_data=f"prod_{p['id']}")] for p in products]
    keyboard.append([InlineKeyboardButton("⬅️ رجوع للقائمة الرئيسية", callback_data="back_main")])
    return InlineKeyboardMarkup(keyboard)

def product_inline_keyboard(product_id, price):
    keyboard = [
        [InlineKeyboardButton(f"🟢 شراء بواسطة النجوم ⭐{price}", callback_data=f"buy_{product_id}")],
        [InlineKeyboardButton("🔴 إلغاء ❌", callback_data="back_main")],
    ]
    return InlineKeyboardMarkup(keyboard)

def back_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ رجوع للقائمة الرئيسية", callback_data="back_main")]])

def admin_main_keyboard():
    keyboard = [
        [InlineKeyboardButton("➕ اضافة منتج", callback_data="admin_add_product")],
        [InlineKeyboardButton("🗑 حذف منتج", callback_data="admin_del_product")],
        [InlineKeyboardButton("📋 عرض جميع المنتجات", callback_data="admin_list")],
        [InlineKeyboardButton("💰 تغيير سعر منتج", callback_data="admin_price")],
        [InlineKeyboardButton("🖼 تغيير صورة منتج", callback_data="admin_image")],
        [InlineKeyboardButton("📝 تغيير وصف منتج", callback_data="admin_desc")],
        [InlineKeyboardButton("🎯 عرض / ايقاف عرض", callback_data="admin_discount")],
        [InlineKeyboardButton("📊 الاحصائيات", callback_data="admin_stats")],
        [InlineKeyboardButton("🚪 خروج", callback_data="back_main")],
    ]
    return InlineKeyboardMarkup(keyboard)

# ═══════════════════════════════════════════
# USER HANDLERS
# ═══════════════════════════════════════════

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(user.id, user.username, user.first_name)
    text = main_menu_text()
    if update.message:
        await update.message.reply_text(text, reply_markup=main_reply_keyboard())
    else:
        await update.callback_query.message.reply_text(text, reply_markup=main_reply_keyboard())

async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = update.effective_user
    add_user(user.id, user.username, user.first_name)

    if text == "📊 إحصائيات البوت":
        users = get_user_count()
        sales = get_total_sales()
        msg = f"""📊 *احصائيات البوت*
━━━━━━━━━━━━━━
👥 *عدد المشتركين:* {users}
💰 *اجمالي المبيعات:* {sales['count']} عملية
⭐ *اجمالي النجوم:* {sales['total']}
━━━━━━━━━━━━━━
👑 {DEV_NAME} - {DEV_USER}"""
        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=back_keyboard())

    elif text == "💳 شحن نقاط في البوت (تلقائي)":
        msg = """💳 *شحن نقاط (نجوم تليجرام)*

لشحن رصيدك بالنجوم:
1️⃣ تأكد من ان رصيد محفظتك كافي
2️⃣ اختر المنتج الذي تريده
3️⃣ اضغط على "شراء بواسطة النجوم"
4️⃣ اتمم الدفع عبر نافذة تليجرام الرسمية

⭐ *النجوم تخصم من محفظتك تلقائياً*
✅ *الكود يوصلك فور الدفع!*"""
        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=back_keyboard())

    elif text in CATEGORY_MAP:
        cat_id = CATEGORY_MAP[text]
        cat_info = CATEGORIES[cat_id]
        await update.message.reply_text(
            f"*{cat_info['name']}*\nاختر المنتج المناسب:",
            parse_mode="Markdown", reply_markup=category_keyboard(cat_id))

    elif text.startswith("/admin") and user.id == ADMIN_ID:
        await update.message.reply_text(
            "🛠 *لوحة تحكم الأدمن*\nاختر ما تريد:",
            parse_mode="Markdown", reply_markup=admin_main_keyboard())

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try: await query.answer()
    except: pass
    data = query.data

    if data == "back_main":
        await start(update, context)
        return

    if data.startswith("prod_"):
        pid = data.replace("prod_", "")
        for cat in CATEGORY_PRODUCTS.values():
            for p in cat:
                if p["id"] == pid:
                    img_path = os.path.join(IMAGE_PATH, f"{pid}.jpg")
                    caption = f"""{p['name']}
━━━━━━━━━━━━━━
{p['desc']}
━━━━━━━━━━━━━━
⭐ السعر: {p['price']} نجمة

💡 اضغط شراء للدفع via Telegram Stars"""
                    if os.path.exists(img_path):
                        with open(img_path, "rb") as f:
                            await query.message.reply_photo(f, caption=caption, reply_markup=product_inline_keyboard(pid, p["price"]))
                    else:
                        await query.message.reply_text(caption, reply_markup=product_inline_keyboard(pid, p["price"]))
                    return

    if data.startswith("buy_"):
        pid = data.replace("buy_", "")
        product = None
        for cat in CATEGORY_PRODUCTS.values():
            for p in cat:
                if p["id"] == pid:
                    product = p
                    break
        if not product:
            await query.edit_message_text("المنتج غير موجود ❌")
            return

        context.user_data["pending_product"] = product
        payload = f"pay_{pid}_{query.from_user.id}"
        try:
            await context.bot.send_invoice(
                chat_id=query.message.chat_id,
                title=product["name"],
                description=product["desc"],
                payload=payload,
                provider_token="",
                currency="XTR",
                prices=[LabeledPrice(label=product["name"], amount=product["price"])],
                need_name=False, need_phone_number=False,
                need_email=False, need_shipping_address=False, is_flexible=False,
            )
        except Exception as e:
            logger.error(f"send_invoice error: {e}")
            await query.message.reply_text(f"❌ حدث خطأ في الدفع: {e}")
        return

    if data in CATEGORIES:
        await query.message.reply_text(
            f"*{CATEGORIES[data]['name']}*\nاختر المنتج:",
            parse_mode="Markdown", reply_markup=category_keyboard(data))
        return

    if data == "admin_stats":
        users = get_user_count()
        sales = get_total_sales()
        await query.edit_message_text(
            f"📊 *الاحصائيات*\n👥 المشتركين: {users}\n💰 المبيعات: {sales['count']}\n⭐ النجوم: {sales['total']}",
            parse_mode="Markdown", reply_markup=admin_main_keyboard())
        return

    await query.edit_message_text("⚠️ امر غير معروف", reply_markup=back_keyboard())

async def pre_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.pre_checkout_query
    await q.answer(ok=q.invoice_payload.startswith("pay_"))

async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    payload = update.message.successful_payment.invoice_payload
    parts = payload.split("_")
    if len(parts) >= 2:
        pid = parts[1]
        product = None
        for cat in CATEGORY_PRODUCTS.values():
            for p in cat:
                if p["id"] == pid:
                    product = p
                    break
        if not product:
            product = get_product(pid)
        if product:
            code = get_product(pid)
            actual_code = code["code"] if code else product.get("code", f"{pid}_CODE")
            add_order(user.id, pid, product["price"])
            code_text = f"""🎉 *تم الشراء بنجاح!* 🎉

━━━━━━━━━━━━━━
📦 *المنتج:* {product['name']}
⭐ *المدفوع:* {product['price']} نجمة
━━━━━━━━━━━━━━

🔑 *الكود الخاص بك:*
`{actual_code}`

💡 *تم حفظ الكود في مشترياتك*
━━━━━━━━━━━━━━
👑 {DEV_NAME} - {DEV_USER}"""
            await update.message.reply_text(code_text, parse_mode="Markdown")

async def my_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    orders = get_user_orders(update.effective_user.id)
    if not orders:
        await update.message.reply_text("🚫 لم تشتري اي منتج بعد!")
        return
    msg = "📦 *مشترياتي*\n━━━━━━━━━━━━━━\n"
    for o in orders:
        msg += f"• {o['product_name']} - `{o['code']}`\n"
    msg += f"\n━━━━━━━━━━━━━━\n👑 {DEV_NAME}"
    await update.message.reply_text(msg, parse_mode="Markdown")

# ═══════════════════════════════════════════
# ADMIN HANDLERS
# ═══════════════════════════════════════════

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ غير مصرح لك")
        return
    await update.message.reply_text("🛠 *لوحة تحكم الأدمن المطلقة*\nاختر ما تريد:", parse_mode="Markdown", reply_markup=admin_main_keyboard())

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if update.effective_user.id != ADMIN_ID:
        await query.edit_message_text("⛔ غير مصرح لك")
        return

    if data == "admin_add_product":
        await query.edit_message_text("📝 *اضافة منتج جديد*\nأرسل *اسم المنتج*:", parse_mode="Markdown")
        return ADD_NAME

    elif data == "admin_del_product":
        products = get_all_products()
        if not products:
            await query.edit_message_text("🚫 لا يوجد منتجات", reply_markup=admin_main_keyboard())
            return
        keyboard = [[InlineKeyboardButton(f"🗑 {p['name']}", callback_data=f"admin_del_{p['id']}")] for p in products]
        keyboard.append([InlineKeyboardButton("⬅️ رجوع", callback_data="admin_back")])
        await query.edit_message_text("اختر منتج للحذف:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    elif data.startswith("admin_del_"):
        delete_product(data.replace("admin_del_", ""))
        await query.edit_message_text("✅ تم حذف المنتج", reply_markup=admin_main_keyboard())
        return

    elif data == "admin_list":
        products = get_all_products()
        if not products:
            await query.edit_message_text("🚫 لا يوجد منتجات", reply_markup=admin_main_keyboard())
            return
        msg = "📋 *جميع المنتجات:*\n━━━━━━━━━━━━━━\n"
        for p in products:
            msg += f"🆔 `{p['id']}` | {p['name']}\n⭐ {p['price']}\n━━━━━━━━━━━━━━\n"
        await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=admin_main_keyboard())
        return

    elif data == "admin_price":
        products = get_all_products()
        if not products:
            await query.edit_message_text("🚫 لا يوجد منتجات", reply_markup=admin_main_keyboard())
            return
        keyboard = [[InlineKeyboardButton(f"💰 {p['name']} (⭐{p['price']})", callback_data=f"admin_pr_{p['id']}")] for p in products]
        keyboard.append([InlineKeyboardButton("⬅️ رجوع", callback_data="admin_back")])
        await query.edit_message_text("اختر منتج لتغيير سعره:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    elif data.startswith("admin_pr_"):
        context.user_data["edit_pid"] = data.replace("admin_pr_", "")
        await query.edit_message_text(f"✏️ أرسل السعر الجديد بالنجوم:", parse_mode="Markdown")
        return PRICE_VAL

    elif data == "admin_image":
        products = get_all_products()
        if not products:
            await query.edit_message_text("🚫 لا يوجد منتجات", reply_markup=admin_main_keyboard())
            return
        keyboard = [[InlineKeyboardButton(f"🖼 {p['name']}", callback_data=f"admin_img_{p['id']}")] for p in products]
        keyboard.append([InlineKeyboardButton("⬅️ رجوع", callback_data="admin_back")])
        await query.edit_message_text("اختر منتج لتغيير صورته:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    elif data.startswith("admin_img_"):
        context.user_data["edit_pid"] = data.replace("admin_img_", "")
        await query.edit_message_text("🖼 أرسل الصورة الجديدة:", parse_mode="Markdown")
        return IMAGE_FILE

    elif data == "admin_desc":
        products = get_all_products()
        if not products:
            await query.edit_message_text("🚫 لا يوجد منتجات", reply_markup=admin_main_keyboard())
            return
        keyboard = [[InlineKeyboardButton(f"📝 {p['name']}", callback_data=f"admin_desc_{p['id']}")] for p in products]
        keyboard.append([InlineKeyboardButton("⬅️ رجوع", callback_data="admin_back")])
        await query.edit_message_text("اختر منتج لتغيير وصفه:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    elif data.startswith("admin_desc_"):
        context.user_data["edit_pid"] = data.replace("admin_desc_", "")
        await query.edit_message_text("📝 أرسل الوصف الجديد:", parse_mode="Markdown")
        return DESC_TEXT

    elif data == "admin_discount":
        products = get_all_products()
        if not products:
            await query.edit_message_text("🚫 لا يوجد منتجات", reply_markup=admin_main_keyboard())
            return
        active = get_active_discounts()
        msg = "🎯 *نظام العروض*\n"
        if active:
            msg += "━━━━━━━━━━━━━━\n*العروض النشطة:*\n"
            for d in active:
                msg += f"🆔 {d['product_id']} | خصم {d['discount_percent']}%\n"
        msg += "\nاختر منتج لاضافة عرض:"
        keyboard = [[InlineKeyboardButton(f"🎯 {p['name']}", callback_data=f"admin_disc_{p['id']}")] for p in products]
        keyboard.append([InlineKeyboardButton("⬅️ رجوع", callback_data="admin_back")])
        await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    elif data.startswith("admin_disc_"):
        context.user_data["disc_pid"] = data.replace("admin_disc_", "")
        await query.edit_message_text("🎯 أرسل نسبة الخصم (رقم فقط):")
        return DISCOUNT_PERCENT

    elif data == "admin_stats":
        users = get_user_count(); sales = get_total_sales()
        await query.edit_message_text(
            f"📊 *الاحصائيات*\n👥 المشتركين: {users}\n💰 المبيعات: {sales['count']}\n⭐ النجوم: {sales['total']}",
            parse_mode="Markdown", reply_markup=admin_main_keyboard())
        return

    elif data == "admin_back":
        await query.edit_message_text("🛠 *لوحة تحكم الأدمن*", parse_mode="Markdown", reply_markup=admin_main_keyboard())
        return

async def add_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["add_name"] = update.message.text
    await update.message.reply_text("📝 أرسل *وصف* المنتج:", parse_mode="Markdown")
    return ADD_DESC

async def add_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["add_desc"] = update.message.text
    await update.message.reply_text("💰 أرسل *السعر* بالنجوم (رقم):", parse_mode="Markdown")
    return ADD_PRICE

async def add_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["add_price"] = int(update.message.text)
        await update.message.reply_text("🔑 أرسل *الكود* (الذي سيوصله للمشتري):", parse_mode="Markdown")
        return ADD_CODE
    except:
        await update.message.reply_text("⚠️ يجب ان يكون رقماً صحيحاً، حاول مرة اخرى:")
        return ADD_PRICE

async def add_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["add_code"] = update.message.text
    context.user_data["add_pid"] = f"p_{update.message.from_user.id}_{int(__import__('time').time())}"
    await update.message.reply_text("🖼 أرسل *صورة* المنتج (او ارسل /skip للتخطي):", parse_mode="Markdown")
    return ADD_IMAGE

async def add_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = context.user_data
    pid = user_data["add_pid"]
    if update.message.photo:
        photo = update.message.photo[-1]
        os.makedirs(IMAGE_PATH, exist_ok=True)
        await photo.get_file().download_to_drive(os.path.join(IMAGE_PATH, f"{pid}.jpg"))
    save_product(pid, "0", user_data["add_name"], user_data["add_price"], user_data["add_desc"], user_data["add_code"], f"{pid}.jpg" if update.message.photo else None)
    await update.message.reply_text(f"✅ *تم اضافة المنتج بنجاح!*\n🆔 `{pid}`", parse_mode="Markdown", reply_markup=admin_main_keyboard())
    return ConversationHandler.END

async def skip_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = context.user_data
    save_product(user_data["add_pid"], "0", user_data["add_name"], user_data["add_price"], user_data["add_desc"], user_data["add_code"], None)
    await update.message.reply_text(f"✅ *تم اضافة المنتج بنجاح!*\n🆔 `{user_data['add_pid']}`", parse_mode="Markdown", reply_markup=admin_main_keyboard())
    return ConversationHandler.END

def get_product_by_id(pid):
    for cat in CATEGORY_PRODUCTS.values():
        for p in cat:
            if p["id"] == pid:
                return {"id": p["id"], "category_id": "0", "name": p["name"], "price": p["price"],
                        "description": p.get("desc", ""), "code": p.get("code", f"{pid}_CODE"), "image": None}
    return get_product(pid)

async def set_price_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        price = int(update.message.text)
        pid = context.user_data.get("edit_pid")
        p = get_product_by_id(pid)
        if p:
            save_product(pid, p["category_id"], p["name"], price, p["description"], p["code"], p["image"])
            await update.message.reply_text(f"✅ تم تحديث السعر الى {price} نجمة", reply_markup=admin_main_keyboard())
        else:
            await update.message.reply_text("⚠️ المنتج غير موجود", reply_markup=admin_main_keyboard())
    except:
        await update.message.reply_text("⚠️ يجب ان يكون رقماً")
    return ConversationHandler.END

async def set_image_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        pid = context.user_data.get("edit_pid")
        os.makedirs(IMAGE_PATH, exist_ok=True)
        await update.message.photo[-1].get_file().download_to_drive(os.path.join(IMAGE_PATH, f"{pid}.jpg"))
        await update.message.reply_text("✅ تم تحديث الصورة", reply_markup=admin_main_keyboard())
    else:
        await update.message.reply_text("⚠️ يرجى ارسال صورة")
    return ConversationHandler.END

async def set_desc_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pid = context.user_data.get("edit_pid")
    p = get_product_by_id(pid)
    if p:
        save_product(pid, p["category_id"], p["name"], p["price"], update.message.text, p["code"], p["image"])
        await update.message.reply_text("✅ تم تحديث الوصف", reply_markup=admin_main_keyboard())
    else:
        await update.message.reply_text("⚠️ المنتج غير موجود", reply_markup=admin_main_keyboard())
    return ConversationHandler.END

async def set_discount_percent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["disc_percent"] = int(update.message.text)
        await update.message.reply_text("⏰ أرسل *مدة العرض بالساعات* (رقم):", parse_mode="Markdown")
        return DISCOUNT_HOURS
    except:
        await update.message.reply_text("⚠️ يجب ان يكون رقماً")
        return DISCOUNT_PERCENT

async def set_discount_hours(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        hours = int(update.message.text)
        pid = context.user_data.get("disc_pid")
        percent = context.user_data.get("disc_percent")
        set_discount(pid, percent, hours)
        await update.message.reply_text(f"✅ *تم تفعيل العرض!*\n🎯 خصم {percent}% لمدة {hours} ساعة", parse_mode="Markdown", reply_markup=admin_main_keyboard())
    except:
        await update.message.reply_text("⚠️ يجب ان يكون رقماً")
    return ConversationHandler.END

# ═══════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════

def main():
    TOKEN = BOT_TOKEN or input("ادخل توكن البوت: ").strip()
    if not TOKEN:
        print("❌ لا يوجد توكن")
        return

    init_db()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("admin_products", my_products))

    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_callback, pattern="^admin_add_product$")],
        states={
            ADD_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_name)],
            ADD_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_desc)],
            ADD_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_price)],
            ADD_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_code)],
            ADD_IMAGE: [
                MessageHandler(filters.PHOTO, add_image),
                CommandHandler("skip", skip_image),
            ],
        },
        fallbacks=[],
    ))

    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_callback, pattern="^admin_pr_")],
        states={PRICE_VAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_price_value)]},
        fallbacks=[],
    ))

    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_callback, pattern="^admin_img_")],
        states={IMAGE_FILE: [MessageHandler(filters.PHOTO, set_image_file)]},
        fallbacks=[],
    ))

    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_callback, pattern="^admin_desc_")],
        states={DESC_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_desc_text)]},
        fallbacks=[],
    ))

    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_callback, pattern="^admin_disc_")],
        states={
            DISCOUNT_PERCENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_discount_percent)],
            DISCOUNT_HOURS: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_discount_hours)],
        },
        fallbacks=[],
    ))

    app.add_handler(CallbackQueryHandler(admin_callback, pattern="^admin_"))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(PreCheckoutQueryHandler(pre_checkout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu))

    logger.info("✅ البوت يعمل...")
    print("✅ البوت يعمل بنجاح!")
    print(f"👑 المطور: @VT_YC")
    print("❌ اضغط Ctrl+C لايقاف البوت")

    app.run_polling()

if __name__ == "__main__":
    main()
