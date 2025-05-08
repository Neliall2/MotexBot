import requests
import logging
from config import Config
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import time
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class BitrixAPI:
    @staticmethod
    def _create_session():
        session = requests.Session()
        retry_strategy = Retry(
            total=3,  # количество попыток
            backoff_factor=1,  # время ожидания между попытками
            status_forcelist=[500, 502, 503, 504]  # коды ошибок для повторных попыток
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    @staticmethod
    def create_task(task_type, data):
        try:
            # Получаем ID проекта для данного типа задачи
            project_id = Config.PROJECT_IDS.get(task_type)
            if not project_id:
                logger.error(f'Project ID not found for task type: {task_type}')
                return {'error': f'Project ID not found for task type: {task_type}'}

            logger.info(f"=== Начало создания задачи ===")
            logger.info(f"Тип задачи: {task_type}")
            logger.info(f"ID проекта: {project_id}")
            logger.info(f"Входные данные: {data}")

            # Формируем описание задачи
            description = ""
            description += f"Клиент: {data['client_code']}\n"
            description += f"Маршрут: {data['route']}\n"

            if task_type != 'info':
                description += "\nТовары:\n"
                for idx, item in enumerate(data['articles'], 1):
                    description += f"{idx}. Артикул: {item['article']}\n   Количество: {item['quantity']}\n"
                description += f"\nДокумент: {data['document_number']}\n"

            description += f"Комментарий: {data['comment']}"

            # Формируем название задачи
            title = data.get('title', Config.TASK_TITLES[task_type])
            if task_type == 'claim' and data.get('claim_type') == 'Недовоз':
                title = f"Претензия {data['claim_type']}"

            # Устанавливаем крайний срок в зависимости от типа задачи
            now = datetime.now()
            
            if task_type == 'info':
                deadline = now + timedelta(days=1)  # 1 день для информационных задач
            else:
                deadline = now + timedelta(days=3)   # 3 дня для претензий и отказов
            
            # Форматируем дату в формате, который ожидает Bitrix24
            deadline_str = deadline.strftime('%Y-%m-%d %H:%M:%S')

            logger.info(f"Название задачи: {title}")
            logger.info(f"Описание задачи: {description}")
            logger.info(f"Крайний срок: {deadline_str}")
            logger.info(f"Ответственный: {Config.RESPONSIBLE_ID}")

            # Создаем задачу
            session = BitrixAPI._create_session()
            start_time = time.time()
            
            try:
                # Создаем задачу
                params = {
                    "fields[TITLE]": title,
                    "fields[DESCRIPTION]": description,
                    "fields[RESPONSIBLE_ID]": int(Config.RESPONSIBLE_ID),
                    "fields[DEADLINE]": deadline_str,  # Крайний срок
                    "fields[GROUP_ID]": int(project_id)  # ID проекта
                }

                logger.info(f"Параметры создания задачи: {params}")

                # Используем метод tasks.task.add для создания задачи
                response = session.post(
                    f"{Config.BITRIX_WEBHOOK}tasks.task.add",
                    data=params,
                    headers={'Content-Type': 'application/x-www-form-urlencoded'},
                    timeout=15
                )
                
                logger.info(f"Статус ответа: {response.status_code}")
                logger.info(f"Ответ API: {response.text}")
                
                result = response.json()
                
                # Логируем время выполнения запроса
                execution_time = time.time() - start_time
                logger.info(f"Время создания задачи: {execution_time:.2f} секунд")
                
                if response.status_code == 200:
                    if 'result' in result:
                        task_id = result['result']['task']['id']
                        logger.info(f"=== Задача успешно создана ===")
                        logger.info(f"ID задачи: {task_id}")
                        logger.info(f"Тип задачи: {task_type}")
                        logger.info(f"Проект: {project_id}")
                        return {'success': True, 'task_id': task_id}
                    elif 'error' in result:
                        error_msg = result['error']
                        logger.error(f"Ошибка API Битрикс24: {error_msg}")
                        return {'error': f'Bitrix API error: {error_msg}'}
                    else:
                        logger.error(f"Неожиданный формат ответа: {result}")
                        return {'error': 'Unexpected response format from Bitrix API'}
                else:
                    error_msg = result.get('error_description', 'Unknown error')
                    logger.error(f"Ошибка создания задачи. Статус: {response.status_code}, Ошибка: {error_msg}")
                    return {'error': f'Failed to create task: {error_msg}'}

            except requests.exceptions.Timeout:
                logger.error("Таймаут запроса при создании задачи")
                return {'error': 'Request timeout'}
            except requests.exceptions.RequestException as e:
                logger.error(f"Ошибка запроса: {str(e)}")
                return {'error': 'Connection error'}
            except ValueError as e:
                logger.error(f"Ошибка парсинга JSON: {str(e)}")
                return {'error': 'Invalid response from server'}
            finally:
                session.close()

        except Exception as e:
            logger.error(f"Непредвиденная ошибка при создании задачи: {str(e)}")
            return {'error': 'Internal server error'}