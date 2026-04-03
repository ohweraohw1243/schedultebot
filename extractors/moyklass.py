import requests
from datetime import datetime, timedelta

def fetch_moyklass_schedule(date_from: str, date_to: str) -> list:
    """
    Экстрактор данных (Extract) из скрытого API МойКласс.
    Мы параметризовали даты, чтобы скрипт мог сам решать, за какой период брать данные (например, на неделю вперед).
    """
    url = 'https://app.moyklass.com/api/crm/lesson/schedule'
    
    # Параметры запроса (мы вынесли даты в аргументы функции, чтобы было гибко)
    params = {
        'archive_classes_search': 'true',
        'archive_filial_search': 'true',
        'dateFrom': date_from,
        'dateTo': date_to,
        'filial_id': ['39082', '0'],
        'full_filial_ids': ['39082', '0'],
        'limit': '50',
        'offset': '0',
        'records': 'true',
        'room_id': '58177',
        'teacher_id': '165882',
        'type': 'all',
        'user_records_only': 'false'
    }
    
    # Твои куки для авторизации (в реальном проекте мы вынесем их в файл .env для безопасности)
    cookies = {
        'version': '3.3.0',
        'device_id': 'e5335c56-f064-43ec-bc82-ca2a3d476995',
        'device_id.sig': 'CQ8HX1-P_bUSmkvkajP1Jz7EAhA',
        'connect.sid': 's%3AEHIuEM9_YrAwg2M9rHqWGqSn150xQE-n.lFXWwFeS%2B%2Bc72Ge8ZhBg3ll3nsrPw%2B7oc5BaTcNd8rI'
    }
    
    # Основные заголовки, чтобы сервер думал, что мы реальный браузер
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
        'Referer': 'https://app.moyklass.com/schedule/list'
    }
    
    print(f"[*] Выгружаю расписание с {date_from} по {date_to}...")
    response = requests.get(url, params=params, cookies=cookies, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"[!] Ошибка доступа: {response.status_code}")
        response.raise_for_status()

def transform_moyklass_data(raw_data: list) -> list:
    """
    Transform-шаг. Берем сырой JSON и вытаскиваем только то, что нужно
    для нашего календаря: ID, дата, время, имя ученика, предмет.
    """
    cleaned_events = []
    
    for lesson in raw_data:
        event_id = lesson.get('id')
        date = lesson.get('date')
        start_time = lesson.get('begin_time')
        end_time = lesson.get('end_time')
        
        # Предмет хранится в Class -> name
        subject = "Без названия"
        if lesson.get('Class') and lesson.get('Class').get('name'):
             subject = lesson['Class']['name']
             
        # Извлекаем студентов
        students = []
        if lesson.get('LessonRecords'):
            for record in lesson['LessonRecords']:
                if record.get('User') and record['User'].get('name'):
                    students.append(record['User']['name'])
                    
        # Формируем итоговое красивое название
        student_str = ", ".join(students) if students else ""
        title = f"{subject} ({student_str})"
        
        cleaned_events.append({
            'source': 'moyklass',
            'event_id': event_id,
            'title': title,
            'date': date,
            'start_time': start_time,
            'end_time': end_time,
            'subject': subject
        })
        
    return cleaned_events

if __name__ == "__main__":
    # Тестовый запуск: берем расписание на ближайшие 7 дней
    today = datetime.now()
    next_week = today + timedelta(days=7)
    
    raw_data = fetch_moyklass_schedule(
        today.strftime('%Y-%m-%d'), 
        next_week.strftime('%Y-%m-%d')
    )
    
    if raw_data:
        print(f"[+] Успешно скачано занятий: {len(raw_data)}")
        
        # Запускаем Transform
        clean_data = transform_moyklass_data(raw_data)
        
        print("\n[+] Очищенные данные для календаря (первые 3 шт):")
        for event in clean_data[:3]:
            print(f"- {event['date']} {event['start_time']}-{event['end_time']} | {event['title']}")
