"""
🤖 TELEGRAM БОТ-ПЕРЕВОДЧИК РУССКИЙ ↔ ЭСТОНСКИЙ
Версия для Railway.app
"""

import telebot
import requests
import json
import time
import sys
import os
import logging
from typing import Optional, Tuple
from flask import Flask, request, Response
from threading import Thread

# ================= КОНФИГУРАЦИЯ =================
class Config:
    """Конфигурация бота (ваши данные)"""
    # Получаем из переменных окружения Railway
    TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', '8432469082:AAHLl4EBWZXqq1YgtDRNoA1DX2EfB1PgLg8')
    DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', 'sk-e37ff6b07b7b4b97847583198555fc1a')
    
    # ID пользователей (твои данные)
    USER_IDS = {
        "viktor": 5274888623,    # Вы (русский)
        "boss": 5201027183       # Начальник (эстонский)
    }
    
    # Настройки API
    DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
    REQUEST_TIMEOUT = 30
    MAX_RETRIES = 3
    RETRY_DELAY = 2

# ================= ИНИЦИАЛИЗАЦИЯ =================
class TranslatorBot:
    """Основной класс бота-переводчика"""
    
    def __init__(self):
        """Инициализация бота с проверкой конфигурации"""
        self.validate_config()
        
        # Инициализация бота Telegram
        self.bot = telebot.TeleBot(Config.TELEGRAM_TOKEN)
        
        # Логирование
        self.setup_logging()
        
        # Карта языков
        self.language_map = {
            Config.USER_IDS["viktor"]: ("ru", "et"),  # русский → эстонский
            Config.USER_IDS["boss"]: ("et", "ru")     # эстонский → русский
        }
        
        print("=" * 60)
        print("🤖 БОТ-ПЕРЕВОДЧИК ИНИЦИАЛИЗИРОВАН")
        print(f"🚀 Запущен на Railway.app")
        print("=" * 60)
    
    def validate_config(self):
        """Валидация конфигурации перед запуском"""
        errors = []
        
        # Проверка токена Telegram
        if not Config.TELEGRAM_TOKEN or len(Config.TELEGRAM_TOKEN) < 30:
            errors.append("Токен Telegram недействителен или слишком короткий")
        
        # Проверка ключа DeepSeek
        if not Config.DEEPSEEK_API_KEY or not Config.DEEPSEEK_API_KEY.startswith("sk-"):
            errors.append("Ключ DeepSeek API недействителен (должен начинаться с 'sk-')")
        
        # Проверка ID пользователей
        if Config.USER_IDS["viktor"] == Config.USER_IDS["boss"]:
            errors.append("ID пользователей не должны совпадать")
        
        if not isinstance(Config.USER_IDS["viktor"], int) or Config.USER_IDS["viktor"] <= 0:
            errors.append("Ваш ID должен быть положительным числом")
        
        if not isinstance(Config.USER_IDS["boss"], int) or Config.USER_IDS["boss"] <= 0:
            errors.append("ID начальника должен быть положительным числом")
        
        if errors:
            print("❌ ОШИБКИ КОНФИГУРАЦИИ:")
            for error in errors:
                print(f"   - {error}")
            sys.exit(1)
    
    def setup_logging(self):
        """Настройка логирования"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        self.logger = logging.getLogger(__name__)
    
    def get_translation_direction(self, sender_id: int) -> Optional[Tuple[int, str, str]]:
        """Определение направления перевода по ID отправителя"""
        if sender_id == Config.USER_IDS["viktor"]:
            recipient_id = Config.USER_IDS["boss"]
            from_lang, to_lang = self.language_map[sender_id]
            self.logger.info(f"👤 Вы → 👔 Начальник (ru→et)")
            return recipient_id, from_lang, to_lang
        
        elif sender_id == Config.USER_IDS["boss"]:
            recipient_id = Config.USER_IDS["viktor"]
            from_lang, to_lang = self.language_map[sender_id]
            self.logger.info(f"👔 Начальник → 👤 Вы (et→ru)")
            return recipient_id, from_lang, to_lang
        
        return None
    
    def translate_with_retry(self, text: str, from_lang: str, to_lang: str) -> Optional[str]:
        """Перевод текста с повторными попытками при ошибках"""
        for attempt in range(Config.MAX_RETRIES):
            try:
                return self._translate_text(text, from_lang, to_lang)
            except requests.exceptions.RequestException as e:
                if attempt < Config.MAX_RETRIES - 1:
                    self.logger.warning(f"Попытка {attempt + 1} не удалась: {e}. Повтор через {Config.RETRY_DELAY} сек...")
                    time.sleep(Config.RETRY_DELAY)
                else:
                    self.logger.error(f"Все попытки перевода не удались: {e}")
                    return None
            except Exception as e:
                self.logger.error(f"Неожиданная ошибка перевода: {e}")
                return None
        
        return None
    
    def _translate_text(self, text: str, from_lang: str, to_lang: str) -> str:
        """Основная функция перевода через DeepSeek API"""
        # Подготовка промпта в зависимости от направления
        if from_lang == 'ru' and to_lang == 'et':
            system_prompt = (
                "Ты профессиональный переводчик с русского на эстонский. "
                "Переведи текст максимально точно, сохраняя смысл и стиль. "
                "Не добавляй пояснений, только чистый перевод."
            )
        else:
            system_prompt = (
                "Ты профессиональный переводчик с эстонского на русский. "
                "Переведи текст максимально точно, сохраняя смысл и стиль. "
                "Не добавляй пояснений, только чистый перевод."
            )
        
        # Формирование запроса
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            "max_tokens": 1000,
            "temperature": 0.3
        }
        
        headers = {
            "Authorization": f"Bearer {Config.DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Отправка запроса
        response = requests.post(
            Config.DEEPSEEK_API_URL,
            headers=headers,
            json=payload,
            timeout=Config.REQUEST_TIMEOUT
        )
        
        # Проверка ответа
        response.raise_for_status()
        
        # Парсинг ответа
        result = response.json()
        
        if 'choices' not in result or not result['choices']:
            raise ValueError("Некорректный ответ от API DeepSeek")
        
        translated_text = result['choices'][0]['message']['content'].strip()
        
        # Очистка текста
        translated_text = self.clean_translation(translated_text)
        
        self.logger.info(f"Перевод: '{text[:50]}...' → '{translated_text[:50]}...'")
        return translated_text
    
    def clean_translation(self, text: str) -> str:
        """Очистка переведенного текста от лишних символов"""
        # Удаляем кавычки в начале и конце
        text = text.strip()
        for quote in ['"', "'", "«", "»", "```"]:
            if text.startswith(quote) and text.endswith(quote):
                text = text[len(quote):-len(quote)].strip()
        
        # Удаляем маркеры типа "Перевод:"
        prefixes_to_remove = ["Перевод:", "Translation:", "Tõlge:", "Tõlge on:"]
        for prefix in prefixes_to_remove:
            if text.startswith(prefix):
                text = text[len(prefix):].strip()
        
        return text
    
    def handle_media_message(self, message):
        """Обработка медиафайлов (фото, видео, документы и т.д.) - просто пересылка"""
        sender_id = message.chat.id
        self.logger.info(f"📎 Получен медиафайл от {sender_id}")
        
        # Определяем получателя
        translation_info = self.get_translation_direction(sender_id)
        
        if not translation_info:
            self.logger.warning(f"Неизвестный отправитель: {sender_id}")
            self.bot.send_message(sender_id, "⛔ Этот бот приватный. Доступ ограничен.")
            return
        
        recipient_id = translation_info[0]
        
        try:
            # Пересылаем медиа в зависимости от типа
            
            # 1. Фото
            if message.photo:
                photo_id = message.photo[-1].file_id
                caption = message.caption
                
                if caption:
                    translated_caption = self.translate_with_retry(
                        caption, 
                        translation_info[1], 
                        translation_info[2]
                    )
                    if translated_caption:
                        self.bot.send_photo(recipient_id, photo_id, caption=translated_caption)
                        self.logger.info(f"✅ Отправлено фото с переведенной подписью")
                    else:
                        self.bot.send_photo(recipient_id, photo_id, caption=caption)
                        self.logger.info(f"✅ Отправлено фото с оригинальной подписью")
                else:
                    self.bot.send_photo(recipient_id, photo_id)
                    self.logger.info(f"✅ Отправлено фото")
            
            # 2. Видео
            elif message.video:
                video_id = message.video.file_id
                caption = message.caption
                
                if caption:
                    translated_caption = self.translate_with_retry(
                        caption, 
                        translation_info[1], 
                        translation_info[2]
                    )
                    if translated_caption:
                        self.bot.send_video(recipient_id, video_id, caption=translated_caption)
                        self.logger.info(f"✅ Отправлено видео с переведенной подписью")
                    else:
                        self.bot.send_video(recipient_id, video_id, caption=caption)
                        self.logger.info(f"✅ Отправлено видео с оригинальной подписью")
                else:
                    self.bot.send_video(recipient_id, video_id)
                    self.logger.info(f"✅ Отправлено видео")
            
            # 3. Документы/файлы
            elif message.document:
                doc_id = message.document.file_id
                caption = message.caption
                
                if caption:
                    translated_caption = self.translate_with_retry(
                        caption, 
                        translation_info[1], 
                        translation_info[2]
                    )
                    if translated_caption:
                        self.bot.send_document(recipient_id, doc_id, caption=translated_caption)
                        self.logger.info(f"✅ Отправлен документ с переведенной подписью")
                    else:
                        self.bot.send_document(recipient_id, doc_id, caption=caption)
                        self.logger.info(f"✅ Отправлен документ с оригинальной подписью")
                else:
                    self.bot.send_document(recipient_id, doc_id)
                    self.logger.info(f"✅ Отправлен документ")
            
            # 4. Аудио
            elif message.audio:
                audio_id = message.audio.file_id
                caption = message.caption
                
                if caption:
                    translated_caption = self.translate_with_retry(
                        caption, 
                        translation_info[1], 
                        translation_info[2]
                    )
                    if translated_caption:
                        self.bot.send_audio(recipient_id, audio_id, caption=translated_caption)
                    else:
                        self.bot.send_audio(recipient_id, audio_id, caption=caption)
                else:
                    self.bot.send_audio(recipient_id, audio_id)
                self.logger.info(f"✅ Отправлено аудио")
            
            # 5. Голосовые сообщения
            elif message.voice:
                voice_id = message.voice.file_id
                self.bot.send_voice(recipient_id, voice_id)
                self.logger.info(f"✅ Отправлено голосовое сообщение")
            
            # 6. Стикеры
            elif message.sticker:
                sticker_id = message.sticker.file_id
                self.bot.send_sticker(recipient_id, sticker_id)
                self.logger.info(f"✅ Отправлен стикер")
            
            # 7. Локация
            elif message.location:
                lat = message.location.latitude
                lon = message.location.longitude
                self.bot.send_location(recipient_id, lat, lon)
                self.logger.info(f"✅ Отправлена локация")
            
            # 8. Контакт
            elif message.contact:
                contact = message.contact
                self.bot.send_contact(
                    recipient_id,
                    phone_number=contact.phone_number,
                    first_name=contact.first_name,
                    last_name=contact.last_name or ''
                )
                self.logger.info(f"✅ Отправлен контакт")
            
            else:
                self.logger.warning(f"Неподдерживаемый тип медиа")
                self.bot.send_message(sender_id, "⚠️ Этот тип сообщения не поддерживается для пересылки")
                
        except Exception as e:
            self.logger.error(f"Ошибка пересылки медиафайла: {e}")
            try:
                self.bot.send_message(sender_id, "❌ Не удалось переслать медиафайл")
            except:
                pass
    
    def handle_text_message(self, message):
        """Обработка текстовых сообщений с переводом"""
        sender_id = message.chat.id
        text = message.text
        
        self.logger.info(f"📨 Получено от {sender_id}: {text[:100]}")
        
        # Определяем направление перевода
        translation_info = self.get_translation_direction(sender_id)
        
        if not translation_info:
            # Неизвестный пользователь
            self.logger.warning(f"Неизвестный отправитель: {sender_id}")
            self.bot.send_message(sender_id, "⛔ Этот бот приватный. Доступ ограничен.")
            return
        
        recipient_id, from_lang, to_lang = translation_info
        
        # Проверяем, не пустое ли сообщение
        if not text or text.strip() == "":
            self.logger.warning("Получено пустое сообщение, игнорирую")
            return
        
        # Пропускаем команды
        if text.startswith('/'):
            self.logger.info(f"Пропущена команда: {text}")
            return
        
        # Выполняем перевод
        translated_text = self.translate_with_retry(text, from_lang, to_lang)
        
        if translated_text:
            # Отправляем переведенное сообщение
            try:
                self.bot.send_message(recipient_id, translated_text)
                self.logger.info(f"✅ Отправлено {recipient_id}: {translated_text[:50]}...")
            except Exception as e:
                self.logger.error(f"Ошибка отправки сообщения: {e}")
        else:
            # Ошибка перевода
            error_msg = f"[Ошибка перевода] {text}"
            try:
                self.bot.send_message(recipient_id, error_msg)
                self.logger.error(f"Отправлен оригинал из-за ошибки перевода")
            except Exception as e:
                self.logger.error(f"Не удалось отправить даже оригинал: {e}")
    
    def handle_message(self, message):
        """Главный обработчик входящих сообщений"""
        # Определяем тип сообщения и вызываем соответствующий обработчик
        if message.content_type == 'text':
            self.handle_text_message(message)
        else:
            # Все остальные типы сообщений (медиа)
            self.handle_media_message(message)
    
    def test_api_connection(self) -> bool:
        """Тестирование подключения к API DeepSeek"""
        try:
            test_text = "Привет"
            test_result = self._translate_text(test_text, 'ru', 'et')
            
            if test_result and len(test_result) > 0:
                print(f"✅ API DeepSeek работает: '{test_text}' → '{test_result}'")
                return True
            else:
                print("❌ API вернул пустой ответ")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка подключения к API DeepSeek: {e}")
            return False
    
    def run_bot(self):
        """Запуск бота в отдельном потоке"""
        # Регистрация универсального обработчика
        @self.bot.message_handler(func=lambda message: True)
        def message_handler(message):
            self.handle_message(message)
        
        # Тестирование API
        print("🔍 Тестирование подключения к DeepSeek API...")
        if not self.test_api_connection():
            print("⚠️  Внимание: проблемы с API. Бот запустится, но перевод может не работать.")
        
        # Информация о пользователях
        print("=" * 60)
        print("👤 ВЫ (русский):")
        print(f"   ID: {Config.USER_IDS['viktor']}")
        print(f"   Язык: русский → эстонский")
        print()
        print("👔 НАЧАЛЬНИК (эстонский):")
        print(f"   ID: {Config.USER_IDS['boss']}")
        print(f"   Язык: эстонский → русский")
        print("=" * 60)
        print("💡 Бот работает на Railway.app")
        print("=" * 60)
        print("🔄 Бот запускается...")
        
        # Запуск бота
        try:
            self.bot.polling(none_stop=True, interval=1, timeout=30)
        except KeyboardInterrupt:
            print("\n🛑 Бот остановлен")
        except Exception as e:
            print(f"❌ Критическая ошибка: {e}")
            self.logger.error(f"Бот упал: {e}")
            # Перезапуск через 5 секунд
            time.sleep(5)
            self.run_bot()

# ================= FLASK СЕРВЕР ДЛЯ RAILWAY =================
app = Flask(__name__)

@app.route('/')
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>🤖 Переводчик бот</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                background-color: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 {
                color: #333;
                text-align: center;
            }
            .status {
                background-color: #4CAF50;
                color: white;
                padding: 10px;
                border-radius: 5px;
                text-align: center;
                margin: 20px 0;
            }
            .info {
                background-color: #e8f4fc;
                padding: 15px;
                border-radius: 5px;
                margin: 15px 0;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 Telegram Переводчик Бот</h1>
            <div class="status">✅ Сервис работает нормально</div>
            
            <div class="info">
                <h3>👤 Пользователи:</h3>
                <p><strong>Вы (русский):</strong> ID {}</p>
                <p><strong>Начальник (эстонский):</strong> ID {}</p>
            </div>
            
            <div class="info">
                <h3>📊 Статус:</h3>
                <p>Бот запущен и готов к работе</p>
                <p>Перевод: Русский ↔ Эстонский</p>
            </div>
            
            <div class="info">
                <h3>🔗 Проверки:</h3>
                <p><a href="/health">Проверить здоровье сервиса</a></p>
                <p><a href="/logs">Посмотреть логи (текст)</a></p>
            </div>
        </div>
    </body>
    </html>
    """.format(Config.USER_IDS['viktor'], Config.USER_IDS['boss'])

@app.route('/health')
def health():
    return {
        "status": "healthy",
        "service": "telegram-translator-bot",
        "users": {
            "viktor_id": Config.USER_IDS['viktor'],
            "boss_id": Config.USER_IDS['boss']
        },
        "environment": "railway"
    }

@app.route('/logs')
def logs():
    return "Логи бота доступны в панели Railway.app"

# ================= ЗАПУСК ВСЕГО ПРИЛОЖЕНИЯ =================
def start_flask():
    """Запуск Flask сервера"""
    port = int(os.environ.get("PORT", 5000))
    print(f"🌐 Flask сервер запущен на порту {port}")
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    try:
        # Запускаем бота в отдельном потоке
        bot_instance = TranslatorBot()
        bot_thread = Thread(target=bot_instance.run_bot, daemon=True)
        bot_thread.start()
        
        # Запускаем Flask сервер в основном потоке
        start_flask()
        
    except Exception as e:
        print(f"❌ ФАТАЛЬНАЯ ОШИБКА ПРИ ЗАПУСКЕ: {e}")
        print("Проверьте:")
        print("1. Интернет-соединение")
        print("2. Корректность токена и API ключа в Railway Variables")
        print("3. Правильность ID пользователей")
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "pip install -r requirements.txt"
  },
  "deploy": {
    "numReplicas": 1,
    "startCommand": "python main.py",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
txt
telebot==0.0.5
Flask==2.3.3
requests==2.31.0
gunicorn==21.2.0
