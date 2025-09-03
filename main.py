import telebot
from telebot import types
import logging
from datetime import datetime

# Вставьте ваш токен бота сюда
BOT_TOKEN = "7514342466:AAEaW7lgV0xrVbAmle8Z1JYG6yLao54GHpk"
ADMIN_ID = 217697846  # Ваш telegram ID
# Включаем логирование
logging.basicConfig(level=logging.INFO)

# Инициализируем бота
bot = telebot.TeleBot(BOT_TOKEN)

# Словарь для хранения состояний пользователей
user_states = {}
user_data = {}

# Состояния
WAITING_CONTACT = "waiting_contact"
WAITING_EXPERIENCE = "waiting_experience"
WAITING_FORMAT = "waiting_format"

# Функции для создания клавиатур
def get_contact_keyboard():
    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
    contact_button = types.KeyboardButton("📱 Поделиться номером", request_contact=True)
    keyboard.add(contact_button)
    return keyboard

def get_experience_keyboard():
    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
    buttons = [
        "🆕 Новичок",
        "📅 Хожу в зал месяц",
        "💪 Хожу в зал полгода",
        "🏋️ Хожу год (занимался с тренером)",
        "🎯 Год занимался без тренера"
    ]
    keyboard.add(*[types.KeyboardButton(btn) for btn in buttons])
    return keyboard

def get_format_keyboard():
    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
    buttons = [
        "🎥 Онлайн ведение (видео с техникой + связь 24/7)",
        "📹 Онлайн тренировка (видеосвязь + связь 24/7)"
    ]
    keyboard.add(*[types.KeyboardButton(btn) for btn in buttons])
    return keyboard

# Команда /start
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    user_states[user_id] = WAITING_CONTACT
    user_data[user_id] = {}
    
    bot.send_message(
        message.chat.id,
        "👋 Привет! Я бот для записи на тренировки.\n\n"
        "Для начала мне нужен ваш номер телефона или telegram.",
        reply_markup=get_contact_keyboard()
    )

# Обработка контакта
@bot.message_handler(content_types=['contact'])
def process_contact(message):
    user_id = message.from_user.id
    
    if user_id not in user_states or user_states[user_id] != WAITING_CONTACT:
        return
    
    # Сохраняем контакт
    contact_info = f"{message.contact.first_name} {message.contact.last_name or ''}".strip()
    phone = message.contact.phone_number
    
    user_data[user_id] = {
        'contact_name': contact_info,
        'phone': phone,
        'username': message.from_user.username or "Не указан"
    }
    
    user_states[user_id] = WAITING_EXPERIENCE
    
    bot.send_message(
        message.chat.id,
        "📱 Отлично! Теперь выберите ваш уровень подготовки:",
        reply_markup=get_experience_keyboard()
    )

# Обработка всех текстовых сообщений
@bot.message_handler(content_types=['text'])
def process_text(message):
    user_id = message.from_user.id
    text = message.text
    
    # Если пользователь не начал диалог
    if user_id not in user_states:
        bot.send_message(message.chat.id, "🤖 Для начала работы нажмите /start")
        return
    
    current_state = user_states[user_id]
    
    # Ввод контакта вручную
    if current_state == WAITING_CONTACT:
        user_data[user_id] = {
            'contact_name': message.from_user.full_name,
            'phone': text,
            'username': message.from_user.username or "Не указан"
        }
        
        user_states[user_id] = WAITING_EXPERIENCE
        
        bot.send_message(
            message.chat.id,
            "📝 Принято! Теперь выберите ваш уровень подготовки:",
            reply_markup=get_experience_keyboard()
        )
    
    # Выбор опыта
    elif current_state == WAITING_EXPERIENCE:
        experience_options = [
            "🆕 Новичок",
            "📅 Хожу в зал месяц", 
            "💪 Хожу в зал полгода",
            "🏋️ Хожу год (занимался с тренером)",
            "🎯 Год занимался без тренера"
        ]
        
        if text not in experience_options:
            bot.send_message(
                message.chat.id,
                "❌ Пожалуйста, выберите один из предложенных вариантов:",
                reply_markup=get_experience_keyboard()
            )
            return
        
        user_data[user_id]['experience'] = text
        user_states[user_id] = WAITING_FORMAT
        
        bot.send_message(
            message.chat.id,
            "💪 Отлично! Теперь выберите формат тренировок:",
            reply_markup=get_format_keyboard()
        )
    
    # Выбор формата
    elif current_state == WAITING_FORMAT:
        format_options = [
            "🎥 Онлайн ведение (видео с техникой + связь 24/7)",
            "📹 Онлайн тренировка (видеосвязь + связь 24/7)"
        ]
        
        if text not in format_options:
            bot.send_message(
                message.chat.id,
                "❌ Пожалуйста, выберите один из предложенных форматов:",
                reply_markup=get_format_keyboard()
            )
            return
        
        user_data[user_id]['format'] = text
        
        # Отправляем подтверждение пользователю
        bot.send_message(
            message.chat.id,
            "✅ Спасибо! Ваша заявка принята.\n"
            "Скоро с вами свяжутся для уточнения деталей!",
            reply_markup=types.ReplyKeyboardRemove()
        )
        
        # Отправляем уведомление админу
        data = user_data[user_id]
        admin_message = (
            "🔔 НОВАЯ ЗАЯВКА НА ТРЕНИРОВКИ\n\n"
            f"👤 Клиент: {data['contact_name']}\n"
            f"📱 Телефон: {data['phone']}\n"
            f"🆔 Username: @{data['username']}\n"
            f"💪 Опыт: {data['experience']}\n"
            f"🎯 Формат: {data['format']}\n"
            f"📅 Время заявки: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        )
        
        try:
            bot.send_message(ADMIN_ID, admin_message)
        except Exception as e:
            logging.error(f"Ошибка отправки админу: {e}")
        
        # Очищаем состояние
        del user_states[user_id]
        del user_data[user_id]
    
    else:
        bot.send_message(message.chat.id, "🤖 Для начала работы нажмите /start")


import telebot
from telebot import types
import logging
from datetime import datetime
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import os

# Фиктивный веб-сервер для Render
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'Bot is running!')
    
    def log_message(self, format, *args):
        pass  # Отключаем логи веб-сервера

def start_web_server():
    port = int(os.environ.get('PORT', 10000))
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    print(f"🌐 Веб-сервер запущен на порту {port}")
    server.serve_forever()

# Запуск бота
if __name__ == "__main__":
    print("🤖 Бот запущен!")
    
    # Запускаем веб-сервер в отдельном потоке
    web_thread = threading.Thread(target=start_web_server, daemon=True)
    web_thread.start()
    
    # Запускаем бота
    bot.infinity_polling()