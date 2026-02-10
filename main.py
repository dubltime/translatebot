import asyncio
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests
import json

# ==================== НАСТРОЙКА ====================
# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ID чатов (ЗАМЕНИ НА СВОИ!)
MY_CHAT_ID = "5274888623"          # Твой ID в Telegram
BOSS_CHAT_ID = "8304415866"        # ID начальника в Telegram

# Ключи (будут взяты из переменных окружения)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# ==================== ФУНКЦИИ ПЕРЕВОДА ====================
def translate_text(text, from_lang="russian", to_lang="estonian"):
    """Перевод текста через DeepSeek API"""
    try:
        url = "https://api.deepseek.com/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        
        prompt = f"Переведи этот текст с {from_lang} на {to_lang}. Только перевод, без пояснений:\n{text}"
        
        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 500,
            "temperature": 0.3
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        translated_text = result['choices'][0]['message']['content'].strip()
        
        # Убираем возможные кавычки и лишние пробелы
        translated_text = translated_text.replace('"', '').replace("'", '').strip()
        
        return translated_text
        
    except Exception as e:
        logger.error(f"Ошибка перевода: {e}")
        return f"⚠️ Ошибка перевода: {str(e)}"

# ==================== ОБРАБОТЧИКИ TELEGRAM ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user_id = update.effective_user.id
    
    # Определяем, кто запустил бота
    if str(user_id) == MY_CHAT_ID:
        await update.message.reply_text(
            "👋 Привет! Я бот-переводчик.\n"
            "Все твои сообщения я буду автоматически переводить начальнику на эстонский.\n"
            "Просто пиши мне сообщения на русском!"
        )
    elif str(user_id) == BOSS_CHAT_ID:
        await update.message.reply_text(
            "👋 Tere! Ma olen tõlkebot.\n"
            "Kõik teie sõnumid tõlgin automaatselt vene keelest eesti keelde.\n"
            "Lihtsalt kirjutage mulle sõnumeid eesti keeles!"
        )
    else:
        await update.message.reply_text("❌ У вас нет доступа к этому боту.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ВСЕХ сообщений с повторными попытками отправки"""
    user_id = str(update.effective_user.id)
    
    # Игнорируем ботов и проверяем доступ
    if update.effective_user.is_bot:
        return
    
    if user_id not in [MY_CHAT_ID, BOSS_CHAT_ID]:
        return
    
    # Определяем пару для перевода
    if user_id == MY_CHAT_ID:
        target_id = BOSS_CHAT_ID
        from_lang, to_lang = "russian", "estonian"
    else:
        target_id = MY_CHAT_ID
        from_lang, to_lang = "estonian", "russian"
    
    # Функция для повторных попыток отправки
    async def send_with_retry(send_func, max_retries=3):
        """Повторные попытки отправки"""
        for attempt in range(max_retries):
            try:
                await send_func()
                return True
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 3 * (attempt + 1)
                    logger.warning(f"Попытка {attempt+1} не удалась, жду {wait_time}сек")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Все {max_retries} попытки не удались: {e}")
                    # Уведомление отправителю о неудаче
                    try:
                        await update.message.reply_text("❌ Не удалось отправить сообщение")
                    except:
                        pass
                    return False
        return False
    
    try:
        message = update.message
        
        # 1. ТЕКСТ
        if message.text:
            translated = translate_text(message.text, from_lang, to_lang)
            await send_with_retry(
                lambda: context.bot.send_message(
                    chat_id=target_id, 
                    text=translated
                ),
                max_retries=3
            )
            return
        
        # 2. ФОТО
        if message.photo:
            photo = message.photo[-1]
            caption = message.caption
            
            if caption:
                translated_caption = translate_text(caption, from_lang, to_lang)
                await send_with_retry(
                    lambda: context.bot.send_photo(
                        chat_id=target_id,
                        photo=photo.file_id,
                        caption=translated_caption
                    ),
                    max_retries=2
                )
            else:
                await send_with_retry(
                    lambda: context.bot.send_photo(
                        chat_id=target_id,
                        photo=photo.file_id
                    ),
                    max_retries=2
                )
            return
        
        # 3. ВИДЕО
        if message.video:
            video = message.video
            caption = message.caption
            
            if caption:
                translated_caption = translate_text(caption, from_lang, to_lang)
                await send_with_retry(
                    lambda: context.bot.send_video(
                        chat_id=target_id,
                        video=video.file_id,
                        caption=translated_caption
                    ),
                    max_retries=2
                )
            else:
                await send_with_retry(
                    lambda: context.bot.send_video(
                        chat_id=target_id,
                        video=video.file_id
                    ),
                    max_retries=2
                )
            return
        
        # 4. ДОКУМЕНТЫ
        if message.document:
            document = message.document
            caption = message.caption
            
            if caption:
                translated_caption = translate_text(caption, from_lang, to_lang)
                await send_with_retry(
                    lambda: context.bot.send_document(
                        chat_id=target_id,
                        document=document.file_id,
                        caption=translated_caption
                    ),
                    max_retries=2
                )
            else:
                await send_with_retry(
                    lambda: context.bot.send_document(
                        chat_id=target_id,
                        document=document.file_id
                    ),
                    max_retries=2
                )
            return
        
        # 5. АУДИО
        if message.audio:
            audio = message.audio
            caption = message.caption
            
            if caption:
                translated_caption = translate_text(caption, from_lang, to_lang)
                await send_with_retry(
                    lambda: context.bot.send_audio(
                        chat_id=target_id,
                        audio=audio.file_id,
                        caption=translated_caption
                    ),
                    max_retries=2
                )
            else:
                await send_with_retry(
                    lambda: context.bot.send_audio(
                        chat_id=target_id,
                        audio=audio.file_id
                    ),
                    max_retries=2
                )
            return
        
        # 6. ГОЛОСОВЫЕ СООБЩЕНИЯ
        if message.voice:
            await send_with_retry(
                lambda: context.bot.send_voice(
                    chat_id=target_id,
                    voice=message.voice.file_id
                ),
                max_retries=2
            )
            return
        
        # 7. СТИКЕРЫ
        if message.sticker:
            await send_with_retry(
                lambda: context.bot.send_sticker(
                    chat_id=target_id,
                    sticker=message.sticker.file_id
                ),
                max_retries=2
            )
            return
        
        # 8. ВСЁ ОСТАЛЬНОЕ - просто пересылаем
        await send_with_retry(
            lambda: message.forward(chat_id=target_id),
            max_retries=2
        )
        
    except Exception as e:
        logger.error(f"Критическая ошибка обработки: {e}")
        # Тихий режим - не спамим пользователю

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Ошибка: {context.error}")
    
    # Отправляем сообщение об ошибке тебе (разработчику)
    try:
        await context.bot.send_message(
            chat_id=MY_CHAT_ID,
            text=f"⚠️ Ошибка в боте: {str(context.error)[:100]}..."
        )
    except:
        pass

# ==================== ЗАПУСК БОТА ====================
def main():
    """Основная функция запуска бота"""
    # Проверяем наличие токенов
    if not TELEGRAM_BOT_TOKEN:
        logger.error("Не задан TELEGRAM_BOT_TOKEN!")
        return
    if not DEEPSEEK_API_KEY:
        logger.error("Не задан DEEPSEEK_API_KEY!")
        return
    
    # Создаём приложение
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Регистрируем обработчики
    # Убрал /start чтобы не мешал, если нужен - раскомментируй
    # app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL, handle_message))
    # Убрал error_handler чтобы не спамил уведомлениями
    # app.add_error_handler(error_handler)
    
    # Запускаем бота
    logger.info("🚀 Бот запускается на Railway...")
    print("Бот активен. Ожидаю сообщения...")
    
    # Всегда используем polling - он проще и надёжнее
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,  # очищает очередь при перезапуске
        close_loop=False
    )

# Запуск бота при выполнении файла
if __name__ == "__main__":
    main()

# ==================== FLASK СЕРВЕР ДЛЯ RAILWAY ====================
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Telegram Translation Bot is running!"

@app.route('/health')
def health():
    return "OK", 200

# Запуск Flask в отдельном потоке, чтобы не мешать боту
import threading

def run_flask():
    app.run(host='0.0.0.0', port=8080, debug=False)

# Запускаем Flask в фоне при старте
if "RAILWAY_ENVIRONMENT" in os.environ:
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    print("Flask server started for Railway")
if __name__ == "__main__":
    main()
