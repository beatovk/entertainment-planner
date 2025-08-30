# 🚀 Система парсинга TimeOut

Универсальная система для автоматического извлечения мест из статей TimeOut с сохранением в базу данных.

## ✨ Возможности

- **Автоматический парсинг** статей TimeOut
- **Умная фильтрация** технического HTML и служебного контента
- **Извлечение данных** о местах (название, описание, изображение)
- **Интеграция с БД** raw.db для дальнейшей обработки
- **Отслеживание сессий** парсинга и статистики
- **Поддержка различных форматов** статей

## 📁 Структура файлов

```
├── universal_parser.py           # Универсальный парсер для разных сайтов
├── improved_parser.py            # Улучшенный парсер TimeOut
├── clean_timeout_parser.py       # Очищенный парсер с фильтрацией
├── timeout_integration.py        # Базовая интеграция с БД
├── final_timeout_integration.py  # Финальная интеграция
├── demo_timeout_system.py        # Демонстрационный скрипт
└── README_TIMEOUT_PARSER.md      # Этот файл
```

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
pip3 install beautifulsoup4 requests
```

### 2. Базовое использование

```bash
# Парсинг статьи и сохранение в БД
python3 final_timeout_integration.py

# Только парсинг без сохранения
python3 clean_timeout_parser.py

# Демонстрация всех возможностей
python3 demo_timeout_system.py
```

### 3. Программное использование

```python
from final_timeout_integration import FinalTimeOutIntegration

# Создаем интеграцию
integration = FinalTimeOutIntegration()

# Парсим статью
url = "https://www.timeout.com/bangkok/restaurants/bangkoks-best-new-cafes-of-2025"
result = integration.parse_and_save(url, limit=20)

if result['success']:
    print(f"Сохранено {result['places_count']} мест")
```

## 🔧 Конфигурация

### Параметры парсинга

- `limit` - максимальное количество мест для извлечения
- `source` - источник данных (по умолчанию 'timeout_clean')
- `db_path` - путь к базе данных (по умолчанию 'raw.db')

### Настройка фильтрации

В `clean_timeout_parser.py` можно настроить:

- Технические классы для исключения
- Паттерны валидных названий мест
- Служебные слова для фильтрации
- Валидацию изображений

## 📊 Структура базы данных

### Таблица `raw_places`

```sql
CREATE TABLE raw_places (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,           -- Источник данных
    source_url TEXT,                -- URL статьи
    name_raw TEXT NOT NULL,         -- Название места
    description_raw TEXT,           -- Описание
    address_raw TEXT,               -- Адрес (если есть)
    raw_json TEXT,                  -- Полные данные в JSON
    fetched_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

### Таблица `parsing_sessions`

```sql
CREATE TABLE parsing_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_url TEXT NOT NULL,       -- URL статьи
    places_found INTEGER,           -- Количество найденных мест
    started_at TIMESTAMP,           -- Время начала
    completed_at TIMESTAMP,         -- Время завершения
    status TEXT                     -- Статус: running/completed/failed
);
```

## 🎯 Примеры использования

### Парсинг конкретной статьи

```python
from clean_timeout_parser import CleanTimeOutParser

parser = CleanTimeOutParser()
places = parser.parse_timeout_article(
    "https://www.timeout.com/bangkok/restaurants/bangkoks-best-new-cafes-of-2025",
    limit=10
)

for place in places:
    print(f"📍 {place['title']}")
    if place['image_url']:
        print(f"   🖼️  {place['image_url']}")
```

### Получение статистики

```python
from final_timeout_integration import FinalTimeOutIntegration

integration = FinalTimeOutIntegration()

# Общее количество мест
total = integration.get_places_count()
print(f"Всего мест: {total}")

# Количество очищенных мест TimeOut
clean = integration.get_clean_places_count()
print(f"Очищенных мест TimeOut: {clean}")

# История парсинга
history = integration.get_parsing_history()
for session in history:
    print(f"Сессия {session['id']}: {session['places_found']} мест")
```

## 🔍 Алгоритм работы

1. **Загрузка HTML** - получение содержимого статьи
2. **Очистка HTML** - удаление технических элементов
3. **Поиск заголовков** - извлечение потенциальных названий мест
4. **Валидация** - проверка на валидность названия
5. **Извлечение данных** - поиск описания и изображения
6. **Фильтрация** - очистка и валидация результатов
7. **Сохранение в БД** - запись с проверкой дубликатов

## 🛡️ Фильтрация контента

### Исключаемые элементы

- HTML теги и атрибуты
- JavaScript код
- CSS стили
- Рекламные блоки
- Социальные кнопки
- Навигационные элементы
- Служебные заголовки

### Валидация названий

- Минимальная длина: 3 символа
- Максимальная длина: 20 символов
- Должны содержать буквы
- Не должны быть техническими
- Должны соответствовать паттернам мест

## 📈 Мониторинг и статистика

### Метрики парсинга

- Количество найденных мест
- Время выполнения
- Статус сессий
- Источники данных
- Уникальность записей

### Отслеживание ошибок

- Логирование ошибок парсинга
- Статус сессий (running/completed/failed)
- Детализация проблем

## 🔧 Расширение функциональности

### Добавление новых источников

1. Создайте новый класс парсера
2. Реализуйте методы извлечения данных
3. Добавьте специфичную фильтрацию
4. Интегрируйте с системой БД

### Кастомизация фильтров

```python
def _is_valid_place_title(self, text: str) -> bool:
    # Добавьте свои правила валидации
    custom_patterns = [
        r'ваш_паттерн',
        r'другой_паттерн'
    ]
    
    for pattern in custom_patterns:
        if re.search(pattern, text):
            return True
    
    return False
```

## 🚨 Ограничения и известные проблемы

- **SSL предупреждения** - связаны с версией urllib3
- **Блокировка сайтов** - некоторые сайты могут блокировать парсеры
- **Изменение структуры** - сайты могут менять HTML структуру
- **Rate limiting** - необходимо соблюдать разумные интервалы между запросами

## 🤝 Поддержка и развитие

### Рекомендации по улучшению

1. **Добавить retry логику** для обработки временных ошибок
2. **Реализовать прокси ротацию** для обхода блокировок
3. **Добавить асинхронность** для повышения производительности
4. **Расширить валидацию** изображений и описаний
5. **Добавить поддержку** других сайтов о местах

### Тестирование

```bash
# Запуск всех тестов
python3 -m pytest tests/

# Тестирование конкретного парсера
python3 clean_timeout_parser.py

# Проверка интеграции
python3 final_timeout_integration.py
```

## 📝 Лицензия

Этот проект создан для демонстрации возможностей парсинга веб-сайтов. Используйте ответственно и соблюдайте robots.txt и условия использования сайтов.

## 🎉 Заключение

Система парсинга TimeOut готова к использованию и может быть легко адаптирована для других сайтов. Основные компоненты:

- ✅ **Универсальный парсер** для разных форматов
- ✅ **Умная фильтрация** технического контента  
- ✅ **Интеграция с БД** для хранения данных
- ✅ **Мониторинг** и статистика парсинга
- ✅ **Расширяемость** для новых источников

Для начала работы запустите `python3 demo_timeout_system.py` для демонстрации всех возможностей!
