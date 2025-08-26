import tkinter as tk
from tkinter import messagebox
import threading
import time
from datetime import datetime

class NotificationManager:
    def __init__(self, database):
        self.database = database
        self.running = False
        self.notification_thread = None
        self.shown_reminders = set()  # Множество для отслеживания показанных напоминаний
    
    def start_monitoring(self):
        """Запустить мониторинг уведомлений в фоновом режиме"""
        if not self.running:
            self.running = True
            self.notification_thread = threading.Thread(target=self._monitor_reminders, daemon=True)
            self.notification_thread.start()
    
    def stop_monitoring(self):
        """Остановить мониторинг уведомлений"""
        self.running = False
        self.shown_reminders.clear()  # Очищаем множество показанных напоминаний
    
    def _monitor_reminders(self):
        """Мониторинг напоминаний в фоновом режиме"""
        while self.running:
            try:
                # Проверяем просроченные напоминания
                self.database.mark_overdue()
                
                # Получаем напоминания, которые должны сработать
                due_reminders = self.database.get_due_reminders()
                
                for reminder in due_reminders:
                    # Проверяем, не показывали ли мы уже это напоминание
                    if reminder[0] not in self.shown_reminders:
                        self.shown_reminders.add(reminder[0])  # Добавляем в множество показанных
                        self._show_notification(reminder)
                        # Статус обновляется в _show_popup при закрытии окна
                
                time.sleep(1)  # Проверяем каждую секунду
            except Exception as e:
                print(f"Ошибка в мониторинге: {e}")
                time.sleep(5)
    
    def _show_notification(self, reminder):
        """Показать уведомление"""
        try:
            # Пробуем системное уведомление
            self._show_system_notification(reminder)
        except:
            # Если не получилось, показываем popup
            self._show_popup(reminder)
    
    def _show_system_notification(self, reminder):
        """Показать системное уведомление (Windows Toast)"""
        try:
            from win10toast import ToastNotifier
            toaster = ToastNotifier()
            toaster.show_toast(
                reminder[1],  # title
                reminder[2] if reminder[2] else "Время напоминания!",  # description
                duration=10,
                threaded=True
            )
        except ImportError:
            # Если win10toast не установлен, используем popup
            raise Exception("win10toast не установлен")
    
    def _show_popup(self, reminder):
        """Показать popup окно"""
        popup = tk.Toplevel()
        popup.title("Напоминание")
        popup.geometry("400x250")
        popup.resizable(False, False)
        
        # Центрируем окно
        popup.geometry("+%d+%d" % (
            popup.winfo_screenwidth()//2 - 200,
            popup.winfo_screenheight()//2 - 100
        ))
        
        # Делаем окно поверх всех остальных
        popup.attributes('-topmost', True)
        popup.focus_force()
        
        # Содержимое окна
        title_label = tk.Label(popup, text=reminder[1], font=("Arial", 14, "bold"))
        title_label.pack(pady=20)
        
        if reminder[2]:
            desc_label = tk.Label(popup, text=reminder[2], font=("Arial", 10))
            desc_label.pack(pady=10)
        
        time_label = tk.Label(popup, text=f"Время: {reminder[3]}", font=("Arial", 9))
        time_label.pack(pady=10)
        
        def close_and_update():
            """Закрыть окно и обновить статус напоминания"""
            popup.destroy()
            # Обновляем статус только для реальных напоминаний (ID > 0)
            if reminder[0] > 0:
                self.database.update_status(reminder[0], "Готово")
                # Удаляем из множества показанных напоминаний
                self.shown_reminders.discard(reminder[0])
        
        # Кнопка закрытия
        close_button = tk.Button(popup, text="OK", command=close_and_update, width=10, height=2)
        close_button.pack(pady=20)
        
        # Автоматическое закрытие через 30 секунд
        popup.after(30000, close_and_update)
        
        # Дополнительная защита: обновляем статус через 5 секунд, если окно еще открыто
        def force_update_status():
            if reminder[0] > 0 and reminder[0] in self.shown_reminders:
                self.database.update_status(reminder[0], "Готово")
                self.shown_reminders.discard(reminder[0])
        
        popup.after(5000, force_update_status)
    
    def show_manual_notification(self, title="Тестовое уведомление", message="Это тестовое уведомление"):
        """Показать уведомление вручную"""
        reminder = (0, title, message, datetime.now())
        self._show_notification(reminder)
    
    def test_notification(self):
        """Тестовая функция для проверки уведомлений"""
        self.show_manual_notification("Тест", "Это тестовое уведомление!")
