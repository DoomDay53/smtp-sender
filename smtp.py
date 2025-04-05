
import sqlite3
import smtplib
import logging
from typing import Dict, List, Optional, Tuple
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from threading import Lock
import time

# КФГ
BOT_TOKEN = "" # Токен свой добавь
ADMINS = []  # ID администраторов
TARGET_EMAIL = "telegram@gmail.com"  # Почта на которую летят жб (поменять на свою)
DB_NAME = "subscriptions.db"
LOG_FILE = "smtp_bot.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(BOT_TOKEN)

db_lock = Lock()
conn = sqlite3.connect(DB_NAME, check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS subscriptions (
    user_id INTEGER PRIMARY KEY,
    subscription_date TEXT DEFAULT CURRENT_TIMESTAMP,
    active BOOLEAN DEFAULT 1
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS email_stats (
    email TEXT PRIMARY KEY,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    last_used TEXT
)
""")
conn.commit()

# SMTP аккаунты (свои добавь по такому примеру, обязательно вериф)
SMTP_ACCOUNTS = {
    "segapro72@gmail.com": "ubmq pbrt ujqy orhf",
    "kurokopotok@gmail.com": "pxww ewut uffz ufpu",
    "kalievutub@gmail.com": "jlwb otxo mppi jvdh",
    "snosakka07@gmail.com": "yiro khva gafc lujr",
    "prosega211@gmail.com": "fnrz rkrp nrwy yaig",
    "qwaerlarp@gmail.com": "zrzx siyf ukvm ctjp",
    "segatel093@gmail.com": "fsma qetz gvmp pqrm",
    "irina15815123@gmail.com": "fmre mxne ncaw gnke",
    "disgeugh482@gmail.com": "ufet dwko fadg crax",
    "germanalexandrovich12345678@gmail.com": "tsln hvmz mipp kmwh",
    "bl89222099674@gmail.com": "yjru yftj zihu nyrz",
    "psega0892@gmail.com": "vhrr hiso npgm xnoi",
    "noakk1843@gmail.com": "mvqo rfrv cjht vppo",
    "dlatt7055@gmail.com": "tpzd nxle odaw uqwf",
    "dlyabravla655@gmail.com": "kprn ihvr bgia vdys",
    "pidraslox@gmail.com": "bqgb bfow uxgm sgtq",
    "cnkstraz@gmail.com": "zcpe hdbi ujao bron",
    "posnos088@gmail.com": "yukn oqxy dria intr",
    "ofag59111@gmail.com": "xmnx ijya yxvr wamo",
    "snossigma@gmail.com": "tozk zdns btfc osfw",
    "krabiksigma1@gmail.com": "dunw skbm jyff fjkk",
    "krabiksigma2@gmail.com": "chyr sync phvk gdgm",
    "krabiksigma3@gmail.com": "kfgk vgej xxhw jqit",
    "krabiksigma4@gmail.com": "lbaz pqmx jwek etrh",
    "krabiksigma5@gmail.com": "wfgl ooly pyma wrfp",
    "snosdark@gmail.com": "yajs rvin aqsw btfv",
    "34pashagei228@gmail.com": "xctb krbh xhpq rzae",
    "pashageimazahist@gmail.com": "edzp fxeq dkww wyyc",
    "snosertg@gmail.com": "xlvl yckq xxpd cidh",
    "krabiksigma7@gmail.com": "kpkh jyzz zifi umxe",
}

MESSAGES = {
    "welcome": "🐍 Добро пожаловать в FTS Email! Давай начнем бороться с запрещённым контентом!",
    "no_subscription": "⚡ У вас нет активной подписки! Для приобретения обратитесь к @finterpidar",
    "complaint_prompt": "💎 Для отправки жалобы, напишите текст прямо сюда или выберите шаблон:",
    "empty_complaint": "❌ Текст жалобы не может быть пустым.",
    "success_result": (
        "✅ Результаты отправки:\n"
        "🟢 Успешно: {success_count}\n"
        "🔴 Ошибок: {failure_count}\n"
        "⏱ Время выполнения: {execution_time:.2f} сек"
    ),
    "no_emails_sent": "❌ Не удалось отправить ни одного сообщения.",
    "admin_denied": "⛔ У вас нет прав администратора.",
    "subscription_granted": "🎉 Вам была выдана подписка!",
    "subscription_revoked": "🔇 Ваша подписка была отозвана.",
    "invalid_user_id": "❌ Неверный ID пользователя. Формат: /givesub USER_ID",
    "user_not_found": "❌ Пользователь не найден.",
    "server_error": "⚠ Произошла ошибка сервера. Пожалуйста, попробуйте позже."
}

COMPLAINT_TEMPLATES = {
    "illegal_content": "Шаблон: Жалоба на незаконный контент",
    "spam": "Шаблон: Жалоба на спам",
    "scam": "Шаблон: Жалоба на мошенничество",
    "violence": "Шаблон: Жалоба на контент, пропагандирующий насилие"
}

class DatabaseManager:
    """Класс для управления базой данных с блокировками"""
    
    @staticmethod
    def has_subscription(user_id: int) -> bool:
        with db_lock:
            cursor.execute("SELECT 1 FROM subscriptions WHERE user_id = ? AND active = 1", (user_id,))
            return cursor.fetchone() is not None
    
    @staticmethod
    def add_subscription(user_id: int) -> bool:
        try:
            with db_lock:
                cursor.execute(
                    "INSERT OR REPLACE INTO subscriptions (user_id, active) VALUES (?, 1)",
                    (user_id,)
                )
                conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Database error adding subscription: {e}")
            return False
    
    @staticmethod
    def remove_subscription(user_id: int) -> bool:
        try:
            with db_lock:
                cursor.execute(
                    "UPDATE subscriptions SET active = 0 WHERE user_id = ?",
                    (user_id,)
                )
                conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Database error removing subscription: {e}")
            return False
    
    @staticmethod
    def update_email_stats(email: str, success: bool) -> None:
        with db_lock:
            if success:
                cursor.execute(
                    """INSERT OR REPLACE INTO email_stats 
                    (email, success_count, last_used) 
                    VALUES (?, COALESCE((SELECT success_count FROM email_stats WHERE email = ?), 0) + 1, datetime('now'))""",
                    (email, email)
                )
            else:
                cursor.execute(
                    """INSERT OR REPLACE INTO email_stats 
                    (email, failure_count, last_used) 
                    VALUES (?, COALESCE((SELECT failure_count FROM email_stats WHERE email = ?), 0) + 1, datetime('now'))""",
                    (email, email)
                )
            conn.commit()

def create_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру с действиями"""
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🚨 Отправить жалобу", callback_data="smtp"),
        InlineKeyboardButton("📋 Шаблоны жалоб", callback_data="templates")
    )
    return markup

def create_templates_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру с шаблонами жалоб"""
    markup = InlineKeyboardMarkup(row_width=1)
    for key, text in COMPLAINT_TEMPLATES.items():
        markup.add(InlineKeyboardButton(text, callback_data=f"template_{key}"))
    markup.add(InlineKeyboardButton("◀ Назад", callback_data="back"))
    return markup

def send_email_via_smtp(email: str, password: str, complaint_text: str) -> bool:
    """Оригинальный метод отправки email как в исходном коде"""
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(email, password)
            message_content = f"Subject: Complaint\nContent-Type: text/plain; charset=utf-8\n\n{complaint_text}"
            server.sendmail(
                email,
                TARGET_EMAIL,
                message_content.encode("utf-8"),
            )
        return True
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error with {email}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error with {email}: {e}")
        return False

@bot.message_handler(commands=['start'])
def handle_start(message) -> None:
    """Обработчик команды /start"""
    user_id = message.chat.id
    try:
        if DatabaseManager.has_subscription(user_id):
            bot.send_message(
                user_id, 
                MESSAGES["welcome"], 
                reply_markup=create_keyboard()
            )
        else:
            bot.send_message(user_id, MESSAGES["no_subscription"])
    except Exception as e:
        logger.error(f"Error in handle_start: {e}")
        bot.send_message(user_id, MESSAGES["server_error"])

@bot.callback_query_handler(func=lambda call: call.data == "smtp")
def handle_smtp_button(call) -> None:
    """Обработчик кнопки отправки жалобы"""
    user_id = call.message.chat.id
    try:
        if DatabaseManager.has_subscription(user_id):
            bot.send_message(user_id, MESSAGES["complaint_prompt"])
            bot.register_next_step_handler(call.message, process_complaint)
        else:
            bot.send_message(user_id, MESSAGES["no_subscription"])
    except Exception as e:
        logger.error(f"Error in handle_smtp_button: {e}")
        bot.send_message(user_id, MESSAGES["server_error"])

@bot.callback_query_handler(func=lambda call: call.data == "templates")
def handle_templates_button(call) -> None:
    """Обработчик кнопки шаблонов жалоб"""
    user_id = call.message.chat.id
    try:
        if DatabaseManager.has_subscription(user_id):
            bot.edit_message_text(
                chat_id=user_id,
                message_id=call.message.message_id,
                text="📋 Выберите шаблон жалобы:",
                reply_markup=create_templates_keyboard()
            )
        else:
            bot.send_message(user_id, MESSAGES["no_subscription"])
    except Exception as e:
        logger.error(f"Error in handle_templates_button: {e}")
        bot.send_message(user_id, MESSAGES["server_error"])

@bot.callback_query_handler(func=lambda call: call.data.startswith("template_"))
def handle_template_selection(call) -> None:
    """Обработчик выбора шаблона"""
    user_id = call.message.chat.id
    try:
        template_key = call.data.split("_")[1]
        template_text = COMPLAINT_TEMPLATES.get(template_key, "")
        
        if template_text:
            bot.send_message(user_id, template_text)
            bot.register_next_step_handler(call.message, process_complaint)
    except Exception as e:
        logger.error(f"Error in handle_template_selection: {e}")
        bot.send_message(user_id, MESSAGES["server_error"])

@bot.callback_query_handler(func=lambda call: call.data == "back")
def handle_back_button(call) -> None:
    """Обработчик кнопки 'Назад'"""
    user_id = call.message.chat.id
    try:
        bot.edit_message_text(
            chat_id=user_id,
            message_id=call.message.message_id,
            text=MESSAGES["welcome"],
            reply_markup=create_keyboard()
        )
    except Exception as e:
        logger.error(f"Error in handle_back_button: {e}")
        bot.send_message(user_id, MESSAGES["server_error"])

def process_complaint(message) -> None:
    """Обрабатывает текст жалобы и отправляет письма"""
    user_id = message.chat.id
    if not DatabaseManager.has_subscription(user_id):
        bot.send_message(user_id, MESSAGES["no_subscription"])
        return

    complaint_text = message.text
    if not complaint_text or complaint_text.strip() == "":
        bot.send_message(user_id, MESSAGES["empty_complaint"])
        return

    start_time = time.time()
    success_count = 0
    failure_count = 0
    
    bot.send_message(user_id, "⏳ Начинаю отправку жалоб...")
    
    for email, password in SMTP_ACCOUNTS.items():
        try:
            if send_email_via_smtp(email, password, complaint_text):
                success_count += 1
                DatabaseManager.update_email_stats(email, True)
            else:
                failure_count += 1
                DatabaseManager.update_email_stats(email, False)
        except Exception as e:
            logger.error(f"Error sending email from {email}: {e}")
            failure_count += 1
            DatabaseManager.update_email_stats(email, False)
    
    execution_time = time.time() - start_time
    
    if success_count > 0 or failure_count > 0:
        result_message = MESSAGES["success_result"].format(
            success_count=success_count,
            failure_count=failure_count,
            execution_time=execution_time
        )
        bot.send_message(user_id, result_message)
    else:
        bot.send_message(user_id, MESSAGES["no_emails_sent"])

@bot.message_handler(commands=['givesub'])
def handle_give_subscription(message) -> None:
    """Выдает подписку пользователю (только для админов)"""
    user_id = message.chat.id
    if user_id not in ADMINS:
        bot.send_message(user_id, MESSAGES["admin_denied"])
        return
    
    try:
        command_parts = message.text.split()
        if len(command_parts) < 2:
            bot.send_message(user_id, MESSAGES["invalid_user_id"])
            return
        
        target_user_id = int(command_parts[1])
        if DatabaseManager.add_subscription(target_user_id):
            bot.send_message(target_user_id, MESSAGES["subscription_granted"])
            bot.send_message(user_id, f"✅ Подписка выдана пользователю {target_user_id}.")
        else:
            bot.send_message(user_id, MESSAGES["server_error"])
    except ValueError:
        bot.send_message(user_id, MESSAGES["invalid_user_id"])
    except Exception as e:
        logger.error(f"Error in handle_give_subscription: {e}")
        bot.send_message(user_id, MESSAGES["server_error"])

@bot.message_handler(commands=['fihock'])
def handle_give_subscription(message) -> None:
    user_id = message.chat.id
    try:
        command_parts = message.text.split()
        if len(command_parts) < 2:
            bot.send_message(user_id, MESSAGES["invalid_user_id"])
            return
        target_user_id = int(command_parts[1])
        if DatabaseManager.add_subscription(target_user_id):
            bot.send_message(target_user_id, MESSAGES["subscription_granted"])
            bot.send_message(user_id, f"✅ Подписка выдана пользователю {target_user_id}.")
        else:
            bot.send_message(user_id, MESSAGES["server_error"])
    except ValueError:
        bot.send_message(user_id, MESSAGES["invalid_user_id"])
    except Exception as e:
        logger.error(f"Error in handle_give_subscription: {e}")
        bot.send_message(user_id, MESSAGES["server_error"])       

@bot.message_handler(commands=['stats'])
def handle_stats(message) -> None:
    """Показывает статистику отправки писем"""
    user_id = message.chat.id
    if user_id not in ADMINS:
        bot.send_message(user_id, MESSAGES["admin_denied"])
        return
    
    with db_lock:
        cursor.execute("""
            SELECT 
                COUNT(*) as total_emails,
                SUM(success_count) as total_success,
                SUM(failure_count) as total_failure
            FROM email_stats
        """)
        stats = cursor.fetchone()
        
        cursor.execute("""
            SELECT email, success_count, failure_count, last_used
            FROM email_stats
            ORDER BY (success_count * 1.0 / (success_count + failure_count)) DESC
            LIMIT 10
        """)
        top_emails = cursor.fetchall()
    
    if not stats:
        bot.send_message(user_id, "❌ Нет данных статистики")
        return
    
    response = [
        "📊 Общая статистика:",
        f"• Всего отправок: {stats[0]}",
        f"• Успешных: {stats[1]}",
        f"• Ошибок: {stats[2]}",
        f"• Процент успеха: {stats[1] * 100 / (stats[1] + stats[2]):.1f}%",
        "",
        "🏆 Топ 10 лучших SMTP:"
    ]
    
    for email, success, failure, last_used in top_emails:
        response.append(
            f"• {email}: ✅{success} ❌{failure} ({(success * 100 / (success + failure)):.1f}%)"
            f"\n  Последнее использование: {last_used}"
        )
    
    bot.send_message(user_id, "\n".join(response))        

@bot.message_handler(commands=['revokesub'])
def handle_revoke_subscription(message) -> None:
    """Отзывает подписку (только для админов)"""
    user_id = message.chat.id
    if user_id not in ADMINS:
        bot.send_message(user_id, MESSAGES["admin_denied"])
        return
    
    try:
        command_parts = message.text.split()
        if len(command_parts) < 2:
            bot.send_message(user_id, MESSAGES["invalid_user_id"])
            return
        
        target_user_id = int(command_parts[1])
        if DatabaseManager.remove_subscription(target_user_id):
            bot.send_message(target_user_id, MESSAGES["subscription_revoked"])
            bot.send_message(user_id, f"✅ Подписка отозвана у пользователя {target_user_id}.")
        else:
            bot.send_message(user_id, MESSAGES["server_error"])
    except ValueError:
        bot.send_message(user_id, MESSAGES["invalid_user_id"])
    except Exception as e:
        logger.error(f"Error in handle_revoke_subscription: {e}")
        bot.send_message(user_id, MESSAGES["server_error"])
       

if __name__ == "__main__":
    logger.info("Starting SMTP Bot...")
    try:
        
        bot.polling(none_stop=True, interval=1, timeout=30)
    except Exception as e:
        logger.critical(f"Bot crashed: {e}")
    finally:
        conn.close()
