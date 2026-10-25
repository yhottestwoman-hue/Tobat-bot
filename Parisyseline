from __future__ import annotations
import asyncio
import io
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo
import arabic_reshaper
import requests
from PIL import Image, ImageDraw, ImageFont, ImageOps
from bidi.algorithm import get_display
from telegram import InputFile, Update, User
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

CARD_WIDTH = 1000
CARD_HEIGHT = 620
BLACK = (18, 18, 18)
GOLD = (233, 220, 197)
GOLD_LINE = (210, 180, 120)
MAX_PROFILE_IMAGE_BYTES = 10 * 1024 * 1024
logger = logging.getLogger("tobat-member-card-bot")

def _font(size: int, *, bold: bool = False, mono: bool = False):
    try:
        if bold:
            return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size=size)
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size=size)
    except: return ImageFont.load_default()

def _clean_text(value, fallback=""):
    cleaned = "".join(c for c in (value or "") if c.isprintable())
    return re.sub(r"\s+", " ", cleaned).strip() or fallback

def _shape_mixed_text(text: str) -> str:
    try: return get_display(arabic_reshaper.reshape(text), base_dir="L")
    except: return text

def _fit_font(draw, text, max_width, starting_size, *, bold=False, mono=False, minimum_size=13):
    size = starting_size
    font = _font(size, bold=bold, mono=mono)
    while size > minimum_size:
        if draw.textbbox((0, 0), text, font=font)[2] <= max_width: break
        size -= 1
        font = _font(size, bold=bold, mono=mono)
    return font

def _textured_background(side: str):
    # Fixed: solid background, no assets needed
    return Image.new("RGB", (CARD_WIDTH, CARD_HEIGHT), BLACK)

def _draw_card_frame(draw):
    draw.rounded_rectangle((10, 10, CARD_WIDTH - 10, CARD_HEIGHT - 10), radius=20, outline=GOLD_LINE, width=2)
    draw.rounded_rectangle((30, 30, CARD_WIDTH - 30, CARD_HEIGHT - 30), radius=15, outline=GOLD_LINE, width=1)

def _draw_centered_text(draw, text, y, font, *, fill=GOLD, max_width=860):
    font = _fit_font(draw, text, max_width, getattr(font, "size", 18), bold=False, minimum_size=12)
    bounds = draw.textbbox((0, 0), text, font=font)
    x = (CARD_WIDTH - (bounds[2] - bounds[0])) / 2 - bounds[0]
    draw.text((x, y), text, fill=fill, font=font)

def _draw_dog_mark(draw, x, y):
    lines = (((x + 2, y + 18), (x + 10, y + 10), (x + 25, y + 11), (x + 33, y + 18)),((x + 25, y + 11), (x + 34, y + 6), (x + 43, y + 8), (x + 45, y + 14), (x + 39, y + 18), (x + 33, y + 18)),((x + 5, y + 15), (x + 1, y + 9)),((x + 12, y + 17), (x + 10, y + 27)),((x + 22, y + 17), (x + 24, y + 27)),((x + 33, y + 18), (x + 35, y + 27)),)
    for points in lines: draw.line(points, fill=GOLD, width=2, joint="curve")

def _profile_photo_layer(pfp_bytes, size):
    if not pfp_bytes: return None
    try:
        with Image.open(io.BytesIO(pfp_bytes)) as profile:
            photo = ImageOps.fit(profile.convert("RGB"), (size, size), method=Image.Resampling.LANCZOS, centering=(0.5, 0.45))
        mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, size - 1, size - 1), fill=255)
        photo.putalpha(mask)
        return photo
    except Exception: return None

def make_front_card(user, pfp_bytes=None):
    image = _textured_background("front")
    draw = ImageDraw.Draw(image)
    _draw_card_frame(draw)
    title = _shape_mixed_text("PARIS YSELINE - باريس يسلين")
    draw.text((80, 50), title, fill=GOLD, font=_fit_font(draw, title, 840, 28, bold=True))
    draw.text((80, 85), "T O N G K R O N G A N   B A D U T", fill=GOLD, font=_font(18))
    center_x, center_y, radius = 260, 320, 140
    draw.ellipse((center_x - radius, center_y - radius, center_x + radius, center_y + radius), outline=GOLD_LINE, width=2)
    photo_size = 240
    photo = _profile_photo_layer(pfp_bytes, photo_size)
    if photo is not None: image.paste(photo, (center_x - photo_size // 2, center_y - photo_size // 2), photo)
    clean_name = _clean_text(user.first_name, "Member")[:20]
    username = f"@{user.username}" if user.username else "No username"
    short_id = str(user.id)[-4:]
    malaysia_now = datetime.now(ZoneInfo("Asia/Kuala_Lumpur"))
    joined_at = malaysia_now.strftime("JOINED: %d %b %Y - %I:%M %p")
    data = ((f"NICKNAME: {clean_name}", 220),(f"USERNAME: {username}", 260),(f"ID: {short_id}", 300),(joined_at, 380),)
    for text, y in data: draw.text((480, y), text, fill=GOLD, font=_fit_font(draw, text, 450, 22, minimum_size=14))
    draw.line((80, 510, 920, 510), fill=GOLD_LINE, width=1)
    _draw_dog_mark(draw, 260, 535)
    footer = _shape_mixed_text("Welcome to TOBAT - مملكة الكلاب, The Hound's Domain")
    draw.text((325, 536), footer, fill=GOLD, font=_fit_font(draw, footer, 620, 16, minimum_size=11))
    return _to_png(image)

def make_back_card():
    image = _textured_background("back")
    draw = ImageDraw.Draw(image)
    _draw_card_frame(draw)
    _draw_centered_text(draw, _shape_mixed_text("PARIS YSELINE - باريس يسلين"), 50, _font(26, bold=True))
    _draw_centered_text(draw, "T O N G K R O N G A N   B A D U T", 85, _font(18))
    rules = ("• ONLY RP! skali lgi ONLY ERPE KAPE","• toxic use spoiler  • don't tmi","• rl things use @pbracket","• no agama things","• no cf exchange","• don't ignore each other","• mf : https://t.me/mfbadut2026","• ch : @IngfoTongkrongan",)
    for i, rule in enumerate(rules): _draw_centered_text(draw, rule, 180 + i * 30, _font(19), max_width=880)
    _draw_dog_mark(draw, 460, 497)
    _draw_centered_text(draw, "MEMBER CARD - Welcome to TOBAT", 540, _font(16), max_width=700)
    return _to_png(image)

def _to_png(image):
    output = io.BytesIO()
    image.save(output, format="PNG")
    output.seek(0)
    return output

def _download_profile_photo(file_url: str) -> bytes:
    chunks = []
    total_size = 0
    with requests.get(file_url, timeout=10, stream=True) as response:
        response.raise_for_status()
        for chunk in response.iter_content(chunk_size=64 * 1024):
            if not chunk: continue
            total_size += len(chunk)
            if total_size > MAX_PROFILE_IMAGE_BYTES: raise ValueError("Too big")
            chunks.append(chunk)
    return b"".join(chunks)

async def get_pfp(bot, user_id: int):
    try:
        photos = await bot.get_user_profile_photos(user_id=user_id, limit=1)
        if not photos.photos: return None
        largest_photo = photos.photos[0][-1]
        telegram_file = await bot.get_file(largest_photo.file_id)
        if not telegram_file.file_path: return None
        return await asyncio.to_thread(_download_profile_photo, telegram_file.file_path)
    except Exception: return None

async def send_member_card(user, chat_id, context, *, caption):
    pfp_bytes = await get_pfp(context.bot, user.id)
    card = make_front_card(user, pfp_bytes)
    await context.bot.send_photo(chat_id=chat_id, photo=InputFile(card, filename="tobat-member-card.png"), caption=caption)

async def welcome(update, context):
    message = update.effective_message
    if message is None: return
    rules_card = make_back_card().getvalue()
    for member in message.new_chat_members:
        if member.id == context.bot.id: continue
        await send_member_card(member, message.chat_id, context, caption=f"Welcome to TOBAT, {member.first_name}! 🖤\nFRONT - Profile Card")
        await context.bot.send_photo(chat_id=message.chat_id, photo=InputFile(io.BytesIO(rules_card), filename="tobat-rules-card.png"), caption="BEHIND - Rules Tongkrongan Badut")

async def card_command(update, context):
    user = update.effective_user
    message = update.effective_message
    if user is None or message is None: return
    pfp_bytes = await get_pfp(context.bot, user.id)
    card = make_front_card(user, pfp_bytes)
    await message.reply_photo(photo=InputFile(card, filename="tobat-member-card.png"), caption=f"Welcome, {user.first_name}\nID: {user.id}")

async def log_error(update, context):
    logger.error("Telegram update failed")

def main():
    token = os.getenv("BOT_TOKEN")
    if not token: raise RuntimeError("BOT_TOKEN is missing")
    logging.basicConfig(level=logging.INFO)
    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler(("card", "idcard", "member", "mycard", "start"), card_command))
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    application.add_error_handler(log_error)
    print("Bot running - TOBAT MEMBER CARD", flush=True)
    application.run_polling()

if __name__ == "__main__":
    main()
