"""
🤖 Telegram Bot для Railway.app
Webhook версия (полностью рабочий код)
"""

import os
import telebot
import requests
from flask import Flask, request, jsonify
import logging

# ================= НАСТРОЙКИ ИЗ ПЕРЕМЕННЫХ СРЕДЫ =================
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', '8432469082:AAHLl4EBWZXqq1YgtDRNoA1DX2EfB1PgLg8')
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', 'sk-e37ff6b07b7b4b97847583198555fc1a')
RAILWAY_PUBLIC_URL = os.environ.get('RAILWAY_PUBLIC_URL', '')
WEBHOOK_PORT = int(os.environ.get('PORT', 8080))

# ================= ID ПОЛЬЗОВАТЕЛЕЙ =================
VIKTOR_ID = 5274888623    # Вы
BOSS_ID = 5201027183      # Начальник

# ================= ИНИЦИАЛИЗАЦИЯ =================
bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

# Флаг подключения
boss_connected = False

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ================= ФУНКЦИЯ ПЕРЕВОДА =================
def translate_text(text, from_lang='ru', to_lang='et'):
    """Перевод через DeepSeek API"""
    try:
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        
        if from_lang == 'ru' and to_lang == 'et':
            prompt = f"Ты профессиональный переводчик переведи с русского на эстонский точно и кратко сохраняя смысл: {text}"
        else:
            prompt = f"Ты профессиональный переводчик переведи с эстонского на русский точно и кратко сохраняя смысл: {text}"
        
        data = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 500,
            "temperature": 0.3
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        translation = result['choices'][0]['message']['content'].strip()
        
        # Очистка от префиксов
        for prefix in ['Перевод:', 'Translation:', 'Tõlge:']:
            if translation.startswith(prefix):
                translation = translation[len(prefix):].strip()
        
        logger.info(f"Перевод: '{text[:50]}...' → '{translation[:50]}...'")
        return translation
        
    except Exception as e:
        logger.error(f"Ошибка перевода: {e}")
        return None

# ================= КОМАНДЫ TELEGRAM =================
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """Приветственное сообщение"""
    user_id = message.chat.id
    
    if user_id == VIKTOR_ID:
        welcome_text = (
            "🤖 *Бот работает на Railway!*\n\n"
            "✅ Webhook подключен\n"
            "🌍 Переводчик активен\n\n"
            "💡 Просто пишите сообщения - они будут переведены начальнику."
        )
        bot.send_message(user_id, welcome_text, parse_mode='Markdown')
        logger.info(f"Вы ({user_id}) запустили бота")
        
    elif user_id == BOSS_ID:
        global boss_connected
        boss_connected = True
        
        welcome_text = (
            "🤖 *Translation bot is active!*\n\n"
            "✅ Webhook connected\n"
            "🌍 Translator ready\n\n"
            "💡 Write messages in Estonian - they will be translated to Russian."
        )
        bot.send_message(user_id, welcome_text, parse_mode='Markdown')
        bot.send_message(VIKTOR_ID, "🎉 *Начальник подключился!*", parse_mode='Markdown')
        logger.info(f"Начальник ({user_id}) подключился")
        
    else:
        bot.send_message(user_id, "⛔ Private bot. Access denied.")
        logger.warning(f"Неизвестный пользователь: {user_id}")

@bot.message_handler(commands=['status'])
def status_command(message):
    """Проверка статуса"""
    user_id = message.chat.id
    if user_id == VIKTOR_ID:
        status = "✅ Бот работает" if boss_connected else "⏳ Ожидаю подключения начальника"
        bot.send_message(user_id, status)

# ================= ОБРАБОТКА СООБЩЕНИЙ =================
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    """Обработка всех сообщений"""
    global boss_connected
    
    user_id = message.chat.id
    text = message.text
    
    # Пропускаем команды
    if text.startswith('/'):
        return
    
    logger.info(f"📨 Получено от {user_id}: {text[:100]}")
    
    # Сообщение от вас
    if user_id == VIKTOR_ID:
        if not boss_connected:
            bot.send_message(user_id, "⏳ Ожидаю подключения начальника...")
            return
        
        # Переводим на эстонский
        translation = translate_text(text, 'ru', 'et')
        
        if translation:
            try:
                bot.send_message(BOSS_ID, translation)
                bot.send_message(user_id, "✅ Отправлено")
                logger.info(f"RU→ET: '{text}' → '{translation}'")
            except Exception as e:
                logger.error(f"Ошибка отправки: {e}")
                bot.send_message(user_id, f"❌ Ошибка: {str(e)[:100]}")
        else:
            bot.send_message(user_id, "❌ Ошибка перевода")
    
    # Сообщение от начальника
    elif user_id == BOSS_ID:
        # Первое сообщение - отмечаем подключение
        if not boss_connected:
            boss_connected = True
            bot.send_message(VIKTOR_ID, "🎉 *Начальник подключился!*", parse_mode='Markdown')
        
        # Переводим на русский
        translation = translate_text(text, 'et', 'ru')
        
        if translation:
            try:
                bot.send_message(VIKTOR_ID, translation)
                logger.info(f"ET→RU: '{text}' → '{translation}'")
            except Exception as e:
                logger.error(f"Ошибка отправки: {e}")
        else:
            bot.send_message(BOSS_ID, "❌ Translation error")

# ================= FLASK ROUTES ДЛЯ RAILWAY =================
@app.route('/')
def home():
    """Главная страница для проверки работы"""
    return jsonify({
        "status": "online",
        "service": "Telegram Translation Bot",
        "users": {
            "viktor": VIKTOR_ID,
            "boss": BOSS_ID,
            "boss_connected": boss_connected
        }
    })

@app.route('/webhook', methods=['POST'])
def webhook():
    """Webhook endpoint для Telegram"""
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    return 'Bad request', 400

@app.route('/health')
def health():
    """Health check для Railway"""
    return 'OK', 200

# ================= НАСТРОЙКА WEBHOOK =================
def set_webhook():
    """Установка webhook в Telegram"""
    if RAILWAY_PUBLIC_URL:
        webhook_url = f"{RAILWAY_PUBLIC_URL}/webhook"
        try:
            bot.remove_webhook()
            bot.set_webhook(url=webhook_url)
            logger.info(f"Webhook установлен: {webhook_url}")
        except Exception as e:
            logger.error(f"Ошибка установки webhook: {e}")
    else:
        logger.warning("RAILWAY_PUBLIC_URL не установлен, webhook не настроен")

# ================= ЗАПУСК ПРИЛОЖЕНИЯ =================
if __name__ == '__main__':
    # Настраиваем webhook при запуске
    set_webhook()
    
    # Запускаем Flask сервер
    logger.info(f"🚀 Запуск бота на порту {WEBHOOK_PORT}")
    logger.info(f"👤 Ваш ID: {VIKTOR_ID}")
    logger.info(f"👔 ID начальника: {BOSS_ID}")
    
    # Проверка переменных окружения
    logger.info(f"TELEGRAM_TOKEN: {'установлен' if TELEGRAM_TOKEN else 'НЕТ!'}")
    logger.info(f"DEEPSEEK_API_KEY: {'установлен' if DEEPSEEK_API_KEY else 'НЕТ!'}")
    logger.info(f"RAILWAY_PUBLIC_URL: {RAILWAY_PUBLIC_URL or 'не установлен'}")
    
    app.run(host='0.0.0.0', port=WEBHOOK_PORT)
