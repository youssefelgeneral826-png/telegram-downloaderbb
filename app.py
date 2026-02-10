import os
import asyncio
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import yt_dlp
import google.generativeai as genai

# --- إعدادات الجنرال يوسف ---
API_ID = 34535400
API_HASH = "dd2b7bae83993de09be6ad6c7e013417"
BOT_TOKEN = "8502451154:AAEpLOZ51mmAoJCkJN29vp5vXwN5a6HVv0k"
GENAI_API_KEY = "AIzaSyCLheYFWE9YLsc5sGSQuI7xhuZvG6ZuGjI"

genai.configure(api_key=GENAI_API_KEY)
ai_model = genai.GenerativeModel('gemini-pro')

app = Client("GeneralBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

def download_media(url, mode, user_id):
    file_name = f"dl_{user_id}_{os.urandom(3).hex()}"
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best' if mode == 'video' else 'bestaudio/best',
        'outtmpl': f'{file_name}.%(ext)s',
        'merge_output_format': 'mp4' if mode == 'video' else None,
        'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3'}] if mode == 'audio' else [],
        'quiet': True,
        'nocheckcertificate': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info), info.get('title', 'Media')

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("👑 **مرحباً بك في بوت الجنرال يوسف!**\n\nأرسل رابطاً للتحميل أو اسأل جيمني أي سؤال.")

@app.on_message(filters.text & ~filters.command(["start"]))
async def handle_msg(client, message):
    if "http" in message.text:
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("🎬 فيديو MP4", callback_data=f"v|{message.text}"),
            InlineKeyboardButton("🎵 صوت MP3", callback_data=f"a|{message.text}")
        ]])
        await message.reply_text("✅ اختر الصيغة:", reply_markup=keyboard)
    else:
        try:
            response = ai_model.generate_content(message.text)
            await message.reply_text(f"🤖 **Gemini:**\n\n{response.text}")
        except:
            await message.reply_text("⚠️ جيمني مشغول.")

@app.on_callback_query()
async def callback(client, query: CallbackQuery):
    data = query.data.split("|")
    mode, url = ('video' if data[0] == 'v' else 'audio'), data[1]
    await query.message.edit(f"📥 جاري التحميل...")
    try:
        loop = asyncio.get_event_loop()
        file_path, title = await loop.run_in_executor(None, download_media, url, mode, query.from_user.id)
        if mode == 'video':
            await query.message.reply_video(video=file_path, caption=f"🎬 {title}")
        else:
            await query.message.reply_audio(audio=file_path, caption=f"🎵 {title}")
        if os.path.exists(file_path): os.remove(file_path)
        await query.message.delete()
    except Exception as e:
        await query.message.reply_text(f"❌ خطأ: {str(e)}")

app.run()
