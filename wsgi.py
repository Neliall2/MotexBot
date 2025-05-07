from bot import app, main
import os
import asyncio
from threading import Thread

def run_bot():
    asyncio.run(main())

if __name__ == '__main__':
    # Запускаем бота в отдельном потоке
    Thread(target=run_bot).start()
    
    # Запускаем Flask
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port) 