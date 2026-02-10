import os
import asyncio
import time
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import yt_dlp
import google.generativeai as genai

# --- إعدادات الجنرال يوسف ---
API_ID = 34535400
API_HASH = "dd2b7bae83993de09be6ad6c7e013417"
BOT_TOKEN = "8502451154:AAEpLOZ51mmAoJCkJN29vp5vXwN5a6HVv0k"
GENAI_API_KEY = "AIzaSyCLheYFWE9YLsc5sGSQuI7xhuZvG6ZuGjI"
ADMIN_ID = 6886619057 # حط الأيدي بتاعك هنا عشان تشوف الإحصائيات
PASSWORD = "123" # كلمة المرور الموحدة للدخول (تقدر تغيرها)

genai.configure(api_key=GENAI_API_KEY)
ai_model = genai.GenerativeModel('gemini-pro')
app = Client("GeneralBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# قواعد بيانات وهمية (يتم مسحها عند ريستارت السيرفر في النسخة المجانية)
users_db = {} 
authorized_users = set()
last_download_time = {}

def download_media(url, mode, user_id):
    file_name = f"dl_{user_id}_{os.urandom(3).hex()}"
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best' if mode == 'video' else 'bestaudio/best',
        'outtmpl': f'{file_name}.%(ext)s',
        'merge_output_format': 'mp4' if mode == 'video' else None,
        'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3'}] if mode == 'audio' else [],
        'quiet': True, 'nocheckcertificate': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info), info.get('title', 'Media')

@app.on_message(filters.command("start"))
async def start(client, message):
    user_id = message.from_user.id
    if user_id not in users_db: users_db[user_id] = "عادي"
    if user_id in authorized_users:
        await message.reply_text(f"👑 **أهلاً بك يا جنرال!**\nرتبتك: {users_db[user_id]}\nأرسل الرابط للتحميل.")
    else:
        await message.reply_text("🔒 **البوت محمي!**\nمن فضلك أرسل كلمة المرور لتتمكن من استخدامه.")

@app.on_message(filters.text)
async def handle_msg(client, message):
    user_id = message.from_user.id
    text = message.text

    # نظام التحقق من الباسورد
    if text == PASSWORD:
        authorized_users.add(user_id)
        return await message.reply_text("✅ تم التحقق! يمكنك الآن استخدام كافة الميزات.")
    
    if user_id not in authorized_users:
        return await message.reply_text("❌ كلمة مرور خاطئة. لا يمكنك استخدام البوت.")

    # لوحة التحكم للأدمن
    if text == "/stats" and user_id == ADMIN_ID:
        return await message.reply_text(f"📊 **إحصائيات البوت:**\nعدد المستخدمين: {len(users_db)}")

    if "http" in text:
        # فرق السرعة (Cool-down)
        now = time.time()
        cooldown = 30 if users_db.get(user_id) == "عادي" else 5
        if user_id in last_download_time and (now - last_download_time[user_id] < cooldown):
            return await message.reply_text(f"⏳ رتبتك ({users_db[user_id]}) تسمح لك بالتحميل كل {cooldown} ثانية.")
        
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("🎬 فيديو", callback_data=f"v|{text}"),
            InlineKeyboardButton("🎵 صوت", callback_data=f"a|{text}")
        ]])
        await message.reply_text("🎬 اختر الصيغة المطلوب تحميلها:", reply_markup=keyboard)
    else:
        response = ai_model.generate_content(text)
        await message.reply_text(f"🤖 **Gemini AI:**\n\n{response.text}")

@app.on_callback_query()
async def callback(client, query: CallbackQuery):
    user_id = query.from_user.id
    data = query.data.split("|")
    mode, url = ('video' if data[0] == 'v' else 'audio'), data[1]
    
    await query.message.edit("📥 جاري التحميل... انتظر قليلاً.")
    try:
        loop = asyncio.get_event_loop()
        file_path, title = await loop.run_in_executor(None, download_media, url, mode, user_id)
        if mode == 'video':
            await query.message.reply_video(video=file_path, caption=f"🎬 {title}")
        else:
            await query.message.reply_audio(audio=file_path, caption=f"🎵 {title}")
        last_download_time[user_id] = time.time()
        if os.path.exists(file_path): os.remove(file_path)
        await query.message.delete()
    except Exception as e:
        await query.message.reply_text(f"❌ خطأ: {str(e)}")

app.run()
