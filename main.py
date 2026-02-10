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
    """Обработчик всех текстовых сообщений"""
    user_id = str(update.effective_user.id)
    user_text = update.message.text
    
    logger.info(f"Сообщение от {user_id}: {user_text}")
    
    # Проверяем токен
    if not TELEGRAM_BOT_TOKEN or not DEEPSEEK_API_KEY:
        await update.message.reply_text("⚠️ Бот не настроен. Проверьте API-ключи.")
        return
    
    # Определяем направление перевода
    if user_id == MY_CHAT_ID:
        # Ты пишешь -> переводим на эстонский для начальника
        try:
            translated = translate_text(user_text, "russian", "estonian")
            
            # Отправляем перевод начальнику
            await context.bot.send_message(
                chat_id=BOSS_CHAT_ID,
                text=f"🇷🇺→🇪🇪\n{translated}\n\n(От: {update.effective_user.first_name})"
            )
            
            # Подтверждаем тебе
            await update.message.reply_text(f"✅ Переведено и отправлено!\nПеревод: {translated}")
            
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка: {str(e)}")
            
    elif user_id == BOSS_CHAT_ID:
        # Начальник пишет -> переводим на русский для тебя
        try:
            translated = translate_text(user_text, "estonian", "russian")
            
            # Отправляем перевод тебе
            await context.bot.send_message(
                chat_id=MY_CHAT_ID,
                text=f"🇪🇪→🇷🇺\n{translated}\n\n(От: начальника)"
            )
            
            # Подтверждаем начальнику
            await update.message.reply_text(f"✅ Tõlgitud ja saadetud!\nTõlge: {translated}")
            
        except Exception as e:
            await update.message.reply_text(f"❌ Viga: {str(e)}")
    else:
        await update.message.reply_text("❌ У вас нет доступа к этому боту.")

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
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)
    
    # Запускаем бота
    logger.info("Бот запускается...")
    
    # Для Railway: используем вебхук (лучше для хостинга)
    PORT = int(os.environ.get("PORT", 8443))
    
    if "RAILWAY_STATIC_URL" in os.environ:
        # На Railway - настраиваем вебхук
        webhook_url = os.environ.get("RAILWAY_STATIC_URL") + "/webhook"
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            webhook_url=webhook_url,
            url_path="webhook"
        )
    else:
        # Локально - используем polling
        print("🚀 Бот запущен локально. Нажми Ctrl+C для остановки.")
        app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
