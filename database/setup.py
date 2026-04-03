import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Импортируем Базовый класс и все описывающие модели базы данных
from database.models import Base, UniversityEvent, MoyKlassEvent

# Получаем абсолютный путь к папке проекта (чтобы файл schedule.db создался именно там)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'schedule.db')

# Создаем движок базы данных SQLite (echo=True будет печатать SQL-запросы - удобно для обучения, но потом выключим)
engine = create_engine(f'sqlite:///{DB_PATH}', echo=False)

# Создаем фабрику сессий (через нее мы будем "общаться" с базой)
SessionLocal = sessionmaker(bind=engine)

def get_session():
    """Функция для удобного получения сессии базы данных"""
    return SessionLocal()

def init_db():
    """Создает все таблицы, если их еще нет"""
    Base.metadata.create_all(engine)
    print(f"[+] База данных (SQLite) инициализирована: {DB_PATH}")
    print("[+] Таблицы university_events и moyklass_events готовы к работе!")

if __name__ == "__main__":
    init_db()
