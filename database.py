import sqlite3
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_file="bot.db"):
        self.db_file = db_file
        self.connection = None
        self.cursor = None
        self.connect()
        self.create_tables()

    def connect(self):
        try:
            self.connection = sqlite3.connect(self.db_file)
            self.cursor = self.connection.cursor()
            logger.info("Connected to database")
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}")

    def create_tables(self):
        try:
            # Создаем таблицу для хранения данных пользователей
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Создаем таблицу для хранения задач
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    task_type TEXT,
                    client_code TEXT,
                    route TEXT,
                    document_number TEXT,
                    comment TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            self.connection.commit()
            logger.info("Database tables created successfully")
        except sqlite3.Error as e:
            logger.error(f"Error creating tables: {e}")

    def add_user(self, user_id, username, first_name, last_name):
        try:
            self.cursor.execute('''
                INSERT OR IGNORE INTO users (user_id, username, first_name, last_name)
                VALUES (?, ?, ?, ?)
            ''', (user_id, username, first_name, last_name))
            self.connection.commit()
            logger.info(f"User {user_id} added to database")
        except sqlite3.Error as e:
            logger.error(f"Error adding user: {e}")

    def add_task(self, user_id, task_type, client_code, route, document_number, comment):
        try:
            self.cursor.execute('''
                INSERT INTO tasks (user_id, task_type, client_code, route, document_number, comment)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, task_type, client_code, route, document_number, comment))
            self.connection.commit()
            logger.info(f"Task added to database for user {user_id}")
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            logger.error(f"Error adding task: {e}")
            return None

    def get_user_tasks(self, user_id):
        try:
            self.cursor.execute('''
                SELECT * FROM tasks WHERE user_id = ? ORDER BY created_at DESC
            ''', (user_id,))
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Error getting user tasks: {e}")
            return []

    def close(self):
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")