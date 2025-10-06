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
                    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_recurring BOOLEAN DEFAULT 0,
                    recurring_interval INTEGER DEFAULT 0,
                    recurring_unit TEXT DEFAULT 'minutes'
                )
            ''')
            
            # Проверяем, есть ли новые поля, и добавляем их если нужно
            cursor.execute('PRAGMA table_info(reminders)')
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'is_recurring' not in columns:
                cursor.execute('ALTER TABLE reminders ADD COLUMN is_recurring BOOLEAN DEFAULT 0')
            if 'recurring_interval' not in columns:
                cursor.execute('ALTER TABLE reminders ADD COLUMN recurring_interval INTEGER DEFAULT 0')
            if 'recurring_unit' not in columns:
                cursor.execute('ALTER TABLE reminders ADD COLUMN recurring_unit TEXT DEFAULT "minutes"')
            
            conn.commit()
    
    def add_reminder(self, title, description, due_time, is_recurring=False, recurring_interval=0, recurring_unit='minutes'):
        """Добавить новое напоминание"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO reminders (title, description, due_time, is_recurring, recurring_interval, recurring_unit)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (title, description, due_time, is_recurring, recurring_interval, recurring_unit))
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
    
    def process_recurring_reminders(self):
        """Обработать повторяющиеся напоминания"""
        now = datetime.now()
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            
            # Найти выполненные и просроченные повторяющиеся напоминания
            cursor.execute('''
                SELECT * FROM reminders 
                WHERE is_recurring = 1 AND (status = 'Готово' OR status = 'Просрочено')
            ''')
            completed_recurring = cursor.fetchall()
            
            for reminder in completed_recurring:
                # Создать новое напоминание на основе текущего времени
                interval = reminder[6]  # recurring_interval
                unit = reminder[7]      # recurring_unit
                
                # Вычислить новое время от текущего момента
                if unit == 'minutes':
                    new_due_time = now + timedelta(minutes=interval)
                elif unit == 'hours':
                    new_due_time = now + timedelta(hours=interval)
                elif unit == 'days':
                    new_due_time = now + timedelta(days=interval)
                else:
                    new_due_time = now + timedelta(minutes=interval)
                
                # Добавить новое напоминание
                cursor.execute('''
                    INSERT INTO reminders (title, description, due_time, is_recurring, recurring_interval, recurring_unit)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (reminder[1], reminder[2], new_due_time, 1, interval, unit))
                
                # Удалить старое напоминание
                cursor.execute('DELETE FROM reminders WHERE id = ?', (reminder[0],))
            
            conn.commit()
