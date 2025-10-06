import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import threading

class ReminderApp:
    def __init__(self, database, notification_manager):
        self.database = database
        self.notification_manager = notification_manager
        
        self.root = tk.Tk()
        self.root.title("Напоминалка")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        self.setup_ui()
        self.refresh_reminders()
        
        # Запускаем мониторинг уведомлений
        self.notification_manager.start_monitoring()
        
        # Обработчик закрытия окна
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        # Главный фрейм
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Настройка весов для растягивания
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Заголовок
        title_label = ttk.Label(main_frame, text="Напоминалка", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        # Кнопки управления
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        
        ttk.Button(control_frame, text="Добавить напоминание", command=self.add_reminder).pack(side="left", padx=(0, 5))
        ttk.Button(control_frame, text="Обновить", command=self.refresh_reminders).pack(side="left", padx=5)
        ttk.Button(control_frame, text="Тест уведомления", command=self.test_notification).pack(side="left", padx=5)
        
        # Quick time buttons
        quick_time_frame = ttk.Frame(main_frame)
        quick_time_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(5, 0))
        
        ttk.Label(quick_time_frame, text="Быстрое напоминание через:").pack(side="left", padx=(0, 5))
        
        self.quick_time_1m_button = ttk.Button(quick_time_frame, text="1 минута", command=lambda: self.set_quick_time(1))
        self.quick_time_1m_button.pack(side="left")
        
        self.quick_time_5m_button = ttk.Button(quick_time_frame, text="5 минут", command=lambda: self.set_quick_time(5))
        self.quick_time_5m_button.pack(side="left", padx=5)
        
        self.quick_time_15m_button = ttk.Button(quick_time_frame, text="15 минут", command=lambda: self.set_quick_time(15))
        self.quick_time_15m_button.pack(side="left", padx=5)
        
        # НОВАЯ КНОПКА "30 МИНУТ" - ПРОДВИНУТОЕ ЗАДАНИЕ
        self.quick_time_30m_button = ttk.Button(quick_time_frame, text="30 минут", command=lambda: self.set_quick_time(30))
        self.quick_time_30m_button.pack(side="left", padx=5)
        
        # Список напоминаний
        list_frame = ttk.Frame(main_frame)
        list_frame.grid(row=4, column=0, columnspan=2, sticky="nsew", pady=(10, 0))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # Заголовки колонок
        headers_frame = ttk.Frame(list_frame)
        headers_frame.grid(row=0, column=0, sticky="ew")
        headers_frame.columnconfigure(1, weight=1)
        
        ttk.Label(headers_frame, text="ID", width=5).grid(row=0, column=0, sticky="w")
        ttk.Label(headers_frame, text="Название").grid(row=0, column=1, sticky="w")
        ttk.Label(headers_frame, text="Время", width=15).grid(row=0, column=2, sticky="w")
        ttk.Label(headers_frame, text="Статус", width=10).grid(row=0, column=3, sticky="w")
        
        # Treeview для списка напоминаний
        self.tree = ttk.Treeview(list_frame, columns=("id", "title", "time", "status"), show="headings", height=15)
        self.tree.heading("id", text="ID")
        self.tree.heading("title", text="Название")
        self.tree.heading("time", text="Время")
        self.tree.heading("status", text="Статус")
        
        self.tree.column("id", width=50)
        self.tree.column("title", width=200)
        self.tree.column("time", width=150)
        self.tree.column("status", width=100)
        
        self.tree.grid(row=1, column=0, sticky="nsew")
        
        # Скроллбар
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=1, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Кнопки действий
        action_frame = ttk.Frame(main_frame)
        action_frame.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        
        ttk.Button(action_frame, text="Отметить как готово", command=self.mark_as_done).pack(side="left", padx=(0, 5))
        ttk.Button(action_frame, text="Удалить", command=self.delete_reminder).pack(side="left", padx=5)
        
        # Двойной клик для просмотра деталей
        self.tree.bind("<Double-1>", self.on_double_click)
        
        # Статус бар
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief="sunken")
        self.status_bar.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        
        self.update_status_bar()
    
    def update_status_bar(self):
        """Обновить статус бар"""
        count = self.database.get_reminders_count()
        self.status_var.set(f"Всего напоминаний: {count}")
    
    def test_notification(self):
        """Тестовая отправка уведомлений"""
        self.notification_manager.test_notification()
    
    def set_quick_time(self, minutes):
        """Установить быстрое напоминание"""
        due_time = datetime.now() + timedelta(minutes=minutes)
        title = f"Быстрое напоминание ({minutes} мин)"
        description = f"Напоминание установлено на {minutes} минут вперед"
        
        self.database.add_reminder(title, description, due_time)
        self.refresh_reminders()
        messagebox.showinfo("Успех", f"Напоминание установлено на {minutes} минут вперед!")
    
    def add_reminder(self):
        """Добавить новое напоминание"""
        dialog = AddReminderDialog(self.root, self.database)
        if dialog.result:
            self.refresh_reminders()
    
    def refresh_reminders(self):
        """Обновить список напоминаний"""
        # Обрабатываем повторяющиеся напоминания
        self.database.process_recurring_reminders()
        
        # Очищаем список
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Получаем все напоминания
        reminders = self.database.get_all_reminders()
        
        # Добавляем в список
        for reminder in reminders:
            self.tree.insert("", "end", values=(
                reminder[0],  # ID
                reminder[1],  # Title
                reminder[3],  # Due time
                reminder[4]   # Status
            ))
        
        self.update_status_bar()
    
    def mark_as_done(self):
        """Отметить как выполненное"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите напоминание!")
            return
        
        item = self.tree.item(selection[0])
        reminder_id = item['values'][0]
        
        self.database.update_status(reminder_id, "Готово")
        
        # Обработать повторяющиеся напоминания
        self.database.process_recurring_reminders()
        
        self.refresh_reminders()
    
    def delete_reminder(self):
        """Удалить напоминание"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите напоминание!")
            return
        
        item = self.tree.item(selection[0])
        reminder_id = item['values'][0]
        
        if messagebox.askyesno("Подтверждение", "Удалить это напоминание?"):
            self.database.delete_reminder(reminder_id)
            self.refresh_reminders()
    
    def on_double_click(self, event):
        """Обработка двойного клика"""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = self.tree.item(selection[0])
        reminder_id = item['values'][0]
        
        reminder = self.database.get_reminder_by_id(reminder_id)
        if reminder:
            details = f"ID: {reminder[0]}\n"
            details += f"Название: {reminder[1]}\n"
            details += f"Описание: {reminder[2]}\n"
            details += f"Время: {reminder[3]}\n"
            details += f"Статус: {reminder[4]}\n"
            details += f"Создано: {reminder[5]}"
            
            messagebox.showinfo("Детали напоминания", details)
    
    def on_closing(self):
        """Обработка закрытия приложения"""
        if messagebox.askokcancel("Выход", "Вы уверены, что хотите выйти?"):
            self.notification_manager.stop_monitoring()
            self.root.destroy()
    
    def run(self):
        """Запуск приложения"""
        self.root.mainloop()


class AddReminderDialog:
    def __init__(self, parent, database):
        self.database = database
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Добавить напоминание")
        self.dialog.geometry("450x450")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Центрируем окно
        self.dialog.geometry("+%d+%d" % (
            parent.winfo_rootx() + 50,
            parent.winfo_rooty() + 50
        ))
        
        self.setup_ui()
    
    def setup_ui(self):
        """Настройка интерфейса диалога"""
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        # Название
        ttk.Label(main_frame, text="Название:").grid(row=0, column=0, sticky="w", pady=(0, 5))
        self.title_var = tk.StringVar()
        self.title_entry = ttk.Entry(main_frame, textvariable=self.title_var, width=40)
        self.title_entry.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        
        # Описание
        ttk.Label(main_frame, text="Описание:").grid(row=2, column=0, sticky="w", pady=(0, 5))
        self.desc_text = tk.Text(main_frame, height=4, width=40)
        self.desc_text.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        
        # Дата и время
        ttk.Label(main_frame, text="Дата и время:").grid(row=4, column=0, sticky="w", pady=(0, 5))
        
        time_frame = ttk.Frame(main_frame)
        time_frame.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        
        # Устанавливаем время по умолчанию (через 5 минут)
        default_time = datetime.now() + timedelta(minutes=5)
        
        self.date_var = tk.StringVar(value=default_time.strftime("%Y-%m-%d"))
        self.time_var = tk.StringVar(value=default_time.strftime("%H:%M"))
        
        ttk.Entry(time_frame, textvariable=self.date_var, width=12).pack(side="left", padx=(0, 5))
        ttk.Entry(time_frame, textvariable=self.time_var, width=8).pack(side="left")
        
        # Повторяющееся напоминание
        self.is_recurring_var = tk.BooleanVar()
        recurring_check = ttk.Checkbutton(main_frame, text="Повторяющееся напоминание", 
                                        variable=self.is_recurring_var, command=self.toggle_recurring)
        recurring_check.grid(row=6, column=0, columnspan=2, sticky="w", pady=(10, 5))
        
        # Настройки повторения (скрыты по умолчанию)
        self.recurring_frame = ttk.Frame(main_frame)
        self.recurring_frame.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        
        ttk.Label(self.recurring_frame, text="Повторять каждые:").pack(side="left", padx=(0, 5))
        
        self.interval_var = tk.StringVar(value="1")
        interval_entry = ttk.Entry(self.recurring_frame, textvariable=self.interval_var, width=5)
        interval_entry.pack(side="left", padx=(0, 5))
        
        self.unit_var = tk.StringVar(value="часов")
        unit_combo = ttk.Combobox(self.recurring_frame, textvariable=self.unit_var, 
                                 values=["минут", "часов", "дней"], state="readonly", width=8)
        unit_combo.pack(side="left")
        
        # Скрываем настройки повторения по умолчанию
        self.recurring_frame.grid_remove()
        
        ttk.Label(time_frame, text="(ГГГГ-ММ-ДД ЧЧ:ММ)").pack(side="left", padx=5)
        
        # Кнопки
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=8, column=0, columnspan=2, pady=(20, 0), sticky="ew")
        
        ttk.Button(button_frame, text="Добавить", command=self.add_reminder).pack(side="left", padx=(0, 10))
        ttk.Button(button_frame, text="Отмена", command=self.cancel).pack(side="left")
        
        # Фокус на поле названия
        self.title_entry.focus()
    
    def toggle_recurring(self):
        """Показать/скрыть настройки повторения"""
        if self.is_recurring_var.get():
            self.recurring_frame.grid()
        else:
            self.recurring_frame.grid_remove()
    
    def add_reminder(self):
        """Добавить напоминание"""
        title = self.title_var.get().strip()
        description = self.desc_text.get("1.0", tk.END).strip()
        
        if not title:
            messagebox.showerror("Ошибка", "Введите название напоминания!")
            return
        
        try:
            date_str = self.date_var.get()
            time_str = self.time_var.get()
            due_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            
            if due_time <= datetime.now():
                messagebox.showerror("Ошибка", "Время напоминания должно быть в будущем!")
                return
            
            # Параметры повторения
            is_recurring = self.is_recurring_var.get()
            recurring_interval = 0
            recurring_unit = 'minutes'
            
            if is_recurring:
                try:
                    recurring_interval = int(self.interval_var.get())
                    if recurring_interval <= 0:
                        messagebox.showerror("Ошибка", "Интервал повторения должен быть больше 0!")
                        return
                    
                    # Преобразуем единицы измерения
                    unit_map = {"минут": "minutes", "часов": "hours", "дней": "days"}
                    recurring_unit = unit_map.get(self.unit_var.get(), "minutes")
                    
                except ValueError:
                    messagebox.showerror("Ошибка", "Неверный интервал повторения!")
                    return
            
            self.database.add_reminder(title, description, due_time, is_recurring, recurring_interval, recurring_unit)
            self.result = True
            self.dialog.destroy()
            
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат даты или времени!")
    
    def cancel(self):
        """Отмена"""
        self.dialog.destroy()