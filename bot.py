import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Импортируем нашу функцию пайплайна
from main import run_etl_pipeline

# Загружаем переменные из .env файла
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Инициализируем бота и диспетчер
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Инициализируем планировщик (Cron-like scheduler)
scheduler = AsyncIOScheduler(timezone="Asia/Novosibirsk")

# Временный файл для хранения ID админа (тебя), чтобы бот знал, кому пушить алерты
ADMIN_FILE = "admin_id.txt"

def get_admin_id():
    """Считываем Chat ID из файла"""
    if os.path.exists(ADMIN_FILE):
        with open(ADMIN_FILE, "r") as f:
            return int(f.read().strip())
    return None

async def scheduled_etl_job():
    """Фоновая задача (будет выполняться каждые 30 минут)"""
    print("⏰ [Сработал Scheduler] Запускаю фоновое обновление расписания...")
    try:
        # Выполняем наш ETL и ловим список изменений (CDC)
        changes = run_etl_pipeline()
        
        # Если есть изменения и мы знаем, кому их слать - отправляем пуш-уведомление!
        admin_id = get_admin_id()
        if changes and admin_id:
            alert_text = "🚨 *ВНИМАНИЕ! ИЗМЕНЕНИЯ В РАСПИСАНИИ!*\n\n"
            alert_text += "\n\n".join(changes)
            await bot.send_message(admin_id, alert_text, parse_mode="Markdown")
            print("✅ Алерты отправлены!")
    except Exception as e:
        print(f"❌ Ошибка в фоновом обновлении: {e}")

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Ответ на команду /start и сохранение твоего ID"""
    user_id = message.from_user.id
    # Записываем твой ID, чтобы бот мог сам писать тебе алерты
    with open(ADMIN_FILE, "w") as f:
        f.write(str(user_id))
        
    text = (
        "Привет! Я бот для управления твоим расписанием. 🗓\n\n"
        "✅ Я запомнил твой контакт! Теперь, если расписание изменится, я пришлю тебе пуш-уведомление.\n\n"
        "Я буду сам проверять расписание каждые 30 минут. "
        "Но ты можешь принудительно обновить его по кнопке ниже."
    )
    await message.answer(text, reply_markup=menu_keyboard)

# Создаем клавиатуру, которая всегда будет внизу
menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔄 Обновить расписание")],
        [KeyboardButton(text="🍎 Настройка календаря")]
    ],
    resize_keyboard=True
)

@dp.message(F.text == "🔄 Обновить расписание")
async def update_schedule(message: types.Message):
    """Обработчик кнопки Обновить"""
    # Сначала отправляем сообщение, что процесс пошел
    status_msg = await message.answer("⏳ Запускаю сбор данных... Это может занять пару секунд.")
    
    try:
        changes = run_etl_pipeline()
        
        # Если есть изменения, сообщим о них прямо в чате
        if changes:
            response_text = "✅ Расписание обновлено! Есть изменения:\n\n" + "\n\n".join(changes)
        else:
            response_text = "✅ Расписание проверено. Изменений нет (всё стабильно)."
        
        # Редактируем сообщение об успехе
        await status_msg.edit_text(response_text, parse_mode="Markdown")
    except Exception as e:
        await status_msg.edit_text(f"❌ Произошла ошибка при обновлении:\n{e}")

@dp.message(F.text == "🍎 Настройка календаря")
async def send_calendar_info(message: types.Message):
    """Инструкция, как подключить Apple Calendar"""
    text = (
        "Так как сервер пока запущен локально на твоем макбуке, "
        "добавить его в Apple Calendar можно по этой ссылке:\n\n"
        "`http://127.0.0.1:8000/my_schedule.ics`\n\n"
        "Вставь её в *Файл -> Новая подписка на календарь* (на Mac)."
    )
    await message.answer(text, parse_mode="Markdown")

async def main():
    print("🤖 Бот запущен! Инициализация APScheduler...")
    
    # Добавляем задачу проверять расписание каждые 30 минут
    scheduler.add_job(scheduled_etl_job, "interval", minutes=30)
    scheduler.start()
    
    print("✅ Планировщик активен. Ожидание сообщений...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
