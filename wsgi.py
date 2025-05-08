from bot import app, main, stop_event
import os
import asyncio
from threading import Thread
import nest_asyncio
import logging
import sys
from datetime import datetime
import time
import tempfile
import signal
import httpx

# Настройка логирования
log_dir = os.path.join(tempfile.gettempdir(), 'app_logs')
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(log_dir, f'app_{datetime.now().strftime("%Y%m%d")}.log'), encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

# Разрешаем вложенные event loops
nest_asyncio.apply()

def run_flask():
    try:
        port = int(os.environ.get('PORT', 8080))
        logger.info(f"Запуск Flask на порту {port}")
        app.run(host='0.0.0.0', port=port)
    except Exception as e:
        logger.error(f"Ошибка Flask: {e}", exc_info=True)

async def health_check():
    """Периодическая проверка состояния приложения"""
    while True:
        try:
            logger.info("Проверка состояния приложения...")
            # Здесь можно добавить проверку соединения с базой данных
            # или другие проверки состояния
            await asyncio.sleep(300)  # Проверка каждые 5 минут
        except Exception as e:
            logger.error(f"Ошибка при проверке состояния: {e}", exc_info=True)
            await asyncio.sleep(60)  # При ошибке ждем минуту перед следующей попыткой

async def keep_alive():
    """Функция для поддержания активности приложения"""
    while not stop_event.is_set():
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get('https://motexbot.onrender.com/')
                logger.info(f"Keep-alive request sent at {datetime.now()}, status: {response.status_code}")
        except Exception as e:
            logger.error(f"Error in keep-alive request: {e}")
        await asyncio.sleep(300)  # Отправляем запрос каждые 5 минут

async def run_all():
    # Запускаем Flask в отдельном потоке
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    logger.info("Flask запущен в отдельном потоке")
    
    # Запускаем проверку состояния
    health_check_task = asyncio.create_task(health_check())
    
    # Запускаем keep-alive для Render
    keep_alive_task = asyncio.create_task(keep_alive())
    
    try:
        logger.info("Запуск бота...")
        await main()
    except asyncio.CancelledError:
        logger.info("Получен сигнал отмены, начинаем корректное завершение работы...")
    except Exception as e:
        logger.error(f"Ошибка в main: {e}", exc_info=True)
        logger.info("Попытка перезапуска через 5 секунд...")
        await asyncio.sleep(5)
    finally:
        # Очищаем все задачи при завершении
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        for task in tasks:
            task.cancel()
        try:
            await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            logger.error(f"Ошибка при завершении задач: {e}", exc_info=True)
        logger.info("Приложение корректно завершено")

def handle_exit(signum, frame):
    """Обработчик сигналов завершения"""
    logger.info(f"Получен сигнал завершения {signum}")
    stop_event.set()
    sys.exit(0)

if __name__ == '__main__':
    # Регистрируем обработчики сигналов
    signal.signal(signal.SIGTERM, handle_exit)
    signal.signal(signal.SIGINT, handle_exit)
    
    try:
        logger.info("Запуск приложения...")
        asyncio.run(run_all())
    except KeyboardInterrupt:
        logger.info("Приложение остановлено пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка приложения: {e}", exc_info=True)
        sys.exit(1) 