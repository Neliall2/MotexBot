import os
from dotenv import load_dotenv

load_dotenv()

# Конфигурация бота
BOT_TOKEN = os.getenv('BOT_TOKEN')
BITRIX_WEBHOOK = os.getenv('BITRIX_WEBHOOK')
RESPONSIBLE_ID = os.getenv('RESPONSIBLE_ID')

# ID проектов для разных типов задач
PROJECT_IDS = {
    'refusal': os.getenv('REFUSAL_PROJECT_ID'),
    'claim': os.getenv('CLAIM_PROJECT_ID'),
    'info': os.getenv('INFO_PROJECT_ID')
}

# Названия задач
TASK_TITLES = {
    'refusal': 'Отказ от доставки',
    'claim': 'Претензия',
    'info': 'Информация от водителя'
}

# Состояния для обработки отказов
REFUSAL_STATES = {
    'CLIENT_CODE': 1,
    'ROUTE': 2,
    'ARTICLE': 3,
    'QUANTITY': 4,
    'DOCUMENT': 5,
    'COMMENT': 6
}

# Состояния для обработки претензий
CLAIM_STATES = {
    'CLIENT_CODE': 1,
    'ROUTE': 2,
    'CLAIM_TYPE': 3,
    'ARTICLE': 4,
    'QUANTITY': 5,
    'DOCUMENT': 6,
    'COMMENT': 7
}

# Состояния для обработки информации
INFO_STATES = {
    'CLIENT_CODE': 1,
    'ROUTE': 2,
    'COMMENT': 3
}

# Типы претензий
CLAIM_TYPES = ['Недовоз', 'Повреждение', 'Несоответствие']

class Config:
    BOT_TOKEN = BOT_TOKEN
    BITRIX_WEBHOOK = BITRIX_WEBHOOK
    RESPONSIBLE_ID = RESPONSIBLE_ID
    PROJECT_IDS = PROJECT_IDS
    TASK_TITLES = TASK_TITLES

    STATES = {
        'START': 0,
        'CLIENT_CODE': 1,
        'ROUTE': 2,
        'ARTICLES': 3,
        'QUANTITY': 4,
        'DOCUMENT_NUMBER': 5,
        'COMMENT': 6,
        'CLAIM_TYPE': 7,
        'INFO_CLIENT_CODE': 8,
        'INFO_ROUTE': 9,
        'INFO_COMMENT': 10
    }