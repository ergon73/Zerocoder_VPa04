import sqlite3
from datetime import datetime, timedelta

class ReminderDatabase:
    def __init__(self, db_name="reminders.db"):
        self.db_name = db_name
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    due_time TIMESTAMP NOT NULL,
                    status TEXT DEFAULT 'Ожидает',
                    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
    
    def add_reminder(self, title, description, due_time):
        """Добавить новое напоминание"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO reminders (title, description, due_time)
                VALUES (?, ?, ?)
            ''', (title, description, due_time))
            conn.commit()
            return cursor.lastrowid
    
    def get_all_reminders(self):
        """Получить все напоминания"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM reminders ORDER BY due_time')
            return cursor.fetchall()
    
    def get_due_reminders(self):
        """Получить напоминания, которые должны сработать"""
        now = datetime.now()
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM reminders 
                WHERE due_time <= ? AND status = 'Ожидает'
                ORDER BY due_time
            ''', (now,))
            return cursor.fetchall()
    
    def sort_by_due_time(self, reminders):
        """Сортировка по времени ближайшего срабатывания"""
        return sorted(reminders, key=lambda x: x[3])
    
    def update_status(self, reminder_id, status):
        """Изменить статус напоминания"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE reminders SET status = ? WHERE id = ?
            ''', (status, reminder_id))
            conn.commit()
    
    def delete_reminder(self, reminder_id):
        """Удалить напоминание"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM reminders WHERE id = ?', (reminder_id,))
            conn.commit()
    
    def mark_overdue(self):
        """Перевести просроченные напоминания в статус 'Просрочено'"""
        now = datetime.now()
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE reminders 
                SET status = 'Просрочено' 
                WHERE due_time < ? AND status = 'Ожидает'
            ''', (now - timedelta(minutes=1),))
            conn.commit()
    
    def get_reminder_by_id(self, reminder_id):
        """Получить напоминание по ID"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM reminders WHERE id = ?', (reminder_id,))
            return cursor.fetchone()
    
    def get_reminders_count(self):
        """Подсчитать общее количество напоминаний"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM reminders')
            return cursor.fetchone()[0]
