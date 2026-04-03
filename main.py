from datetime import datetime, timedelta

# Импортируем инфраструктуру базы
from database.setup import init_db, get_session
from database.loader import load_moyklass_data, load_nstu_data

# Импортируем экстракторы (Сбор и трансформацию)
from extractors.moyklass import fetch_moyklass_schedule, transform_moyklass_data
from extractors.nstu import fetch_nstu_schedule

def run_etl_pipeline() -> list:
    """
    Главная функция - Оркестратор ETL (Extract -> Transform -> Load)
    Возвращает список изменений (измененных занятий).
    """
    print("🚀 Старт ETL-пайплайна: Сбор расписания...\n")
    
    # 1. Подключение к БД
    init_db()
    session = get_session()
    
    # 2. Обработка МойКласс (События на ближайшие 14 дней для надежности)
    today = datetime.now()
    two_weeks_later = today + timedelta(days=14)
    date_from = today.strftime('%Y-%m-%d')
    date_to = two_weeks_later.strftime('%Y-%m-%d')
    
    changes = []
    
    print(f"\n--- [1] МойКласс (С {date_from} по {date_to}) ---")
    raw_mk = fetch_moyklass_schedule(date_from, date_to)
    
    if raw_mk:
        # Transform
        clean_mk = transform_moyklass_data(raw_mk)
        # Load (тут ловим изменения!)
        changes = load_moyklass_data(session, clean_mk)
        
    # 3. Обработка НГТУ (Сбор статики)
    print("\n--- [2] ВУЗ (НГТУ - ФБИ-34) ---")
    group_name = "%D0%A4%D0%91%D0%98-34"
    # Extract & Transform (он в одном месте у нас)
    clean_nstu = fetch_nstu_schedule(group_name)
    
    if clean_nstu:
        # Load
        load_nstu_data(session, clean_nstu)
        
    # Завершаем соединение
    session.close()
    print("\n✅ ETL-пайплайн успешно завершен!")
    return changes

if __name__ == "__main__":
    run_etl_pipeline()
