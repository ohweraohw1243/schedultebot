from sqlalchemy.orm import Session
from database.models import UniversityEvent, MoyKlassEvent

def load_moyklass_data(session: Session, events: list) -> list:
    """
    Загрузка (Load) данных МойКласс в базу.
    Используем логику Upsert (Update or Insert):
    - Возвращает список изменений (переносов занятий)
    """
    added_count = 0
    updated_count = 0
    changes = []
    
    for event_data in events:
        # Ищем, есть ли уже в базе запись с таким ID от 'МойКласс'
        existing = session.query(MoyKlassEvent).filter_by(source_event_id=str(event_data['event_id'])).first()
        
        if existing:
            # Сравниваем даты и время (CDC - Change Data Capture)
            if existing.date != event_data['date'] or existing.start_time != event_data['start_time']:
                changes.append(
                    f"🔄 *Перенос:* {event_data['title']}\n"
                    f"🔻 Было: {existing.date} в {existing.start_time}\n"
                    f"🟢 Стало: {event_data['date']} в {event_data['start_time']}"
                )
            
            # Обновляем
            existing.date = event_data['date']
            existing.start_time = event_data['start_time']
            existing.end_time = event_data['end_time']
            existing.title = event_data['title']
            existing.subject = event_data['subject']
            updated_count += 1
        else:
            # Создаем новую запись
            new_event = MoyKlassEvent(
                source_event_id=str(event_data['event_id']),
                date=event_data['date'],
                start_time=event_data['start_time'],
                end_time=event_data['end_time'],
                title=event_data['title'],
                subject=event_data['subject']
            )
            session.add(new_event)
            added_count += 1
            
    # Сохраняем все изменения транзакцией
    session.commit()
    print(f"[+] БД (МойКласс): Добавлено новых: {added_count}, Обновлено старых: {updated_count}")
    return changes

def load_nstu_data(session: Session, events: list):
    """
    Загрузка (Load) расписания вуза.
    Так как оно статичное (собираем сразу всё на семестр),
    проще всего удалить старое и записать новое (чтобы затереть отмененные пары).
    """
    # Удаляем старые записи
    session.query(UniversityEvent).delete()
    
    # Вставляем новые
    for event_data in events:
        new_event = UniversityEvent(
            day_of_week=event_data['day_of_week'],
            time_range=event_data['time'],
            subject=event_data['subject'],
            room=event_data['room'],
            week_type=event_data['week_type']
        )
        session.add(new_event)
        
    session.commit()
    print(f"[+] БД (ВУЗ): Загружено актуальных пар: {len(events)} (старые удалены)")
