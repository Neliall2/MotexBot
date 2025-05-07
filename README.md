# MotBot Logistic

Telegram бот для обработки отказов, претензий и информационных сообщений от водителей.

## Структура проекта

```
motbot/
├── bot.py              # Основной файл бота
├── bitrix_api.py       # API для работы с Bitrix24
├── config.py           # Конфигурация
├── requirements.txt    # Зависимости
├── Dockerfile         # Конфигурация Docker
├── .dockerignore      # Исключения для Docker
├── .gitignore         # Исключения для Git
└── README.md          # Документация
```

## Установка и запуск

1. Клонируйте репозиторий:
```bash
git clone https://github.com/your-username/motbot.git
cd motbot
```

2. Создайте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # для Linux/Mac
venv\Scripts\activate     # для Windows
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Создайте файл .env с настройками:
```
BOT_TOKEN=your_bot_token
BITRIX_WEBHOOK=your_webhook_url
RESPONSIBLE_ID=your_responsible_id
REFUSAL_PROJECT_ID=your_refusal_project_id
CLAIM_PROJECT_ID=your_claim_project_id
INFO_PROJECT_ID=your_info_project_id
```

5. Запустите бота:
```bash
python bot.py
```

## Функциональность

- Обработка отказов от доставки
- Обработка претензий (недовоз, повреждение, несоответствие)
- Обработка информационных сообщений
- Автоматическое создание задач в Bitrix24
- Установка крайних сроков для задач
- Привязка задач к проектам 