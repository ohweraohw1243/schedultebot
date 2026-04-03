from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from icalendar import Calendar, Event
import pytz
from datetime import datetime, timedelta

from database.setup import get_session
from database.models import MoyKlassEvent, UniversityEvent

app = FastAPI(title="Schedule Calendar API")
# Временная зона Новосибирска для правильной синхронизации с расписанием
TZ = pytz.timezone('Asia/Novosibirsk')
# МойКласс отдает расписание по Москве
MOSCOW_TZ = pytz.timezone('Europe/Moscow')

# Словарь для перевода дней недели из расписания ВУЗа
day_mapping = {
    'пн': 0,
    'вт': 1,
    'ср': 2,
    'чт': 3,
    'пт': 4,
    'сб': 5,
    'вс': 6
}

@app.get("/my_schedule.ics", response_class=PlainTextResponse)
def get_calendar():
    """
    Генератор файла .ics для Apple Calendar.
    Собирает данные из базы и превращает в события календаря.
    """
    session = get_session()
    cal = Calendar()
    cal.add('prodid', '-//Dan Schedule Bot//')
    cal.add('version', '2.0')
    
    # 1. События МойКласс (Они с точными датами)
    moyklass_events = session.query(MoyKlassEvent).all()
    for mk in moyklass_events:
        event = Event()
        # Парсим дату и время (2026-04-03 17:00)
        dt_start = datetime.strptime(f"{mk.date} {mk.start_time}", "%Y-%m-%d %H:%M")
        dt_end = datetime.strptime(f"{mk.date} {mk.end_time}", "%Y-%m-%d %H:%M")
        
        # Привязываем московскую временную зону (Apple Calendar потом сам переконвертирует ее в локальное время телефона)
        dt_start = MOSCOW_TZ.localize(dt_start)
        dt_end = MOSCOW_TZ.localize(dt_end)
        
        event.add('summary', f"👨‍🏫 {mk.title}") # Добавляем эмодзи для красоты
        event.add('dtstart', dt_start)
        event.add('dtend', dt_end)
        event.add('uid', f"moyklass_{mk.source_event_id}@daniil.schedule")
        
        cal.add_component(event)

    # 2. События Университета (Сложный генератор)
    # Так как пары ВУЗа идут каждую неделю (или чет/нечет),
    # мы сгенерируем конкретные дни на 30 дней вперед от текущей даты.
    univer_events = session.query(UniversityEvent).all()
    today_dt = datetime.now()
    
    for i in range(30): # Проецируем на 30 дней вперед
        target_date = today_dt + timedelta(days=i)
        target_weekday = target_date.weekday() # 0-Mon, 1-Tue, etc.
        
        for un in univer_events:
            if day_mapping.get(un.day_of_week) == target_weekday:
                # В будущем можно добавить проверку по четным/нечетным неделям через `un.week_type` 
                # (Если сейчас четная неделя, а пара по нечетной - пропускать)
                # Пока выводим все пары с пометкой типа недели в заголовке
                
                start_h, start_m = map(int, un.time_range.split('-')[0].split(':'))
                end_h, end_m = map(int, un.time_range.split('-')[1].split(':'))
                
                dt_start = TZ.localize(target_date.replace(hour=start_h, minute=start_m, second=0, microsecond=0))
                dt_end = TZ.localize(target_date.replace(hour=end_h, minute=end_m, second=0, microsecond=0))
                
                event = Event()
                event.add('summary', f"🎓 {un.subject} [{un.week_type}]")
                event.add('location', un.room)
                event.add('dtstart', dt_start)
                event.add('dtend', dt_end)
                event.add('uid', f"nstu_{un.id}_{target_date.strftime('%Y%m%d')}@daniil.schedule")
                
                cal.add_component(event)
                
    session.close()
    
    # Возвращаем строковое представление файла:
    return cal.to_ical().decode()

if __name__ == "__main__":
    import uvicorn
    # Запуск сервера локально на порту 8000
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
