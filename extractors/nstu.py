import requests
from bs4 import BeautifulSoup

def fetch_nstu_schedule(group: str) -> list:
    """
    Экстрактор данных (Extract & Transform) из расписания НГТУ.
    Скрейпит HTML таблицу и превращает её в список структурированных занятий.
    """
    url = f"https://www.fb.nstu.ru/study_process/schedule/schedule_classes/schedule?group={group}&print=true"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36'
    }
    
    print(f"[*] Скачиваю расписание вуза для группы {group}...")
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, "lxml") # lxml работает быстрее
    
    events = []
    
    # Находим главную таблицу
    table_body = soup.find('div', class_='schedule__table-body')
    if not table_body:
        print("[!] Таблица расписания не найдена!")
        return events
        
    current_day = None
    
    # Идем по строкам дней/времени
    for row in table_body.find_all('div', class_='schedule__table-row', recursive=False):
        day_cell = row.find('div', class_='schedule__table-day')
        
        # Если это новая строка с днем недели
        if day_cell:
            current_day = day_cell.text.strip()
            
        # Теперь ищем блоки времени внутри этого дня
        time_rows = row.find_all('div', class_='schedule__table-row')
        for time_row in time_rows:
            time_cell = time_row.find('div', class_='schedule__table-time')
            if not time_cell:
                continue
                
            time_str = time_cell.text.strip()
            
            # Проверяем, есть ли названия предметов здесь
            items = time_row.find_all('div', class_='schedule__table-item')
            # Аудитории
            class_cells = time_row.find_all('div', class_='schedule__table-class')
            
            for item, class_cell in zip(items, class_cells):
                # Извлекаем все текстовые узлы внутри ячейки предмета
                texts = [t.strip() for t in item.stripped_strings if t.strip() and t.strip() != '\xa0']
                if not texts:
                    continue
                
                # Текст может выглядеть так: ['недели 4 8 12 16', 'Управление проектами в цифровой среде', '· Драгунова Е. В.', 'Практика 6-811']
                # или ['по чётным', 'Основы здорового питания и этикета', ...]
                
                week_type = "all"
                subject_parts = []
                
                for t in texts:
                    t_lower = t.lower()
                    if t_lower.startswith('недели') or 'чётным' in t_lower or 'нечетным' in t_lower or 'нечётным' in t_lower:
                        week_type = t
                    else:
                        subject_parts.append(t)
                        
                subject = " ".join(subject_parts).replace('\n', ' ').strip()
                room = class_cell.text.replace('\xa0', '').strip()
                
                # Добавляем событие в список
                events.append({
                    'source': 'nstu',
                    'day_of_week': current_day,
                    'time': time_str,
                    'subject': subject,
                    'room': room,
                    'week_type': week_type
                })
                
    return events


if __name__ == "__main__":
    group_name = "%D0%A4%D0%91%D0%98-34" # ФБИ-34 в URL формате
    schedule_data = fetch_nstu_schedule(group_name)
    
    if schedule_data:
        print(f"[+] Найдено занятий в вузе: {len(schedule_data)}\n")
        
        print("[+] Очищенные (Transform) данные для загрузки в БД:")
        for event in schedule_data[:10]: # Покажем первые 10
            print(f"- {event['day_of_week']} {event['time']} [{event['week_type']}] | {event['subject']} (Ауд: {event['room']})")
