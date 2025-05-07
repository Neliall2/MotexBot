from bot import app, main
import os
from threading import Thread

if __name__ == '__main__':
    # Запускаем бота в отдельном потоке
    Thread(target=main).start()
    
    # Запускаем Flask
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port) 