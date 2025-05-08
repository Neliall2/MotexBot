from bot import app, main
import os
import asyncio
from threading import Thread
import nest_asyncio

# Разрешаем вложенные event loops
nest_asyncio.apply()

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

async def run_all():
    # Запускаем Flask в отдельном потоке
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True  # Делаем поток демоном
    flask_thread.start()
    
    try:
        # Запускаем бота
        await main()
    except Exception as e:
        print(f"Error in main: {e}")
    finally:
        # Очищаем все задачи при завершении
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

if __name__ == '__main__':
    try:
        asyncio.run(run_all())
    except KeyboardInterrupt:
        print("Application stopped by user")
    except Exception as e:
        print(f"Application error: {e}") 