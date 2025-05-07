from bot import app, main
import os
import asyncio
from threading import Thread

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    # Запускаем Flask в отдельном потоке
    Thread(target=run_flask).start()
    
    # Запускаем бота в основном потоке
    asyncio.run(main()) 