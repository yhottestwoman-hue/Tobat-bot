import os
import json
import csv
import io
from datetime import datetime
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATA_FILE = "bbc_data.json"

# Load data
def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

data = load_data()

# Auto hitung semua chat
async def count_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or update.effective_user.is_bot:
        return
    if not update.effective_message or update.effective_message.text and update.effective_message.text.startswith("/"):
        return
    
    user_id = str(update.effective_user.id)
    name = update.effective_user.full_name
    username = update.effective_user.username or "-"

    if user_id not in data:
        data[user_id] = {"name": name, "username": username, "bbc": 0, "last": str(datetime.now())}
    
    data[user_id]["bbc"] += 1
    data[user_id]["name"] = name
    data[user_id]["username"] = username
    data[user_id]["last"] = str(datetime.now())
    save_data(data)

# /bbc cek satu orang
async def bbc_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply chat orang yang mau di cek BBC nya dengan /bbc")
        return
    uid = str(update.message.reply_to_message.from_user.id)
    info = data.get(uid, {"bbc": 0})
    await update.message.reply_text(f"{info.get('name')} : {info.get('bbc')} BBC")

# /daftarin buat yang silent
async def daftarin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply orang yang mau di daftarin dengan /daftarin")
        return
    user = update.message.reply_to_message.from_user
    uid = str(user.id)
    if uid not in data:
        data[uid] = {"name": user.full_name, "username": user.username or "-", "bbc": 0, "last": str(datetime.now())}
        save_data(data)
    await update.message.reply_text(f"{user.full_name} sudah di daftarin (BBC: {data[uid]['bbc']})")

def make_list(min_bbc, max_bbc=None):
    result = []
    for uid, info in data.items():
        bbc = info["bbc"]
        if max_bbc is None:
            if bbc >= min_bbc:
                result.append(info)
        else:
            if min_bbc <= bbc <= max_bbc:
                result.append(info)
    # sort tertinggi dulu
    result.sort(key=lambda x: x["bbc"], reverse=True)
    return result

async def list500(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lst = make_list(500)
    if not lst:
        await update.message.reply_text("Belum ada yang 500+")
        return
    text = f"LIST 500+ ({len(lst)} orang) - AKTIF ✅\n\n"
    for i, u in enumerate(lst, 1):
        text += f"{i}. {u['name']} (@{u['username']}) - {u['bbc']} BBC\n"
    # telegram limit 4096
    for chunk in [text[i:i+4000] for i in range(0, len(text), 4000)]:
        await update.message.reply_text(chunk)

async def list300(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lst = make_list(300, 499)
    if not lst:
        await update.message.reply_text("Belum ada yang 300-499")
        return
    text = f"LIST 300-499 ({len(lst)} orang) - DIPANTAU ⚠️\n\n"
    for i, u in enumerate(lst, 1):
        text += f"{i}. {u['name']} (@{u['username']}) - {u['bbc']} BBC\n"
    for chunk in [text[i:i+4000] for i in range(0, len(text), 4000)]:
        await update.message.reply_text(chunk)

async def listlow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lst = make_list(0, 299)
    if not lst:
        await update.message.reply_text("Belum ada yang <300")
        return
    text = f"LIST <300 ({len(lst)} orang) - MAU DI KICK ❌\n\n"
    for i, u in enumerate(lst, 1):
        text += f"{i}. {u['name']} (@{u['username']}) - {u['bbc']} BBC\n"
    for chunk in [text[i:i+4000] for i in range(0, len(text), 4000)]:
        await update.message.reply_text(chunk)

async def export_csv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Name", "Username", "UserID", "BBC", "Last Active"])
    for uid, info in data.items():
        writer.writerow([info["name"], info["username"], uid, info["bbc"], info["last"]])
    
    output.seek(0)
    bio = io.BytesIO(output.getvalue().encode())
    await update.message.reply_document(document=bio, filename=f"tobat_bbc_{datetime.now().date()}.csv", caption=f"Total {len(data)} member terdata")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, count_message))
    app.add_handler(CommandHandler("bbc", bbc_check))
    app.add_handler(CommandHandler("daftarin", daftarin))
    app.add_handler(CommandHandler("list500", list500))
    app.add_handler(CommandHandler("list300", list300))
    app.add_handler(CommandHandler("listlow", listlow))
    app.add_handler(CommandHandler("list", list500))
    app.add_handler(CommandHandler("export", export_csv))
    print("BOT LIST BBC RUNNING - auto hitung")
    app.run_polling()

if __name__ == "__main__":
    main()
