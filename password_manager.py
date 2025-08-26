#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CLI-приложение для хранения паролей с шифрованием
"""

import sqlite3
import hashlib
import string
import random
import getpass
import os
from cryptography.fernet import Fernet

class DatabaseManager:
    def __init__(self, db_name: str = "passwords.db") -> None:
        self.db_name = db_name
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            
            # Таблица для мастер-пароля
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS master_password (
                    id INTEGER PRIMARY KEY,
                    password_hash TEXT NOT NULL
                )
            ''')
            
            # Таблица для паролей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS passwords (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    login TEXT NOT NULL,
                    password_encrypted TEXT NOT NULL,
                    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
    
    def set_master_password(self, password):
        """Установить мастер-пароль"""
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            
            # Проверяем, есть ли уже мастер-пароль
            cursor.execute('SELECT COUNT(*) FROM master_password')
            if cursor.fetchone()[0] == 0:
                cursor.execute('INSERT INTO master_password (password_hash) VALUES (?)', (password_hash,))
            else:
                cursor.execute('UPDATE master_password SET password_hash = ? WHERE id = 1', (password_hash,))
            
            conn.commit()
    
    def get_master_password(self):
        """Получить хэш мастер-пароля"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT password_hash FROM master_password LIMIT 1')
            result = cursor.fetchone()
            return result[0] if result else None
    
    def verify_master_password(self, password):
        """Проверить мастер-пароль"""
        stored_hash = self.get_master_password()
        if not stored_hash:
            return False
        
        input_hash = hashlib.sha256(password.encode()).hexdigest()
        return input_hash == stored_hash
    
    def add_password(self, name, login, encrypted_password):
        """Добавить пароль"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO passwords (name, login, password_encrypted)
                VALUES (?, ?, ?)
            ''', (name, login, encrypted_password))
            conn.commit()
            return cursor.lastrowid
    
    def get_password(self, name):
        """Получить пароль по названию"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM passwords WHERE name = ?', (name,))
            return cursor.fetchone()
    
    def list_passwords(self):
        """Получить список всех паролей"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, name, login, created_time FROM passwords ORDER BY name')
            return cursor.fetchall()
    
    def delete_password(self, name):
        """Удалить пароль"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM passwords WHERE name = ?', (name,))
            conn.commit()
            return cursor.rowcount > 0


class EncryptionManager:
    def __init__(self, key_file=".key"):
        self.key_file = key_file
        self.key = self._load_or_generate_key()
        self.cipher = Fernet(self.key)
    
    def _load_or_generate_key(self):
        """Загрузить существующий ключ или сгенерировать новый"""
        if os.path.exists(self.key_file):
            with open(self.key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
            return key
    
    def encrypt(self, data):
        """Зашифровать данные"""
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data):
        """Расшифровать данные"""
        return self.cipher.decrypt(encrypted_data.encode()).decode()


class PasswordGenerator:
    def __init__(self, length=16, use_uppercase=True, use_lowercase=True, use_digits=True, use_special=True, exclude_similar=False):
        self.length = length
        self.use_uppercase = use_uppercase
        self.use_lowercase = use_lowercase
        self.use_digits = use_digits
        self.use_special = use_special
        self.exclude_similar = exclude_similar
    
    def generate(self, length=16, use_uppercase=True, use_lowercase=True, use_digits=True, use_special=True, exclude_similar=False):
        """Генерировать пароль с заданными параметрами"""
        character_pool = ""
        
        if use_uppercase:
            character_pool += string.ascii_uppercase
        if use_lowercase:
            character_pool += string.ascii_lowercase
        if use_digits:
            character_pool += string.digits
        if use_special:
            character_pool += string.punctuation
        
        if not character_pool:
            raise ValueError("Не выбраны символы для генерации пароля.")
        
        # ПРОДВИНУТОЕ ЗАДАНИЕ: Проверка на похожие символы с перегенерацией
        if exclude_similar:
            max_attempts = 100  # Ограничиваем количество попыток
            for attempt in range(max_attempts):
                password = ''.join(random.choice(character_pool) for _ in range(length))
                
                # Проверяем, есть ли похожие символы в одном пароле
                similar_chars = ['0', 'O', 'l', 'I']
                has_similar = False
                
                for char in similar_chars:
                    if char in password:
                        # Проверяем, есть ли другая похожая буква в том же пароле
                        for other_char in similar_chars:
                            if other_char != char and other_char in password:
                                has_similar = True
                                break
                        if has_similar:
                            break
                
                # Если похожих символов нет или только один, возвращаем пароль
                if not has_similar:
                    return password
            
            # Если не удалось сгенерировать подходящий пароль, возвращаем обычный
            print("Предупреждение: Не удалось сгенерировать пароль без похожих символов. Возвращаем обычный пароль.")
            return ''.join(random.choice(character_pool) for _ in range(length))
        else:
            # Обычная генерация без проверки
            password = ''.join(random.choice(character_pool) for _ in range(length))
            return password


class PasswordManager:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.encryption_manager = EncryptionManager()
        self.password_generator = PasswordGenerator()
    
    def setup_master_password(self):
        """Установить мастер-пароль при первом запуске"""
        print("Добро пожаловать! Это ваш первый запуск.")
        print("Установите мастер-пароль для защиты ваших данных.")
        
        while True:
            password = getpass.getpass("Введите мастер-пароль: ")
            confirm_password = getpass.getpass("Подтвердите мастер-пароль: ")
            
            if password == confirm_password:
                if len(password) >= 6:
                    self.db_manager.set_master_password(password)
                    print("Мастер-пароль успешно установлен!")
                    return True
                else:
                    print("Пароль должен содержать минимум 6 символов.")
            else:
                print("Пароли не совпадают. Попробуйте снова.")
    
    def authenticate(self):
        """Аутентификация пользователя"""
        stored_hash = self.db_manager.get_master_password()
        
        if not stored_hash:
            return self.setup_master_password()
        
        max_attempts = 3
        for attempt in range(max_attempts):
            password = getpass.getpass("Введите мастер-пароль: ")
            
            if self.db_manager.verify_master_password(password):
                print("Аутентификация успешна!")
                return True
            else:
                remaining = max_attempts - attempt - 1
                if remaining > 0:
                    print(f"Неверный пароль. Осталось попыток: {remaining}")
                else:
                    print("Превышено количество попыток. Выход.")
                    return False
        
        return False
    
    def add_password(self):
        """Добавить новый пароль"""
        print("\n--- Добавление нового пароля ---")
        
        name = input("Название/откуда (например, 'Google'): ").strip()
        if not name:
            print("Название не может быть пустым.")
            return
        
        login = input("Логин: ").strip()
        if not login:
            print("Логин не может быть пустым.")
            return
        
        # Генерируем пароль
        password = self.generate_password_interactive()
        if not password:
            return
        
        # Шифруем и сохраняем
        encrypted_password = self.encryption_manager.encrypt(password)
        self.db_manager.add_password(name, login, encrypted_password)
        
        print(f"\nПароль для '{name}' успешно сохранен!")
    
    def generate_password_interactive(self):
        """Интерактивная генерация пароля"""
        print("\n--- Генерация нового пароля ---")
        try:
            length = int(input(f"Длина пароля (по умолчанию 16): ") or 16)
            use_uppercase = input("Использовать заглавные буквы? (да/нет): ").lower() == 'да'
            use_lowercase = input("Использовать строчные буквы? (да/нет): ").lower() == 'да'
            use_digits = input("Использовать цифры? (да/нет): ").lower() == 'да'
            use_special = input("Использовать спецсимволы? (да/нет): ").lower() == 'да'
            
            # ПРОДВИНУТОЕ ЗАДАНИЕ: Вопрос об исключении похожих символов
            exclude_similar = input("Исключить похожие символы (0/O, l/I)? (да/нет): ").lower() == 'да'
            
            password = self.password_generator.generate(
                length=length,
                use_uppercase=use_uppercase,
                use_lowercase=use_lowercase,
                use_digits=use_digits,
                use_special=use_special,
                exclude_similar=exclude_similar  # ПРОДВИНУТОЕ ЗАДАНИЕ: Передаем новый параметр
            )
            
            print(f"\nСгенерированный пароль: {password}")
            return password
            
        except ValueError as e:
            print(f"Ошибка: {e}")
            return None
    
    def get_password(self):
        """Получить пароль по названию"""
        print("\n--- Получение пароля ---")
        name = input("Введите название: ").strip()
        
        if not name:
            print("Название не может быть пустым.")
            return
        
        record = self.db_manager.get_password(name)
        if not record:
            print(f"Пароль для '{name}' не найден.")
            return
        
        # Расшифровываем пароль
        decrypted_password = self.encryption_manager.decrypt(record[3])
        
        print(f"\nНазвание: {record[1]}")
        print(f"Логин: {record[2]}")
        print(f"Пароль: {decrypted_password}")
    
    def list_passwords(self):
        """Показать список всех паролей"""
        print("\n--- Список всех паролей ---")
        passwords = self.db_manager.list_passwords()
        
        if not passwords:
            print("Сохраненных паролей нет.")
            return
        
        print(f"{'ID':<5} {'Название':<20} {'Логин':<20} {'Создано'}")
        print("-" * 70)
        
        for password in passwords:
            print(f"{password[0]:<5} {password[1]:<20} {password[2]:<20} {password[3]}")
    
    def delete_password(self):
        """Удалить пароль"""
        print("\n--- Удаление пароля ---")
        name = input("Введите название для удаления: ").strip()
        
        if not name:
            print("Название не может быть пустым.")
            return
        
        if self.db_manager.delete_password(name):
            print(f"Пароль '{name}' успешно удален!")
        else:
            print(f"Пароль '{name}' не найден.")
    
    def show_menu(self):
        """Показать главное меню"""
        while True:
            print("\n" + "="*50)
            print("МЕНЕДЖЕР ПАРОЛЕЙ")
            print("="*50)
            print("1. Добавить новый пароль")
            print("2. Получить пароль")
            print("3. Список всех паролей")
            print("4. Удалить пароль")
            print("5. Создать новый пароль")
            print("0. Выход")
            print("="*50)
            
            choice = input("Выберите действие: ").strip()
            
            if choice == "1":
                self.add_password()
            elif choice == "2":
                self.get_password()
            elif choice == "3":
                self.list_passwords()
            elif choice == "4":
                self.delete_password()
            elif choice == "5":
                self.generate_password_interactive()
            elif choice == "0":
                print("До свидания!")
                break
            else:
                print("Неверный выбор. Попробуйте снова.")


def main():
    """Главная функция"""
    print("Запуск менеджера паролей...")
    
    manager = PasswordManager()
    
    if manager.authenticate():
        manager.show_menu()
    else:
        print("Ошибка аутентификации.")


if __name__ == "__main__":
    main()