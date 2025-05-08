import logging
import json
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes
)
from config import Config
from bitrix_api import BitrixAPI
from database import Database
from flask import Flask
from threading import Thread, Lock
import os
import asyncio
import sys
from datetime import datetime
import tempfile
import signal
import httpx

# Создаем Flask приложение
app = Flask(__name__)

# Настройка логирования
log_dir = os.path.join(tempfile.gettempdir(), 'bot_logs')
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(log_dir, f'bot_{datetime.now().strftime("%Y%m%d")}.log'), encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

# Глобальные переменные для контроля состояния бота
bot_lock = Lock()
bot_instance = None
stop_event = asyncio.Event()

db = Database()
STATES = Config.STATES

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    try:
        port = int(os.environ.get('PORT', 8080))
        logger.info(f"Запуск Flask на порту {port}")
        app.run(host='0.0.0.0', port=port)
    except Exception as e:
        logger.error(f"Ошибка Flask: {e}", exc_info=True)

def main_menu():
    return ReplyKeyboardMarkup([
        ['🚫 Отказ', '⚠️ Претензия'],
        ['ℹ️ Информация', '❌ Отмена']
    ], resize_keyboard=True)


def cancel_button():
    return ReplyKeyboardMarkup([['❌ Отмена']], resize_keyboard=True)


def add_more_button():
    return ReplyKeyboardMarkup([
        ['➕ Добавить артикул', '➡ Продолжить'],
        ['❌ Отмена']
    ], resize_keyboard=True)


def claim_type_keyboard():
    return ReplyKeyboardMarkup([
        ['Недовоз', 'Брак'],
        ['Пересорт', '❌ Отмена']
    ], resize_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Добрый день! Выберите тип обращения:",
        reply_markup=main_menu()
    )
    return STATES['START']


async def handle_refusal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("📋 Введите код клиента:", reply_markup=cancel_button())
    return STATES['CLIENT_CODE']


async def handle_claim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("📋 Выберите тип претензии:", reply_markup=claim_type_keyboard())
    return STATES['CLAIM_TYPE']


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "Добрый день! Выберите тип обращения:",
        reply_markup=main_menu()
    )
    return ConversationHandler.END


async def check_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == '❌ Отмена':
        return await cancel(update, context)
    return None


async def process_client_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cancel_result = await check_cancel(update, context)
    if cancel_result is not None:
        return cancel_result

    user = update.message.from_user
    code = update.message.text

    if not code.isdigit():
        await update.message.reply_text("❌ Код должен содержать только цифры!")
        return STATES['CLIENT_CODE']

    context.user_data['client_code'] = code
    await update.message.reply_text("📍 Введите маршрут:")
    return STATES['ROUTE']


async def process_route(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cancel_result = await check_cancel(update, context)
    if cancel_result is not None:
        return cancel_result

    context.user_data['route'] = update.message.text
    await update.message.reply_text("📦 Введите артикул товара:")
    return STATES['ARTICLES']


async def process_articles(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cancel_result = await check_cancel(update, context)
    if cancel_result is not None:
        return cancel_result

    context.user_data['current_article'] = update.message.text
    await update.message.reply_text("🔢 Введите количество:")
    return STATES['QUANTITY']


async def process_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cancel_result = await check_cancel(update, context)
    if cancel_result is not None:
        return cancel_result

    quantity = update.message.text

    if not quantity.isdigit():
        await update.message.reply_text("❌ Введите число!")
        return STATES['QUANTITY']

    article = context.user_data.get('current_article')
    if not article:
        await update.message.reply_text("⚠️ Ошибка: артикул не найден")
        return STATES['ARTICLES']

    if 'articles' not in context.user_data:
        context.user_data['articles'] = []

    context.user_data['articles'].append({
        'article': article,
        'quantity': quantity
    })

    del context.user_data['current_article']

    await update.message.reply_text(
        "✅ Товар добавлен!\nДобавить ещё артикул?",
        reply_markup=add_more_button()
    )
    return STATES['ARTICLES']


async def process_articles_or_continue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cancel_result = await check_cancel(update, context)
    if cancel_result is not None:
        return cancel_result

    choice = update.message.text

    if choice == '➕ Добавить артикул':
        await update.message.reply_text("📦 Введите артикул товара:")
        return STATES['ARTICLES']
    elif choice == '➡ Продолжить':
        await update.message.reply_text("📄 Введите номер документа/УПД:")
        return STATES['DOCUMENT_NUMBER']
    else:
        context.user_data['current_article'] = choice
        await update.message.reply_text("🔢 Введите количество:")
        return STATES['QUANTITY']


async def process_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cancel_result = await check_cancel(update, context)
    if cancel_result is not None:
        return cancel_result

    context.user_data['document_number'] = update.message.text
    await update.message.reply_text("📝 Введите комментарий:")
    return STATES['COMMENT']


async def process_comment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cancel_result = await check_cancel(update, context)
    if cancel_result is not None:
        return cancel_result

    user_data = context.user_data
    user_data['comment'] = update.message.text

    task_type = 'claim' if 'claim_type' in user_data else 'refusal'
    task_title = Config.TASK_TITLES[task_type]
    
    # Формируем название задачи в зависимости от типа претензии
    if task_type == 'claim':
        task_title = f"Претензия {user_data['claim_type']}"

    result = BitrixAPI.create_task(task_type, {
        'client_code': user_data['client_code'],
        'route': user_data['route'],
        'articles': user_data.get('articles', []),
        'document_number': user_data.get('document_number', ''),
        'comment': user_data['comment'],
        'claim_type': user_data.get('claim_type', ''),
        'title': task_title
    })

    if result.get('success'):
        await update.message.reply_text(
            f"✅ Задача создана! ID: {result['task_id']}",
            reply_markup=main_menu()
        )
    else:
        await update.message.reply_text(
            f"❌ Ошибка: {result.get('error', 'Неизвестная ошибка')}",
            reply_markup=main_menu()
        )

    context.user_data.clear()
    return ConversationHandler.END


async def process_claim_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    claim_type = update.message.text
    if claim_type not in ['Недовоз', 'Брак', 'Пересорт']:
        await update.message.reply_text("❌ Выберите тип претензии из списка!", reply_markup=claim_type_keyboard())
        return STATES['CLAIM_TYPE']
    
    context.user_data['claim_type'] = claim_type
    await update.message.reply_text("📋 Введите код клиента:", reply_markup=cancel_button())
    return STATES['CLIENT_CODE']


async def handle_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("📋 Введите код клиента:", reply_markup=cancel_button())
    return STATES['INFO_CLIENT_CODE']


async def process_info_client_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cancel_result = await check_cancel(update, context)
    if cancel_result is not None:
        return cancel_result

    code = update.message.text
    if not code.isdigit():
        await update.message.reply_text("❌ Код должен содержать только цифры!")
        return STATES['INFO_CLIENT_CODE']

    context.user_data['client_code'] = code
    await update.message.reply_text("📍 Введите маршрут:")
    return STATES['INFO_ROUTE']


async def process_info_route(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cancel_result = await check_cancel(update, context)
    if cancel_result is not None:
        return cancel_result

    context.user_data['route'] = update.message.text
    await update.message.reply_text("📝 Введите комментарий:")
    return STATES['INFO_COMMENT']


async def process_info_comment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cancel_result = await check_cancel(update, context)
    if cancel_result is not None:
        return cancel_result

    user_data = context.user_data
    user_data['comment'] = update.message.text

    result = BitrixAPI.create_task('info', {
        'client_code': user_data['client_code'],
        'route': user_data['route'],
        'comment': user_data['comment'],
        'title': 'Информация от водителя'
    })

    if result.get('success'):
        await update.message.reply_text(
            f"✅ Задача создана! ID: {result['task_id']}",
            reply_markup=main_menu()
        )
    else:
        await update.message.reply_text(
            f"❌ Ошибка: {result.get('error', 'Неизвестная ошибка')}",
            reply_markup=main_menu()
        )

    context.user_data.clear()
    return ConversationHandler.END


async def check_bot_health():
    """Проверка состояния бота"""
    global bot_instance
    while not stop_event.is_set():
        try:
            if bot_instance is not None:
                # Проверяем соединение с Telegram API
                try:
                    await bot_instance.bot.get_me()
                    logger.info("Проверка состояния бота: OK")
                except Exception as e:
                    logger.error(f"Ошибка при проверке состояния бота: {e}")
                    # Перезапускаем бота при ошибке
                    with bot_lock:
                        try:
                            await bot_instance.stop()
                            await bot_instance.shutdown()
                        except Exception as stop_error:
                            logger.error(f"Ошибка при остановке бота: {stop_error}")
                        bot_instance = None
            await asyncio.sleep(60)  # Проверка каждую минуту
        except Exception as e:
            logger.error(f"Ошибка в проверке состояния бота: {e}")
            await asyncio.sleep(60)

async def main():
    global bot_instance, stop_event
    
    # Запускаем проверку состояния бота
    health_check_task = asyncio.create_task(check_bot_health())
    
    retry_count = 0
    max_retries = 5
    
    while not stop_event.is_set():
        try:
            with bot_lock:
                if bot_instance is not None:
                    logger.info("Останавливаем предыдущий экземпляр бота...")
                    try:
                        await bot_instance.stop()
                        await bot_instance.shutdown()
                    except Exception as e:
                        logger.error(f"Ошибка при остановке предыдущего экземпляра: {e}", exc_info=True)
                    bot_instance = None
                    await asyncio.sleep(2)  # Даем время на завершение

                logger.info("Инициализация нового экземпляра бота...")
                # Создаем HTTP-клиент перед инициализацией бота
                async with httpx.AsyncClient() as client:
                    application = (
                        ApplicationBuilder()
                        .token(Config.BOT_TOKEN)
                        .http_version("1.1")
                        .get_updates_http_version("1.1")
                        .build()
                    )

                    # Настройка обработчиков
                    refusal_conv = ConversationHandler(
                        entry_points=[MessageHandler(filters.Regex(r'^🚫 Отказ$'), handle_refusal)],
                        states={
                            STATES['CLIENT_CODE']: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_client_code)],
                            STATES['ROUTE']: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_route)],
                            STATES['ARTICLES']: [
                                MessageHandler(filters.Regex(r'^(➕ Добавить артикул|➡ Продолжить)$'), process_articles_or_continue),
                                MessageHandler(filters.TEXT & ~filters.COMMAND, process_articles)
                            ],
                            STATES['QUANTITY']: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_quantity)],
                            STATES['DOCUMENT_NUMBER']: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_document)],
                            STATES['COMMENT']: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_comment)]
                        },
                        fallbacks=[CommandHandler('cancel', cancel)],
                        name='refusal_conversation',
                        persistent=False
                    )

                    claim_conv = ConversationHandler(
                        entry_points=[MessageHandler(filters.Regex(r'^⚠️ Претензия$'), handle_claim)],
                        states={
                            STATES['CLAIM_TYPE']: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_claim_type)],
                            STATES['CLIENT_CODE']: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_client_code)],
                            STATES['ROUTE']: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_route)],
                            STATES['ARTICLES']: [
                                MessageHandler(filters.Regex(r'^(➕ Добавить артикул|➡ Продолжить)$'), process_articles_or_continue),
                                MessageHandler(filters.TEXT & ~filters.COMMAND, process_articles)
                            ],
                            STATES['QUANTITY']: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_quantity)],
                            STATES['DOCUMENT_NUMBER']: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_document)],
                            STATES['COMMENT']: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_comment)]
                        },
                        fallbacks=[CommandHandler('cancel', cancel)],
                        name='claim_conversation',
                        persistent=False
                    )

                    info_conv = ConversationHandler(
                        entry_points=[MessageHandler(filters.Regex(r'^ℹ️ Информация$'), handle_info)],
                        states={
                            STATES['INFO_CLIENT_CODE']: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_info_client_code)],
                            STATES['INFO_ROUTE']: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_info_route)],
                            STATES['INFO_COMMENT']: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_info_comment)]
                        },
                        fallbacks=[CommandHandler('cancel', cancel)],
                        name='info_conversation',
                        persistent=False
                    )

                    application.add_handler(refusal_conv)
                    application.add_handler(claim_conv)
                    application.add_handler(info_conv)
                    application.add_handler(CommandHandler('start', start))
                    application.add_error_handler(error_handler)

                    bot_instance = application
                    logger.info("Бот успешно инициализирован")

                # Запускаем бота
                try:
                    await application.initialize()
                    await application.start()
                    await application.updater.start_polling(
                        drop_pending_updates=True,
                        allowed_updates=Update.ALL_TYPES,
                        pool_timeout=30,
                        read_timeout=30,
                        write_timeout=30,
                        connect_timeout=30
                    )
                
                    # Сбрасываем счетчик попыток при успешном запуске
                    retry_count = 0
                    
                    # Ждем сигнала остановки
                    while not stop_event.is_set():
                        try:
                            await asyncio.sleep(1)
                        except asyncio.CancelledError:
                            logger.info("Получен сигнал отмены, начинаем корректное завершение работы...")
                            break

                    # Корректное завершение работы
                    try:
                        await application.updater.stop()
                        await application.stop()
                        await application.shutdown()
                        logger.info("Бот успешно остановлен")
                    except Exception as e:
                        logger.error(f"Ошибка при остановке бота: {e}", exc_info=True)
                except Exception as e:
                    logger.error(f"Ошибка при запуске бота: {e}", exc_info=True)
                    if bot_instance is not None:
                        try:
                            await bot_instance.stop()
                            await bot_instance.shutdown()
                        except Exception as stop_error:
                            logger.error(f"Ошибка при остановке бота после ошибки запуска: {stop_error}", exc_info=True)
                        bot_instance = None
                    
                    # Увеличиваем счетчик попыток
                    retry_count += 1
                    if retry_count >= max_retries:
                        logger.error(f"Достигнуто максимальное количество попыток ({max_retries}). Останавливаем бота.")
                        stop_event.set()
                        break
                    
                    # Экспоненциальная задержка перед следующей попыткой
                    delay = min(300, 5 * (2 ** retry_count))  # Максимум 5 минут
                    logger.info(f"Попытка переподключения через {delay} секунд...")
                    await asyncio.sleep(delay)

        except asyncio.CancelledError:
            logger.info("Получен сигнал отмены в основном цикле")
            break
        except Exception as e:
            logger.error(f"Критическая ошибка в работе бота: {e}", exc_info=True)
            logger.info("Попытка переподключения через 5 секунд...")
            await asyncio.sleep(5)
    
    # Отменяем задачу проверки состояния
    health_check_task.cancel()
    try:
        await health_check_task
    except asyncio.CancelledError:
        pass

def handle_signal(signum, frame):
    """Обработчик сигналов завершения"""
    logger.info(f"Получен сигнал завершения {signum}")
    stop_event.set()

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик ошибок бота"""
    logger.error(f"Ошибка при обработке обновления {update}: {context.error}", exc_info=True)
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "Произошла ошибка при обработке запроса. Пожалуйста, попробуйте позже."
            )
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения об ошибке: {e}", exc_info=True)

if __name__ == '__main__':
    # Регистрируем обработчики сигналов
    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)
    
    try:
        logger.info("Запуск бота...")
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске бота: {e}", exc_info=True)
        sys.exit(1)