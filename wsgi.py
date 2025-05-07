from bot import app, main
import os
import asyncio
from threading import Thread
import nest_asyncio

# Разрешаем вложенные event loops
nest_asyncio.apply()

async def run_flask():
    port = int(os.environ.get('PORT', 8080))
    # Запускаем Flask в отдельном потоке
    Thread(target=lambda: app.run(host='0.0.0.0', port=port)).start()

async def run_all():
    # Запускаем Flask
    await run_flask()
    # Запускаем бота
    await main()

if __name__ == '__main__':
    asyncio.run(run_all()) 