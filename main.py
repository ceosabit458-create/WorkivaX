import telebot
import json
import os
import datetime
import time
from telebot import types

# ==================== ১. কনফিগারেশন ====================
TOKEN = "8841425707:AAGEzw3D9qGHewUZeLvaQI6CCXJ2QzzbpMQ"

ADMIN_ID = 8833538161

CHANNELS = ["@workivax_payment_proof", "@WorkivaX_Support"]

ADSTERRA = "https://www.profitableratecpmnetwork.com/t0ii9m7xa?key=1e25f424ca7a2d7cf7626b79ee6470fb"

# Earning / Withdrawal settings
MIN_W = 50.0
REFERRAL_REWARD = 5.0
AD_REWARD = 0.06
FREE_DAILY_AD_LIMIT = 5
PREMIUM_DAILY_AD_LIMIT = 20

# Premium settings
PREMIUM_PRICE_USD = 1.0
PREMIUM_DAYS = 30
PREMIUM_JOIN_REWARD = 5.0

# এখানে আপনার আসল $1 payment instructions বসাবেন
PREMIUM_PAYMENT_INFO = (
    "💳 Premium Membership Fee: $1 / 30 Days\n\n"
    "Payment করার নিয়ম:\n"
    "1. আপনার নির্ধারিত payment method-এ $1 পাঠান।\n"
    "2. Payment-এর Transaction ID/Proof পাঠান।\n"
    "3. Admin verification-এর পর Premium active হবে।\n\n"
    "⚠️ PAYMENT DETAILS: এখানে আপনার আসল payment address/method বসান।"
)

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
DB = "bot_db.json"
states = {}


# ==================== ২. ডাটাবেস ====================
def load_db():
    if not os.path.exists(DB):
        data = {
            "users": {},
            "tasks": [],
            "t_cnt": 1,
            "p_cnt": 1
        }
        with open(DB, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    with open(DB, "r", encoding="utf-8") as f:
        db = json.load(f)

    # পুরোনো database থাকলেও নতুন fields তৈরি হবে
    db.setdefault("users", {})
    db.setdefault("tasks", [])
    db.setdefault("t_cnt", 1)
    db.setdefault("p_cnt", 1)
    return db


def save_db(data):
    with open(DB, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def get_user(db, uid):
    uid = str(uid)

    if uid not in db["users"]:
        db["users"][uid] = {
            "bal": 0.0,
            "dep": 0.0,
            "earn": 0.0,
            "refs": 0,
            "ads": 0,
            "date": "",
            "done": [],
            "premium": False,
            "premium_until": "",
            "premium_pending": False,
            "ad_reset_at": ""
        }
        save_db(db)
    else:
        # পুরোনো user account-এর missing fields ঠিক করা
        u = db["users"][uid]
        u.setdefault("bal", 0.0)
        u.setdefault("dep", 0.0)
        u.setdefault("earn", 0.0)
        u.setdefault("refs", 0)
        u.setdefault("ads", 0)
        u.setdefault("date", "")
        u.setdefault("done", [])
        u.setdefault("premium", False)
        u.setdefault("premium_until", "")
        u.setdefault("premium_pending", False)
        u.setdefault("ad_reset_at", "")

    return db["users"][uid]


def is_premium(u):
    if not u.get("premium", False):
        return False

    until = u.get("premium_until", "")
    if not until:
        return False

    try:
        expiry = datetime.datetime.strptime(until, "%Y-%m-%d").date()
        if datetime.date.today() <= expiry:
            return True

        # Expired হলে automatically off
        u["premium"] = False
        return False
    except:
        return False


def premium_days_left(u):
    if not is_premium(u):
        return 0

    expiry = datetime.datetime.strptime(
        u["premium_until"], "%Y-%m-%d"
    ).date()

    return max(0, (expiry - datetime.date.today()).days)


def check_join(uid):
    for ch in CHANNELS:
        try:
            status = bot.get_chat_member(ch, uid).status
            if status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True


def main_kb(uid):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    kb.add(
        "🛠️ কাজ করুন",
        "📺 Watch Ad",
        "📢 প্রমোট করুন",
        "👤 প্রোফাইল",
        "🔗 Refer & Earn",
        "⭐ Premium",
        "📥 ডিপোজিট",
        "🏧 টাকা তুলুন"
    )

    if uid == ADMIN_ID:
        kb.add("👨‍✈️ Admin Panel")

    return kb


# ==================== ৩. START ====================
@bot.message_handler(commands=["start"])
def start(m):
    uid = m.from_user.id

    if not check_join(uid):
        kb = types.InlineKeyboardMarkup()
        kb.add(
            types.InlineKeyboardButton(
                "📢 Join Channel",
                url="https://t.me/workivax_payment_proof"
            )
        )
        kb.add(
            types.InlineKeyboardButton(
                "💬 Join Support",
                url="https://t.me/WorkivaX_Support"
            )
        )
        kb.add(
            types.InlineKeyboardButton(
                "✅ Joined / Check",
                callback_data="chk"
            )
        )

        return bot.send_message(
            uid,
            "⚠️ বট ব্যবহার করতে আগে বাধ্যতামূলক Channel ও Support-এ Join করুন:",
            reply_markup=kb
        )

    db = load_db()
    args = m.text.split()

    # Referral
    if len(args) > 1 and args[1].isdigit():
        rid = int(args[1])

        if rid != uid and str(rid) in db["users"]:
            new_user = get_user(db, uid)
            r_user = get_user(db, rid)

            # একই user যেন বারবার referral bonus না দিতে পারে
            if new_user.get("referred_by") is None:
                new_user["referred_by"] = rid
                r_user["bal"] += REFERRAL_REWARD
                r_user["earn"] += REFERRAL_REWARD
                r_user["refs"] += 1

                save_db(db)

                try:
                    bot.send_message(
                        rid,
                        f"🎉 নতুন Referral!\n"
                        f"💰 Referral Bonus: ৳{REFERRAL_REWARD:.2f}"
                    )
                except:
                    pass

                try:
                    bot.send_message(
                        ADMIN_ID,
                        f"👥 <b>নতুন Referral</b>\n"
                        f"🆔 New User: <code>{uid}</code>\n"
                        f"🎯 Referrer: <code>{rid}</code>"
                    )
                except:
                    pass

    bot.send_message(
        uid,
        f"👋 স্বাগতম {m.from_user.first_name}!",
        reply_markup=main_kb(uid)
    )


# ==================== ৪. CALLBACKS ====================
@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    uid = c.from_user.id

    # Channel check
    if c.data == "chk":
        if check_join(uid):
            bot.answer_callback_query(
                c.id,
                "✅ Access confirmed!",
                show_alert=True
            )

            try:
                bot.delete_message(uid, c.message.message_id)
            except:
                pass

            bot.send_message(
                uid,
                "মূল মেনু:",
                reply_markup=main_kb(uid)
            )
        else:
            bot.answer_callback_query(
                c.id,
                "❌ আপনি এখনো সবগুলোতে Join করেননি!",
                show_alert=True
            )
        return

    # Watch Ad claim
    if c.data == "vad":
        db = load_db()
        u = get_user(db, uid)

        # Free user: 24 hours = 5 Ads
        # Premium user: 24 hours = 20 Ads
        limit = PREMIUM_DAILY_AD_LIMIT if is_premium(u) else FREE_DAILY_AD_LIMIT

        now = datetime.datetime.now()
        reset_at = u.get("ad_reset_at", "")

        # প্রথমবার বা আগের 24-hour window শেষ হলে counter reset
        if not reset_at:
            u["ad_reset_at"] = now.isoformat()
            u["ads"] = 0
        else:
            try:
                reset_time = datetime.datetime.fromisoformat(reset_at)
                if now - reset_time >= datetime.timedelta(hours=24):
                    u["ad_reset_at"] = now.isoformat()
                    u["ads"] = 0
            except:
                u["ad_reset_at"] = now.isoformat()
                u["ads"] = 0

        if u.get("ads", 0) >= limit:
            try:
                reset_time = datetime.datetime.fromisoformat(u["ad_reset_at"])
                remaining = datetime.timedelta(hours=24) - (now - reset_time)
                hours = max(0, int(remaining.total_seconds() // 3600))
                minutes = max(0, int((remaining.total_seconds() % 3600) // 60))
                wait_text = f"{hours} ঘণ্টা {minutes} মিনিট"
            except:
                wait_text = "২৪ ঘণ্টা"

            return bot.answer_callback_query(
                c.id,
                f"⚠️ আপনার {limit}টি Ad-এর limit শেষ। আবার Ad দেখতে {wait_text} অপেক্ষা করুন।",
                show_alert=True
            )

        u["bal"] += AD_REWARD
        u["earn"] += AD_REWARD
        u["ads"] += 1

        save_db(db)

        remaining_ads = limit - u["ads"]

        bot.answer_callback_query(
            c.id,
            f"✅ ৳{AD_REWARD:.2f} যোগ হয়েছে! আজ/এই ২৪ ঘণ্টার window-এ আরও {remaining_ads}টি Ad বাকি।",
            show_alert=True
        )

        try:
            bot.delete_message(uid, c.message.message_id)
        except:
            pass

        return

    # Premium payment request approve/reject
    if c.data.startswith("premapp_") or c.data.startswith("premrej_"):
        if uid != ADMIN_ID:
            return

        action, target_uid = c.data.split("_")
        target_uid = int(target_uid)

        db = load_db()
        u = get_user(db, target_uid)

        if action == "premapp":
            start_date = datetime.date.today()
            expiry = start_date + datetime.timedelta(days=PREMIUM_DAYS)

            u["premium"] = True
            u["premium_until"] = str(expiry)
            u["premium_pending"] = False

            save_db(db)

            bot.send_message(
                target_uid,
                f"🎉 <b>Premium Activated!</b>\n\n"
                f"⭐ Premium: Active\n"
                f"📅 Valid Until: {expiry}\n"
                f"⏳ Duration: {PREMIUM_DAYS} Days\n\n"
                f"💰 এখন Premium Tasks ব্যবহার করতে পারবেন।"
            )

            bot.answer_callback_query(
                c.id,
                "✅ Premium approved!",
                show_alert=True
            )

        else:
            u["premium_pending"] = False
            save_db(db)

            bot.send_message(
                target_uid,
                "❌ আপনার Premium payment verification করা যায়নি। "
                "সঠিক payment proof দিয়ে আবার চেষ্টা করুন।"
            )

            bot.answer_callback_query(
                c.id,
                "❌ Premium rejected!",
                show_alert=True
            )

        try:
            bot.edit_message_reply_markup(
                ADMIN_ID,
                c.message.message_id,
                reply_markup=None
            )
        except:
            pass

        return

    # Premium payment proof submission
    if c.data == "premium_proof":
        states[uid] = {"act": "premium_proof"}
        bot.send_message(
            uid,
            "📸 আপনার $1 payment-এর Transaction ID অথবা Screenshot পাঠান:"
        )
        return

    # Task proof
    if c.data.startswith("vt_"):
        tid = int(c.data.split("_")[1])

        db = load_db()
        u = get_user(db, uid)

        t = next(
            (x for x in db["tasks"] if x["id"] == tid),
            None
        )

        if not t or tid in u["done"]:
            return bot.answer_callback_query(
                c.id,
                "❌ কাজটি আর উপলব্ধ নেই!",
                show_alert=True
            )

        # Premium task হলে premium check
        if t.get("premium", False) and not is_premium(u):
            return bot.answer_callback_query(
                c.id,
                "⭐ এই কাজটি শুধু Premium Members-এর জন্য।",
                show_alert=True
            )

        states[uid] = {
            "act": "sp",
            "tid": tid
        }

        bot.send_message(
            uid,
            "📸 প্রমাণ হিসেবে Screenshot বা প্রয়োজনীয় তথ্য পাঠান:"
        )
        return

    # Admin approve/reject task proof
    if c.data.startswith("app_") or c.data.startswith("rej_"):
        if uid != ADMIN_ID:
            return

        act, pid, wid, tid = c.data.split("_")

        db = load_db()
        w = get_user(db, wid)

        t = next(
            (x for x in db["tasks"] if x["id"] == int(tid)),
            None
        )

        if act == "app" and t:
            w["bal"] += t["reward"]
            w["earn"] += t["reward"]

            t["done"] = t.get("done", 0) + 1

            if t["done"] >= t["qty"]:
                t["status"] = "done"

            save_db(db)

            bot.send_message(
                int(wid),
                f"🎉 আপনার Task Proof (#{tid}) approved!\n"
                f"💰 ৳{t['reward']:.2f} balance-এ যোগ হয়েছে।"
            )
        else:
            bot.send_message(
                int(wid),
                f"❌ আপনার Task Proof (#{tid}) rejected হয়েছে।"
            )

        try:
            bot.edit_message_reply_markup(
                ADMIN_ID,
                c.message.message_id,
                reply_markup=None
            )
        except:
            pass

        return

    # Task creation
    if c.data.startswith("tp_"):
        task_type = c.data.split("_", 1)[1]

        states[uid] = {
            "act": "ctitle",
            "type": task_type
        }

        bot.send_message(
            uid,
            "📌 Task-এর title দিন:"
        )
        return

    # Withdraw method
    if c.data.startswith("w_"):
        method = c.data.split("_", 1)[1]

        states[uid] = {
            "act": "wamt",
            "meth": method
        }

        bot.send_message(
            uid,
            f"📱 আপনার {method} number এবং amount লিখুন\n"
            f"(উদাহরণ: 01700000000 50)"
        )
        return


# ==================== ৫. TEXT / PHOTO ====================
@bot.message_handler(content_types=["text", "photo"])
def msg(m):
    uid = m.from_user.id

    if not check_join(uid):
        return

    txt = m.text or ""
    db = load_db()
    u = get_user(db, uid)
    st = states.get(uid, {})

    # Premium payment proof
    if st.get("act") == "premium_proof":
        states.pop(uid, None)

        u["premium_pending"] = True
        save_db(db)

        proof_text = txt if txt else "📸 Screenshot attached"

        kb = types.InlineKeyboardMarkup()
        kb.add(
            types.InlineKeyboardButton(
                "✅ Approve Premium",
                callback_data=f"premapp_{uid}"
            ),
            types.InlineKeyboardButton(
                "❌ Reject",
                callback_data=f"premrej_{uid}"
            )
        )

        caption = (
            "⭐ <b>Premium Payment Request</b>\n\n"
            f"👤 User ID: <code>{uid}</code>\n"
            f"💵 Amount: ${PREMIUM_PRICE_USD:.2f}\n"
            f"📅 Duration: {PREMIUM_DAYS} Days\n"
            f"📝 Proof: {proof_text}"
        )

        if m.photo:
            bot.send_photo(
                ADMIN_ID,
                m.photo[-1].file_id,
                caption=caption,
                reply_markup=kb
            )
        else:
            bot.send_message(
                ADMIN_ID,
                caption,
                reply_markup=kb
            )

        bot.send_message(
            uid,
            "✅ আপনার Premium payment proof জমা হয়েছে। "
            "Admin verification-এর পর Premium active হবে।"
        )
        return

    # Task proof
    if st.get("act") == "sp" and (txt or m.photo):
        states.pop(uid, None)

        tid = st["tid"]

        t = next(
            (x for x in db["tasks"] if x["id"] == tid),
            None
        )

        if not t:
            return

        if t.get("premium", False) and not is_premium(u):
            return bot.send_message(
                uid,
                "⭐ এই কাজটি Premium Members-এর জন্য।"
            )

        u["done"].append(tid)

        pid = db["p_cnt"]
        db["p_cnt"] += 1

        save_db(db)

        kb = types.InlineKeyboardMarkup()

        kb.add(
            types.InlineKeyboardButton(
                "✅ Approve",
                callback_data=f"app_{pid}_{uid}_{tid}"
            ),
            types.InlineKeyboardButton(
                "❌ Reject",
                callback_data=f"rej_{pid}_{uid}_{tid}"
            )
        )

        c_msg = (
            f"📩 <b>নতুন Task Proof</b>\n"
            f"👤 User ID: <code>{uid}</code>\n"
            f"📌 Task: #{tid} ({t['title']})\n"
            f"💰 Reward: ৳{t['reward']:.2f}"
        )

        if m.photo:
            bot.send_photo(
                ADMIN_ID,
                m.photo[-1].file_id,
                caption=c_msg,
                reply_markup=kb
            )
        else:
            bot.send_message(
                ADMIN_ID,
                c_msg + f"\n📝 Text: {txt}",
                reply_markup=kb
            )

        bot.send_message(
            uid,
            "✅ আপনার proof জমা হয়েছে। Admin verification-এর পর balance যোগ হবে।"
        )
        return

    # Create task - title
    if st.get("act") == "ctitle":
        states[uid]["title"] = txt
        states[uid]["act"] = "clink"

        bot.send_message(
            uid,
            "🔗 Task-এর link দিন:"
        )
        return

    # Create task - link
    if st.get("act") == "clink":
        states[uid]["link"] = txt
        states[uid]["act"] = "creward"

        bot.send_message(
            uid,
            "💰 প্রতি task-এর জন্য worker-কে কত টাকা দেবেন? (যেমন: 5)"
        )
        return

    # Create task - reward
    if st.get("act") == "creward":
        try:
            rew = float(txt)

            if rew <= 0:
                raise Exception

            states[uid]["rew"] = rew
            states[uid]["act"] = "cqty"

            bot.send_message(
                uid,
                "👥 কতজন worker প্রয়োজন তা লিখুন:"
            )

        except:
            bot.send_message(
                uid,
                "❌ সঠিক amount লিখুন!"
            )
        return

    # Create task - quantity
    if st.get("act") == "cqty":
        try:
            qty = int(txt)

            if qty <= 0:
                raise Exception

            data = states.pop(uid)

            cost = data["rew"] * qty

            if u["dep"] < cost:
                return bot.send_message(
                    uid,
                    f"❌ পর্যাপ্ত deposit নেই!\n"
                    f"প্রয়োজন: ৳{cost:.2f}\n"
                    f"আছে: ৳{u['dep']:.2f}"
                )

            u["dep"] -= cost

            # Telegram Join task = Premium task
            premium_task = (
                data["type"].lower() in [
                    "telegram",
                    "telegram_join",
                    "premium"
                ]
            )

            t = {
                "id": db["t_cnt"],
                "type": data["type"],
                "title": data["title"],
                "link": data["link"],
                "reward": data["rew"],
                "qty": qty,
                "done": 0,
                "status": "active",
                "premium": premium_task
            }

            db["t_cnt"] += 1
            db["tasks"].append(t)

            save_db(db)

            tag = "⭐ Premium" if premium_task else "🆓 Standard"

            bot.send_message(
                uid,
                f"🎉 Task successfully live!\n"
                f"{tag}\n"
                f"💰 Total cost: ৳{cost:.2f}"
            )

        except:
            bot.send_message(
                uid,
                "❌ সঠিক পূর্ণসংখ্যা লিখুন!"
            )
        return

    # Withdraw
    if st.get("act") == "wamt":
        method = st["meth"]
        states.pop(uid, None)

        try:
            parts = txt.split()

            if len(parts) != 2:
                raise Exception

            num = parts[0]
            amt = float(parts[1])

            if amt < MIN_W or amt > u["bal"]:
                return bot.send_message(
                    uid,
                    f"❌ Minimum withdrawal ৳{MIN_W:.2f} "
                    f"এবং আপনার balance ৳{u['bal']:.2f}"
                )

            u["bal"] -= amt
            save_db(db)

            bot.send_message(
                uid,
                "✅ আপনার withdrawal request জমা হয়েছে!"
            )

            bot.send_message(
                ADMIN_ID,
                f"🔔 <b>New Withdrawal</b>\n"
                f"👤 User: <code>{uid}</code>\n"
                f"💳 Method: {method}\n"
                f"📱 Number: <code>{num}</code>\n"
                f"💵 Amount: ৳{amt:.2f}"
            )

        except:
            bot.send_message(
                uid,
                "❌ Format ভুল!\n"
                "উদাহরণ: 01700000000 50"
            )
        return

    # Profile
    if txt == "👤 প্রোফাইল":
        premium_status = (
            f"⭐ Premium: Active\n"
            f"📅 Valid Until: {u.get('premium_until', '')}\n"
            f"⏳ Days Left: {premium_days_left(u)}"
            if is_premium(u)
            else "⭐ Premium: Inactive"
        )

        bot.send_message(
            uid,
            f"👤 <b>আপনার প্রোফাইল</b>\n\n"
            f"🆔 ID: <code>{uid}</code>\n"
            f"💵 Earnings Balance: ৳{u['bal']:.2f}\n"
            f"💳 Deposit Balance: ৳{u['dep']:.2f}\n"
            f"👥 Referrals: {u['refs']} জন\n\n"
            f"{premium_status}"
        )
        return

    # Watch Ad
    if txt == "📺 Watch Ad":
        kb = types.InlineKeyboardMarkup()

        kb.add(
            types.InlineKeyboardButton(
                "🔗 Open Ad",
                url=ADSTERRA
            )
        )

        kb.add(
            types.InlineKeyboardButton(
                f"🎁 Claim ৳{AD_REWARD:.2f}",
                callback_data="vad"
            )
        )

        bot.send_message(
            uid,
            f"📺 Ad দেখুন এবং claim করুন।\n"
            f"💰 প্রতি Ad: ৳{AD_REWARD:.2f}\n"
            f"⏰ Free: {FREE_DAILY_AD_LIMIT} Ads / 24h\n⭐ Premium: {PREMIUM_DAILY_AD_LIMIT} Ads / 24h",
            reply_markup=kb
        )
        return

    # Premium
    if txt == "⭐ Premium":
        if is_premium(u):
            bot.send_message(
                uid,
                f"⭐ <b>Premium Active</b>\n\n"
                f"📅 Valid Until: {u['premium_until']}\n"
                f"⏳ Days Left: {premium_days_left(u)}\n\n"
                f"💰 Premium Telegram Join Tasks: প্রতি Join-এ ৳{PREMIUM_JOIN_REWARD:.2f}"
            )
            return

        if u.get("premium_pending", False):
            bot.send_message(
                uid,
                "⏳ আপনার Premium payment verification pending আছে।"
            )
            return

        kb = types.InlineKeyboardMarkup()

        kb.add(
            types.InlineKeyboardButton(
                "💳 Pay $1 & Activate",
                callback_data="premium_proof"
            )
        )

        bot.send_message(
            uid,
            f"⭐ <b>WorkivaX Premium</b>\n\n"
            f"💵 Price: ${PREMIUM_PRICE_USD:.2f}\n"
            f"📅 Duration: {PREMIUM_DAYS} Days\n\n"
            f"Premium Members পাবেন:\n"
            f"📲 Telegram Join Tasks\n"
            f"💰 প্রতি Join-এ ৳{PREMIUM_JOIN_REWARD:.2f}\n"
            f"🎯 Additional Premium Tasks & Rewards\n\n"
            f"{PREMIUM_PAYMENT_INFO}",
            reply_markup=kb
        )
        return

    # Work / tasks
    if txt == "🛠️ কাজ করুন":
        acts = []

        for x in db["tasks"]:
            if (
                x["status"] == "active"
                and x["done"] < x["qty"]
                and x["id"] not in u["done"]
            ):
                if x.get("premium", False):
                    if is_premium(u):
                        acts.append(x)
                else:
                    acts.append(x)

        if not acts:
            return bot.send_message(
                uid,
                "❌ এই মুহূর্তে আপনার জন্য কোনো কাজ উপলব্ধ নেই।"
            )

        kb = types.InlineKeyboardMarkup()

        for x in acts:
            label = (
                "⭐ "
                if x.get("premium", False)
                else ""
            )

            kb.add(
                types.InlineKeyboardButton(
                    f"{label}[{x['type']}] {x['title']} "
                    f"(৳{x['reward']:.2f})",
                    callback_data=f"vt_{x['id']}"
                )
            )

        bot.send_message(
            uid,
            "📋 আপনার জন্য available tasks:",
            reply_markup=kb
        )
        return

    # Promote
    if txt == "📢 প্রমোট করুন":
        if u["dep"] < 1.0:
            return bot.send_message(
                uid,
                f"❌ পর্যাপ্ত deposit balance নেই!\n"
                f"বর্তমান: ৳{u['dep']:.2f}"
        )

        kb = types.InlineKeyboardMarkup(row_width=2)

        kb.add(
            types.InlineKeyboardButton(
                "YouTube",
                callback_data="tp_YouTube"
            ),
            types.InlineKeyboardButton(
                "TikTok",
                callback_data="tp_TikTok"
            ),
            types.InlineKeyboardButton(
                "Facebook",
                callback_data="tp_Facebook"
            ),
            types.InlineKeyboardButton(
                "Telegram Join",
                callback_data="tp_Telegram"
            ),
            types.InlineKeyboardButton(
                "Custom",
                callback_data="tp_Custom"
            )
        )

        bot.send_message(
            uid,
            "📢 Task category বেছে নিন:",
            reply_markup=kb
        )
        return

    # Referral
    if txt == "🔗 Refer & Earn":
        bot_un = bot.get_me().username

        bot.send_message(
            uid,
            f"🔗 <b>আপনার Referral Link:</b>\n"
            f"<code>https://t.me/{bot_un}?start={uid}</code>\n\n"
            f"🎁 প্রতি successful referral-এ ৳{REFERRAL_REWARD:.2f} bonus!"
        )
        return

    # Deposit
    if txt == "📥 ডিপোজিট":
        bot.send_message(
            uid,
            "📥 <b>ডিপোজিট করার নিয়ম:</b>\n\n"
            "বিকাশ/নগদ (Personal): <code>01700000000</code>\n\n"
            "টাকা পাঠানোর পর Transaction ID এবং আপনার User ID "
            "Admin/Support-এ দিন: @WorkivaX_Support"
        )
        return

    # Withdraw
    if txt == "🏧 টাকা তুলুন":
        if u["bal"] < MIN_W:
            return bot.send_message(
                uid,
                f"⚠️ Minimum withdrawal ৳{MIN_W:.2f}\n"
                f"আপনার balance: ৳{u['bal']:.2f}"
            )

        kb = types.InlineKeyboardMarkup()

        kb.add(
            types.InlineKeyboardButton(
                "bKash",
                callback_data="w_bKash"
            ),
            types.InlineKeyboardButton(
                "Nagad",
                callback_data="w_Nagad"
            )
        )

        bot.send_message(
            uid,
            "পেমেন্ট method select করুন:",
            reply_markup=kb
        )
        return

    # Admin panel
    if txt == "👨‍✈️ Admin Panel" and uid == ADMIN_ID:
        bot.send_message(
            uid,
            "👨‍✈️ <b>Admin Panel</b>\n\n"
            "Deposit দিতে:\n"
            "<code>/addbalance USER_ID AMOUNT</code>\n\n"
            "Premium manually দিতে:\n"
            "<code>/addpremium USER_ID DAYS</code>\n\n"
            "Premium remove করতে:\n"
            "<code>/removepremium USER_ID</code>"
        )
        return


# ==================== ৬. ADMIN COMMANDS ====================
@bot.message_handler(commands=["addbalance"])
def addbal(m):
    if m.from_user.id != ADMIN_ID:
        return

    try:
        _, tuid, amt = m.text.split()

        db = load_db()
        u = get_user(db, tuid)

        amount = float(amt)

        if amount <= 0:
            raise Exception

        u["dep"] += amount

        save_db(db)

        bot.send_message(
            m.chat.id,
            f"✅ User {tuid}-কে ৳{amount:.2f} deposit দেওয়া হয়েছে।"
        )

        bot.send_message(
            int(tuid),
            f"🎉 আপনার account-এ ৳{amount:.2f} deposit balance যুক্ত হয়েছে!"
        )

    except:
        bot.send_message(
            m.chat.id,
            "❌ Format:\n/addbalance USER_ID AMOUNT"
        )


@bot.message_handler(commands=["addpremium"])
def addpremium(m):
    if m.from_user.id != ADMIN_ID:
        return

    try:
        _, tuid, days = m.text.split()

        tuid = int(tuid)
        days = int(days)

        if days <= 0:
            raise Exception

        db = load_db()
        u = get_user(db, tuid)

        expiry = datetime.date.today() + datetime.timedelta(days=days)

        u["premium"] = True
        u["premium_until"] = str(expiry)
        u["premium_pending"] = False

        save_db(db)

        bot.send_message(
            m.chat.id,
            f"✅ User {tuid}-এর Premium {days} দিনের জন্য active করা হয়েছে।"
        )

        bot.send_message(
            tuid,
            f"🎉 <b>Premium Activated!</b>\n\n"
            f"📅 Valid Until: {expiry}\n"
            f"⏳ Duration: {days} Days"
        )

    except:
        bot.send_message(
            m.chat.id,
            "❌ Format:\n/addpremium USER_ID DAYS"
        )


@bot.message_handler(commands=["removepremium"])
def removepremium(m):
    if m.from_user.id != ADMIN_ID:
        return

    try:
        _, tuid = m.text.split()

        db = load_db()
        u = get_user(db, tuid)

        u["premium"] = False
        u["premium_until"] = ""
        u["premium_pending"] = False

        save_db(db)

        bot.send_message(
            m.chat.id,
            f"✅ User {tuid}-এর Premium removed."
        )

        bot.send_message(
            int(tuid),
            "⚠️ আপনার Premium Membership deactivated করা হয়েছে।"
        )

    except:
        bot.send_message(
            m.chat.id,
            "❌ Format:\n/removepremium USER_ID"
        )


# ==================== ৭. BOT LOOP ====================
print("WorkivaX Bot is running smoothly...")

while True:
    try:
        bot.infinity_polling(
            timeout=60,
            long_polling_timeout=60
        )

    except Exception as e:
        print(
            f"Network Connection Error: {e}. "
            f"Reconnecting in 5 seconds..."
        )
        time.sleep(5)
