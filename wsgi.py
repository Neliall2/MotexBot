from bot import app, main
import os
import asyncio
from threading import Thread
import nest_asyncio
import logging
import sys
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log')
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
        logger.error(f"Ошибка Flask: {e}")

async def run_all():
    # Запускаем Flask в отдельном потоке
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    logger.info("Flask запущен в отдельном потоке")
    
    while True:  # Бесконечный цикл для поддержания работы приложения
        try:
            logger.info("Запуск бота...")
            await main()
        except Exception as e:
            logger.error(f"Ошибка в main: {e}")
            logger.info("Попытка перезапуска через 5 секунд...")
            await asyncio.sleep(5)
        finally:
            # Очищаем все задачи при завершении
            tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)

if __name__ == '__main__':
    try:
        logger.info("Запуск приложения...")
        asyncio.run(run_all())
    except KeyboardInterrupt:
        logger.info("Приложение остановлено пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка приложения: {e}")
        sys.exit(1) 