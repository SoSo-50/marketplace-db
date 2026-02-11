import os
import telebot
from telebot import types
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

# --- تنظیمات دیتابیس ---
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

BOT_TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

# --- تنظیمات اتصال دیتابیس ---
engine = None
db_session = None

try:
    if DATABASE_URL:
        engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=300)
        session_factory = sessionmaker(bind=engine)
        db_session = scoped_session(session_factory)
        print("✅ Database Connected.")
except Exception as e:
    print(f"❌ Database Connection Error: {e}")

# --- توابع کمکی ---

def get_logged_in_user(telegram_id):
    if not db_session: 
        print("❌ DB Session is None!")
        return None
        
    session = db_session()
    try:
        session.commit()
        
        print(f"🔍 Checking Login for Telegram ID: {telegram_id}")
        
        sql = text("SELECT user_id, first_name, username, phone, email, address FROM users WHERE telegram_id = :tid")
        user = session.execute(sql, {'tid': telegram_id}).fetchone()
        
        if user:
            print(f"✅ User Found: {user[2]} (ID: {user[0]})")
            return user
        else:
            print(f"⚠️ User NOT Found for ID: {telegram_id}")
            return None
            
    except Exception as e:
        print(f"❌ Error in get_logged_in_user: {e}")
        session.rollback()
        return None
    finally:
        pass 

def connect_telegram_to_account(username, password, telegram_id):
    if not db_session: return False
    session = db_session()
    try:
        print(f"🔐 Attempting login for: {username} with TID: {telegram_id}")
        
        # ۱. ابتدا هر اتصال قبلی را پاک می‌کنیم
        session.execute(text("UPDATE users SET telegram_id = NULL WHERE telegram_id = :tid"), {'tid': telegram_id})
        
        # ۲. پیدا کردن کاربر
        sql = text("SELECT user_id, password FROM users WHERE username = :u")
        user = session.execute(sql, {'u': username}).fetchone()
        
        if user:
            db_user_id = user[0]
            db_password_hash = user[1]
            
            # ۳. بررسی پسورد
            is_valid = False
            try:
                is_valid = check_password_hash(db_password_hash, password)
            except:
                is_valid = (db_password_hash == password)

            if is_valid:
                # ۴. آپدیت دیتابیس با Telegram ID
                update_sql = text("UPDATE users SET telegram_id = :tid WHERE user_id = :uid")
                session.execute(update_sql, {'tid': telegram_id, 'uid': db_user_id})
                session.commit() 
                print(f"✅ Login Successful! DB Updated for User ID: {db_user_id}")
                return True
            else:
                print("❌ Password Mismatch")
        else:
            print("❌ User Not Found")
        
        return False
    except Exception as e:
        session.rollback()
        print(f"❌ Login Exception: {e}")
        return False
    finally:
        db_session.remove()

def register_new_account(username, password, first_name, telegram_id):
    if not db_session: return False
    session = db_session()
    try:
        check = session.execute(text("SELECT user_id FROM users WHERE username = :u"), {'u': username}).fetchone()
        if check: return False

        hashed_pw = generate_password_hash(password)

        sql = text("""
            INSERT INTO users (username, password, first_name, telegram_id, role, is_active)
            VALUES (:u, :p, :fn, :tid, 'customer', TRUE)
        """)
        session.execute(sql, {'u': username, 'p': hashed_pw, 'fn': first_name, 'tid': telegram_id})
        session.commit()
        print(f"✅ Registered New User: {username}")
        return True
    except Exception as e:
        session.rollback()
        print(f"❌ Register Error: {e}")
        return False
    finally:
        db_session.remove()

# --- منوی اصلی ---
def main_menu(is_logged_in=False):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add('🛍 محصولات', '🔎 جستجو')
    markup.add('🛒 سبد خرید')
    
    if is_logged_in:
        markup.add('👤 پروفایل من', '🚪 خروج')
    else:
        markup.add('🔐 ورود | ثبت‌نام')
    
    markup.add('🔄 شروع مجدد ربات')
    return markup

# --- هندلر استارت و ری‌استارت ---
@bot.message_handler(commands=['start', 'restart'])
def send_welcome(message):
    try:
        bot.clear_step_handler_by_chat_id(message.chat.id)
    except: pass

    user = get_logged_in_user(message.from_user.id)
    
    if user:
        name = user[1] or user[2]
        bot.reply_to(message, f"سلام {name} عزیز! 👋\nربات آماده است.", reply_markup=main_menu(True))
    else:
        bot.reply_to(message, "به فروشگاه خوش آمدید! 🌹\nلطفاً برای استفاده کامل وارد شوید.", reply_markup=main_menu(False))

@bot.message_handler(func=lambda m: m.text == '🔄 شروع مجدد ربات')
def restart_btn(message):
    send_welcome(message)

# --- ورود و ثبت نام ---
@bot.message_handler(func=lambda m: m.text == '🔐 ورود | ثبت‌نام')
def auth_menu(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔐 ورود", callback_data="auth_login"))
    markup.add(types.InlineKeyboardButton("📝 ثبت‌نام", callback_data="auth_register"))
    bot.reply_to(message, "انتخاب کنید:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('auth_'))
def handle_auth(call):
    bot.answer_callback_query(call.id)
    action = call.data.split('_')[1]
    if action == 'login':
        msg = bot.send_message(call.message.chat.id, "👤 نام کاربری:", reply_markup=types.ForceReply())
        bot.register_next_step_handler(msg, lambda m: login_step_2(m))
    elif action == 'register':
        msg = bot.send_message(call.message.chat.id, "📝 نام کاربری جدید:", reply_markup=types.ForceReply())
        bot.register_next_step_handler(msg, lambda m: reg_step_2(m))

def login_step_2(message):
    if message.text in ['/start', '🔄 شروع مجدد ربات']: return send_welcome(message)
    username = message.text
    msg = bot.reply_to(message, "🔑 رمز عبور:", reply_markup=types.ForceReply())
    bot.register_next_step_handler(msg, lambda m: login_step_3(m, username))

def login_step_3(message, username):
    if connect_telegram_to_account(username, message.text, message.from_user.id):
        user = get_logged_in_user(message.from_user.id)
        if user:
            bot.reply_to(message, "✅ ورود موفقیت‌آمیز بود!", reply_markup=main_menu(True))
        else:
            bot.reply_to(message, "⚠️ ورود انجام شد اما دیتابیس هنوز آپدیت نشده. لطفاً یک بار 'شروع مجدد' را بزنید.", reply_markup=main_menu(True))
    else:
        bot.reply_to(message, "❌ نام کاربری یا رمز عبور اشتباه است.", reply_markup=main_menu(False))

def reg_step_2(message):
    if message.text in ['/start', '🔄 شروع مجدد ربات']: return send_welcome(message)
    username = message.text
    msg = bot.reply_to(message, "🔑 رمز عبور:", reply_markup=types.ForceReply())
    bot.register_next_step_handler(msg, lambda m: reg_step_3(m, username))

def reg_step_3(message, username):
    if register_new_account(username, message.text, message.from_user.first_name, message.from_user.id):
        bot.reply_to(message, "🎉 اکانت ساخته شد!", reply_markup=main_menu(True))
    else:
        bot.reply_to(message, "❌ نام کاربری تکراری.", reply_markup=main_menu(False))

# --- محصولات ---
@bot.message_handler(func=lambda m: m.text == '🛍 محصولات')
def show_products(message):
    if not db_session: return
    session = db_session()
    try:
        products = session.execute(text("SELECT product_id, name, price FROM product WHERE is_active = TRUE LIMIT 5")).fetchall()
        if not products:
            bot.reply_to(message, "محصولی یافت نشد.")
        else:
            bot.send_message(message.chat.id, "📦 **محصولات:**", parse_mode='Markdown')
            for prod in products:
                send_product_card(message.chat.id, prod)
    except Exception as e:
        print(f"Products Error: {e}")
        bot.reply_to(message, "خطا در دریافت لیست محصولات.")
    finally:
        db_session.remove()

def send_product_card(chat_id, prod):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(f"🛒 افزودن ({int(prod[2]):,} ت)", callback_data=f"add_{prod[0]}"))
    text = f"🏷 **{prod[1]}**\n💰 {int(prod[2]):,} تومان"
    bot.send_message(chat_id, text, reply_markup=markup, parse_mode='Markdown')

# --- افزودن به سبد ---
@bot.callback_query_handler(func=lambda call: call.data.startswith('add_'))
def add_to_cart(call):
    user = get_logged_in_user(call.from_user.id)
    
    if not user:
        print(f"⛔ Blocked add_to_cart for TID: {call.from_user.id} because user is None")
        bot.answer_callback_query(call.id, "⚠️ لطفاً ابتدا وارد حساب شوید", show_alert=True)
        return

    session = db_session()
    try:
        p_id = int(call.data.split('_')[1])
        print(f"🛒 Adding product {p_id} for User ID {user[0]}")
        
        sql = text("""
            INSERT INTO cart (user_id, product_id, quantity) VALUES (:uid, :pid, 1)
            ON CONFLICT (user_id, product_id) DO UPDATE SET quantity = cart.quantity + 1
        """)
        session.execute(sql, {'uid': user[0], 'pid': p_id})
        session.commit()
        bot.answer_callback_query(call.id, "✅ به سبد اضافه شد", show_alert=False)
    except Exception as e:
        session.rollback()
        print(f"❌ Add Cart Error: {e}")
        bot.answer_callback_query(call.id, "❌ خطا در افزودن", show_alert=True)
    finally:
        db_session.remove()

# --- سبد خرید ---
@bot.message_handler(func=lambda m: m.text == '🛒 سبد خرید')
def show_cart(message):
    user = get_logged_in_user(message.from_user.id)
    
    if not user:
        print(f"⛔ Blocked show_cart for TID: {message.from_user.id}")
        bot.reply_to(message, "برای مشاهده سبد خرید باید وارد شوید.", reply_markup=main_menu(False))
        return

    session = db_session()
    try:
        items = session.execute(text("""
            SELECT p.name, p.price, c.quantity 
            FROM cart c JOIN product p ON c.product_id = p.product_id 
            WHERE c.user_id = :uid
        """), {'uid': user[0]}).fetchall()
        
        if not items:
            bot.reply_to(message, "سبد خرید شما خالی است.")
            return

        total = 0
        msg = "🛒 **سبد خرید شما:**\n\n"
        for item in items:
            sub = item[1] * item[2]
            total += sub
            msg += f"- {item[0]} ({item[2]} عدد) = {int(sub):,}\n"
        msg += f"\n💰 **جمع کل: {int(total):,} تومان**"
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✅ نهایی کردن خرید", callback_data="checkout_final"))
        markup.add(types.InlineKeyboardButton("🗑 خالی کردن سبد", callback_data="cart_clear"))
        
        bot.send_message(message.chat.id, msg, reply_markup=markup, parse_mode='Markdown')
    except Exception as e:
        print(f"❌ Show Cart Error: {e}")
        bot.reply_to(message, "خطا در نمایش سبد.")
    finally:
        db_session.remove()

@bot.callback_query_handler(func=lambda call: call.data == 'cart_clear')
def clear_cart(call):
    user = get_logged_in_user(call.from_user.id)
    if not user: return
    
    session = db_session()
    try:
        session.execute(text("DELETE FROM cart WHERE user_id = :uid"), {'uid': user[0]})
        session.commit()
        bot.edit_message_text("🗑 سبد خرید خالی شد.", call.message.chat.id, call.message.message_id)
    except:
        session.rollback()
    finally:
        db_session.remove()

# --- نهایی سازی ---
@bot.callback_query_handler(func=lambda call: call.data == 'checkout_final')
def checkout(call):
    bot.answer_callback_query(call.id)
    user = get_logged_in_user(call.from_user.id)
    if not user: return

    session = db_session()
    try:
        addr = user[5] if user[5] and len(user[5]) > 5 else "خرید سریع تلگرامی"

        cart_items = session.execute(text("SELECT product_id, quantity FROM cart WHERE user_id = :uid"), {'uid': user[0]}).fetchall()
        if not cart_items:
            bot.send_message(call.message.chat.id, "سبد خالی است!")
            return

        total = 0
        order_items = []
        for item in cart_items:
            prod = session.execute(text("SELECT price FROM product WHERE product_id = :pid"), {'pid': item[0]}).fetchone()
            if prod:
                total += prod[0] * item[1]
                order_items.append({'pid': item[0], 'qty': item[1], 'price': prod[0]})

        oid = session.execute(text("""
            INSERT INTO orders (user_id, total_amount, shipping_address, status) 
            VALUES (:uid, :tot, :addr, 'Processing') RETURNING order_id
        """), {'uid': user[0], 'tot': total, 'addr': addr}).scalar()

        for i in order_items:
            session.execute(text("INSERT INTO order_item (order_id, product_id, quantity, item_price) VALUES (:oid, :pid, :qty, :pr)"),
                            {'oid': oid, 'pid': i['pid'], 'qty': i['qty'], 'pr': i['price']})

        session.execute(text("DELETE FROM cart WHERE user_id = :uid"), {'uid': user[0]})
        session.commit()

        bot.edit_message_text(f"✅ سفارش شما با موفقیت ثبت شد!\n🔖 کد رهگیری: `{oid}`\n💰 مبلغ: {int(total):,} تومان", 
                              call.message.chat.id, call.message.message_id, parse_mode='Markdown')
    except Exception as e:
        session.rollback()
        print(f"Checkout Error: {e}")
    finally:
        db_session.remove()

# --- پروفایل ---
@bot.message_handler(func=lambda m: m.text == '👤 پروفایل من')
def show_profile(message):
    user = get_logged_in_user(message.from_user.id)
    if not user:
        bot.reply_to(message, "شما لاگین نیستید.", reply_markup=main_menu(False))
        return
    
    msg = f"👤 {user[1]}\nنام کاربری: {user[2]}\nآدرس: {user[5] or '---'}"
    bot.reply_to(message, msg)

@bot.message_handler(func=lambda m: m.text == '🚪 خروج')
def logout(message):
    if not db_session: return
    session = db_session()
    try:
        session.execute(text("UPDATE users SET telegram_id = NULL WHERE telegram_id = :tid"), {'tid': message.from_user.id})
        session.commit()
        bot.reply_to(message, "خارج شدید.", reply_markup=main_menu(False))
    except:
        session.rollback()
    finally:
        db_session.remove()

# --- جستجو ---
@bot.message_handler(func=lambda m: m.text == '🔎 جستجو')
def ask_search(m):
    msg = bot.reply_to(m, "نام محصول:", reply_markup=types.ForceReply())
    bot.register_next_step_handler(msg, do_search)

def do_search(m):
    if m.text in ['🔄 شروع مجدد ربات', '🛍 محصولات', '🛒 سبد خرید']: return restart_btn(m)
    
    if not db_session: return
    session = db_session()
    try:
        res = session.execute(text("SELECT product_id, name, price FROM product WHERE name ILIKE :q"), {'q': f'%{m.text}%'}).fetchall()
        if res:
            bot.reply_to(m, f"✅ {len(res)} محصول:", reply_markup=main_menu(True))
            for p in res: send_product_card(m.chat.id, p)
        else:
            bot.reply_to(m, "یافت نشد.")
    except:
        session.rollback()
    finally:
        db_session.remove()