import telebot
import json
import os
import datetime
import time
from telebot import types

# ==================== ১. কনফিগারেশন ====================
# 🔑 আপনার BotFather থেকে পাওয়া API Token-টি নিচে " " এর ভেতরে বসান:
TOKEN = "8841425707:AAGEzw3D9qGHewUZeLvaQI6CCXJ2QzzbpMQ"

# আপনার টেলিগ্রাম আইডি (এডমিন ও ওনার)
ADMIN_ID = 8833538161

# বাধ্যতামূলক চ্যানেল ও গ্রুপ
CHANNELS = ["@workivax_payment_proof", "@WorkivaX_Support"]

# 🎯 আপনার আসল Adsterra Direct Link
ADSTERRA = "https://www.profitableratecpmnetwork.com/t0ii9m7xa?key=1e25f424ca7a2d7cf7626b79ee6470fb"

# 🏧 মিনিমাম উইথড্র লিমিট
MIN_W = 50.0

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
DB = "bot_db.json"
states = {}

# ==================== ২. ডাটাবেস হ্যান্ডলার ====================
def load_db():
    if not os.path.exists(DB):
        with open(DB, "w", encoding="utf-8") as f:
            json.dump({"users": {}, "tasks": [], "t_cnt": 1, "p_cnt": 1}, f, ensure_ascii=False, indent=4)
    with open(DB, "r", encoding="utf-8") as f:
        return json.load(f)

def save_db(data):
    with open(DB, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_user(db, uid):
    uid = str(uid)
    if uid not in db["users"]:
        db["users"][uid] = {"bal": 0.0, "dep": 0.0, "earn": 0.0, "refs": 0, "ads": 0, "date": "", "done": []}
        save_db(db)
    return db["users"][uid]

def check_join(uid):
    for ch in CHANNELS:
        try:
            if bot.get_chat_member(ch, uid).status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True

def main_kb(uid):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add("🛠️ কাজ করুন", "📺 Watch Ad", "📢 প্রমোট করুন", "👤 প্রোফাইল", "🔗 Refer & Earn", "📥 ডিপোজিট", "🏧 টাকা তুলুন")
    if uid == ADMIN_ID:
        kb.add("👨‍✈️ Admin Panel")
    return kb

# ==================== ৩. বট কমান্ড ও হ্যান্ডলার ====================
@bot.message_handler(commands=['start'])
def start(m):
    uid = m.from_user.id
    if not check_join(uid):
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("📢 Join Channel", url="https://t.me/workivax_payment_proof"))
        kb.add(types.InlineKeyboardButton("💬 Join Support", url="https://t.me/WorkivaX_Support"))
        kb.add(types.InlineKeyboardButton("✅ Joined / Check", callback_data="chk"))
        return bot.send_message(uid, "⚠️ বট ব্যবহার করতে বাধ্যতামূলক চ্যানেল ও গ্রুপে জয়েন করুন:", reply_markup=kb)
    
    db = load_db()
    args = m.text.split()
    if len(args) > 1 and args[1].isdigit():
        rid = int(args[1])
        if rid != uid and str(rid) in db["users"]:
            r_user = db["users"][str(rid)]
            if get_user(db, uid)["earn"] == 0.0:
                r_user["bal"] += 2.0
                r_user["earn"] += 2.0
                r_user["refs"] += 1
                save_db(db)
                try:
                    bot.send_message(rid, "🎉 আপনার রেফারেল লিংকে নতুন ইউজার জয়েন করেছে! আপনি ৳২.০০ বোনাস পেলেন।")
                except:
                    pass
                try:
                    bot.send_message(ADMIN_ID, f"👥 <b>নতুন রেফারেল জয়েন করেছে!</b>\n🆔 নতুন ইউজার: <code>{uid}</code>\n🎯 কার লিংকে: <code>{rid}</code>")
                except:
                    pass

    bot.send_message(uid, f"👋 স্বাগতম {m.from_user.first_name}!", reply_markup=main_kb(uid))

@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    uid = c.from_user.id
    if c.data == "chk":
        if check_join(uid):
            bot.answer_callback_query(c.id, "✅ এক্সেস নিশ্চিত!", show_alert=True)
            try:
                bot.delete_message(uid, c.message.message_id)
            except:
                pass
            bot.send_message(uid, "মূল মেনু:", reply_markup=main_kb(uid))
        else:
            bot.answer_callback_query(c.id, "❌ আপনি এখনো সবকটিতে জয়েন করেননি!", show_alert=True)
            
    elif c.data == "vad":
        db = load_db()
        u = get_user(db, uid)
        today = str(datetime.date.today())
        if u["date"] != today:
            u["date"] = today
            u["ads"] = 0
            save_db(db)
        if u["ads"] >= 20:
            return bot.answer_callback_query(c.id, "⚠️ আজকের দেখার লিমিট শেষ!", show_alert=True)
        u["bal"] += 0.50
        u["earn"] += 0.50
        u["ads"] += 1
        save_db(db)
        bot.answer_callback_query(c.id, "✅ ৳০.৫০ আপনার ব্যালেন্সে যোগ হয়েছে!", show_alert=True)
        try:
            bot.delete_message(uid, c.message.message_id)
        except:
            pass
            
    elif c.data.startswith("vt_"):
        tid = int(c.data.split("_")[1])
        db = load_db()
        u = get_user(db, uid)
        t = next((x for x in db["tasks"] if x["id"] == tid), None)
        if not t or tid in u["done"]:
            return bot.answer_callback_query(c.id, "❌ কাজটি আর উপলব্ধ নেই!", show_alert=True)
        states[uid] = {"act": "sp", "tid": tid}
        bot.send_message(uid, "📸 প্রমাণ হিসেবে স্ক্রিনশট বা আপনার ইউজারনেম/কমেন্ট পাঠান:")
        
    elif c.data.startswith("app_") or c.data.startswith("rej_"):
        if uid != ADMIN_ID:
            return
        act, pid, wid, tid = c.data.split("_")
        db = load_db()
        w = get_user(db, wid)
        t = next((x for x in db["tasks"] if x["id"] == int(tid)), None)
        if act == "app" and t:
            w["bal"] += t["reward"]
            w["earn"] += t["reward"]
            t["done"] = t.get("done", 0) + 1
            if t["done"] >= t["qty"]:
                t["status"] = "done"
            save_db(db)
            bot.send_message(int(wid), f"🎉 আপনার টাস্ক প্রুফ (#{tid}) অ্যাপ্রুভ হয়েছে এবং ৳{t['reward']} যোগ হয়েছে!")
        else:
            bot.send_message(int(wid), f"❌ আপনার টাস্ক প্রুফ (#{tid}) রিজেক্ট করা হয়েছে।")
        try:
            bot.edit_message_caption("✅ যাচাই সম্পন্ন হয়েছে", ADMIN_ID, c.message.message_id)
        except:
            pass
            
    elif c.data.startswith("tp_"):
        states[uid] = {"act": "ctitle", "type": c.data.split("_")[1]}
        bot.send_message(uid, "📌 টাস্কের শিরোনাম দিন (যেমন: YouTube Subscribe):")
        
    elif c.data.startswith("w_"):
        states[uid] = {"act": "wamt", "meth": c.data.split("_")[1]}
        bot.send_message(uid, f"📱 আপনার **{c.data.split('_')[1]}** নাম্বার এবং টাকার পরিমাণ লিখুন\n(উদাহরণ: `01700000000 50`)", parse_mode="Markdown")

@bot.message_handler(content_types=['text', 'photo'])
def msg(m):
    uid = m.from_user.id
    if not check_join(uid):
        return
    txt = m.text
    db = load_db()
    u = get_user(db, uid)
    st = states.get(uid, {})
    
    if st.get("act") == "sp" and (txt or m.photo):
        states.pop(uid, None)
        tid = st["tid"]
        t = next((x for x in db["tasks"] if x["id"] == tid), None)
        if not t:
            return
        u["done"].append(tid)
        pid = db["p_cnt"]
        db["p_cnt"] += 1
        save_db(db)
        
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("✅ Approve", callback_data=f"app_{pid}_{uid}_{tid}"), types.InlineKeyboardButton("❌ Reject", callback_data=f"rej_{pid}_{uid}_{tid}"))
        c_msg = f"📩 <b>নতুন প্রুফ জমা পড়েছে!</b>\n👤 User ID: <code>{uid}</code>\n📌 Task: #{tid} ({t['title']})\n💰 Reward: ৳{t['reward']}"
        
        if m.photo:
            bot.send_photo(ADMIN_ID, m.photo[-1].file_id, caption=c_msg, reply_markup=kb)
        else:
            bot.send_message(ADMIN_ID, c_msg + f"\n📝 Text: {txt}", reply_markup=kb)
        bot.send_message(uid, "✅ আপনার প্রুফ সফলভাবে জমা হয়েছে! এডমিন চেক করে ব্যালেন্স যুক্ত করবেন।")
        
    elif st.get("act") == "ctitle":
        states[uid]["title"] = txt
        states[uid]["act"] = "clink"
        bot.send_message(uid, "🔗 টাস্কের লিংক দিন:")
    elif st.get("act") == "clink":
        states[uid]["link"] = txt
        states[uid]["act"] = "creward"
        bot.send_message(uid, "💰 প্রতি কাজের জন্য ওয়ার্কারকে কত টাকা দিতে চান (যেমন: 1.50):")
    elif st.get("act") == "creward":
        try:
            rew = float(txt)
            if rew <= 0:
                raise Exception
            states[uid]["rew"] = rew
            states[uid]["act"] = "cqty"
            bot.send_message(uid, "👥 কতজন ওয়ার্কার প্রয়োজন তা লিখুন:")
        except:
            bot.send_message(uid, "❌ সঠিক সংখ্যা লিখুন!")
    elif st.get("act") == "cqty":
        try:
            qty = int(txt)
            data = states.pop(uid)
            cost = data["rew"] * qty
            if u["dep"] < cost:
                return bot.send_message(uid, f"❌ পর্যাপ্ত ডিপোজিট নেই! আপনার প্রয়োজন: ৳{cost:.2f}, আছে: ৳{u['dep']:.2f}")
            u["dep"] -= cost
            t = {"id": db["t_cnt"], "type": data["type"], "title": data["title"], "link": data["link"], "reward": data["rew"], "qty": qty, "done": 0, "status": "active"}
            db["t_cnt"] += 1
            db["tasks"].append(t)
            save_db(db)
            bot.send_message(uid, f"🎉 টাস্কটি সফলভাবে লাইভ হয়েছে! মোট খরচ: ৳{cost:.2f}")
        except:
            bot.send_message(uid, "❌ সঠিক পূর্ণসংখ্যা লিখুন!")

    elif st.get("act") == "wamt":
        states.pop(uid, None)
        try:
            parts = txt.split()
            num = parts[0]
            amt = float(parts[1])
            if amt < MIN_W or amt > u["bal"]:
                return bot.send_message(uid, "❌ পর্যাপ্ত ব্যালেন্স নেই অথবা সর্বনিম্ন লিমিটের চেয়ে কম!")
            u["bal"] -= amt
            save_db(db)
            bot.send_message(uid, "✅ আপনার উইথড্র রিকোয়েস্ট সফলভাবে জমা হয়েছে!")
            bot.send_message(ADMIN_ID, f"🔔 <b>নতুন উইথড্র রিকোয়েস্ট!</b>\n👤 User: <code>{uid}</code>\n💳 Method: {st['meth']}\n📱 Number: <code>{num}</code>\n💵 Amount: ৳{amt}")
        except:
            bot.send_message(uid, "❌ ভুল ফরম্যাট! সঠিক নিয়মে লিখুন (যেমন: `01700000000 50`)", parse_mode="Markdown")

    elif txt == "👤 প্রোফাইল":
        bot.send_message(uid, f"👤 <b>আপনার প্রোফাইল:</b>\n🆔 ID: <code>{uid}</code>\n💵 আয়ের ব্যালেন্স: ৳{u['bal']:.2f}\n💳 ডিপোজিট ব্যালেন্স: ৳{u['dep']:.2f}\n👥 মোট রেফার: {u['refs']} জন")
    elif txt == "📺 Watch Ad":
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("🔗 Open Ad", url=ADSTERRA))
        kb.add(types.InlineKeyboardButton("🎁 Claim ৳0.50", callback_data="vad"))
        bot.send_message(uid, "📺 নিচের লিংকে ক্লিক করে ১৫ সেকেন্ড দেখে এসে ক্লেইম করুন:", reply_markup=kb)
    elif txt == "🛠️ কাজ করুন":
        acts = [x for x in db["tasks"] if x["status"] == "active" and x["done"] < x["qty"] and x["id"] not in u["done"]]
        if not acts:
            return bot.send_message(uid, "❌ এই মুহূর্তে কোনো কাজ উপলব্ধ নেই।")
        kb = types.InlineKeyboardMarkup()
        for x in acts:
            kb.add(types.InlineKeyboardButton(f"[{x['type']}] {x['title']} (৳{x['reward']})", callback_data=f"vt_{x['id']}"))
        bot.send_message(uid, "📋 উপলব্ধ কাজসমূহ:", reply_markup=kb)
    elif txt == "📢 প্রমোট করুন":
        if u["dep"] < 1.0:
            return bot.send_message(uid, f"❌ পর্যাপ্ত ডিপোজিট ব্যালেন্স নেই! (বর্তমান: ৳{u['dep']:.2f})\nটাস্ক দিতে আগে ডিপোজিট করুন।")
        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.add(types.InlineKeyboardButton("YouTube", callback_data="tp_YouTube"), types.InlineKeyboardButton("TikTok", callback_data="tp_TikTok"), types.InlineKeyboardButton("Facebook", callback_data="tp_Facebook"), types.InlineKeyboardButton("Custom", callback_data="tp_Custom"))
        bot.send_message(uid, "📢 ক্যাটাগরি বেছে নিন:", reply_markup=kb)
    elif txt == "🔗 Refer & Earn":
        bot_un = bot.get_me().username
        bot.send_message(uid, f"🔗 <b>আপনার রেফারেল লিংক:</b>\n<code>https://t.me/{bot_un}?start={uid}</code>\n\nপ্রতি রেফারে পাবেন ৳২.০০ বোনাস!")
    elif txt == "📥 ডিপোজিট করুন":
        bot.send_message(uid, "📥 <b>ডিপোজিট করার নিয়ম:</b>\nবিকাশ/নগদ (Personal): <code>01700000000</code>\n\nটাকা পাঠানোর পর TrxID এবং আপনার ইউজার আইডি এডমিনকে দিন: @WorkivaX_Support")
    elif txt == "🏧 টাকা তুলুন":
        if u["bal"] < MIN_W:
            return bot.send_message(uid, f"⚠️ সর্বনিম্ন উইথড্র লিমিট ৳{MIN_W}। আপনার ব্যালেন্সে আছে: ৳{u['bal']:.2f}")
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("bKash", callback_data="w_bKash"), types.InlineKeyboardButton("Nagad", callback_data="w_Nagad"))
        bot.send_message(uid, "পেমেন্ট মেথড সিলেক্ট করুন:", reply_markup=kb)
    elif txt == "👨‍✈️ Admin Panel" and uid == ADMIN_ID:
        bot.send_message(uid, "👨‍✈️ <b>এডমিন প্যানেল:</b>\nইউজারকে ডিপোজিট দিতে লিখুন:\n<code>/addbalance <user_id> <amount></code>")

@bot.message_handler(commands=['addbalance'])
def addbal(m):
    if m.from_user.id != ADMIN_ID:
        return
    try:
        _, tuid, amt = m.text.split()
        db = load_db()
        u = get_user(db, tuid)
        u["dep"] += float(amt)
        save_db(db)
        bot.send_message(m.chat.id, f"✅ ইউজার {tuid}-কে ৳{amt} ডিপোজিট দেওয়া হয়েছে।")
        bot.send_message(int(tuid), f"🎉 আপনার অ্যাকাউন্টে ৳{amt} ডিপোজিট ব্যালেন্স যুক্ত হয়েছে!")
    except:
        bot.send_message(m.chat.id, "❌ সঠিক ফরম্যাটে লিখুন: `/addbalance <user_id> <amount>`", parse_mode="Markdown")

# ==================== ৪. অটো-রিকানেক্টিং লুপ ====================
print("WorkivaX Bot is running smoothly...")
while True:
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except Exception as e:
        print(f"Network Connection Error: {e}. Reconnecting in 5 seconds...")
        time.sleep(5)
