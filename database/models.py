from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

# Базовый класс для всех моделей
Base = declarative_base()

class UniversityEvent(Base):
    """
    Таблица для расписания Вуза.
    Здесь описываются РЕГУЛЯРНЫЕ правила, а не конкретные даты.
    """
    __tablename__ = 'university_events'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    day_of_week = Column(String, nullable=False) # 'пн', 'вт', 'ср'...
    time_range = Column(String, nullable=False)  # '08:30-10:00'
    subject = Column(String, nullable=False)     # Управление проектами
    room = Column(String)                        # 6-811
    week_type = Column(String, nullable=False)   # 'all', 'по чётным', 'недели 4 8'

class MoyKlassEvent(Base):
    """
    Таблица для учеников МойКласс.
    Здесь описываются КОНКРЕТНЫЕ события (занятия на конкретную дату).
    """
    __tablename__ = 'moyklass_events'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    # Сохраняем оригинальный ID из "МойКласс", 
    # чтобы не добавлять одно занятие несколько раз (уникальность).
    source_event_id = Column(String, unique=True, nullable=False)
    date = Column(String, nullable=False)        # 2026-04-03
    start_time = Column(String, nullable=False)  # 17:00
    end_time = Column(String, nullable=False)    # 17:50
    title = Column(String, nullable=False)       # Математика (Иванов Иван)
    subject = Column(String)                     # Математика (для поиска)
