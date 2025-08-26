#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Главный файл для запуска напоминалки
"""

from database import ReminderDatabase
from notifications import NotificationManager
from gui import ReminderApp

def main():
    """Главная функция приложения"""
    print("Запуск напоминалки...")
    
    # Инициализируем базу данных
    database = ReminderDatabase()
    
    # Инициализируем менеджер уведомлений
    notification_manager = NotificationManager(database)
    
    # Создаем и запускаем GUI приложение
    app = ReminderApp(database, notification_manager)
    app.run()

if __name__ == "__main__":
    main()
