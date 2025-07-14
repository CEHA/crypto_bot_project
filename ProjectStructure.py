"""Модуль для створення базової структури проєкту."""

import configparser
import os
from typing import List


class ProjectStructureGenerator:
    """Генератор базової структури проєкту."""

    def __init__(self, project_name: str, base_path: str = ".") -> None:
        """Ініціалізує ProjectStructureGenerator.

        Args:
            project_name: Назва проєкту.
            base_path: Базовий шлях для створення проєкту (за замовчуванням - поточна директорія).
        """
        self.project_name = project_name
        self.base_path = base_path
        self.project_path = os.path.join(self.base_path, self.project_name)

    def create_directories(self, directories: List[str]) -> None:
        """Створює директорії проєкту.

        Args:
            directories: Список директорій для створення.
        """
        for directory in directories:
            path = os.path.join(self.project_path, directory)
            os.makedirs(path, exist_ok=True)
            print(f"Створено директорію: {path}")

    def create_files(self, files: List[str]) -> None:
        """Створює файли проєкту.

        Args:
            files: Список файлів для створення.
        """
        for file in files:
            path = os.path.join(self.project_path, file)
            if not os.path.exists(path):
                with open(path, "w") as f:
                    f.write("# Вміст файлу\n")  # Додаємо базовий вміст
                print(f"Створено файл: {path}")
            else:
                print(f"Файл вже існує: {path}")

    def create_config_file(self, config_data: dict, filename: str = "config.ini") -> None:
        """Створює файл конфігурації.

        Args:
            config_data: Словник з даними конфігурації.
            filename: Назва файлу конфігурації (за замовчуванням - config.ini).
        """
        config = configparser.ConfigParser()
        config.read_dict(config_data)

        config_path = os.path.join(self.project_path, filename)
        with open(config_path, "w") as configfile:
            config.write(configfile)
        print(f"Створено файл конфігурації: {config_path}")

    def generate(self) -> None:
        """Генерує структуру проєкту."""
        directories = [
            self.project_name,
            os.path.join(self.project_name, "src"),
            os.path.join(self.project_name, "tests"),
            os.path.join(self.project_name, "docs"),
        ]
        files = [
            os.path.join(self.project_name, "README.md"),
            os.path.join(self.project_name, "src", "__init__.py"),
            os.path.join(self.project_name, "tests", "__init__.py"),
            os.path.join(self.project_name, "requirements.txt"),
        ]
        config_data = {
            "DEFAULT": {
                "log_level": "INFO",
                "api_url": "https://api.example.com",
            },
            "DATABASE": {
                "host": "localhost",
                "port": "5432",
                "username": "user",
                "password": "password",
            },
        }

        self.create_directories(directories)
        self.create_files(files)
        self.create_config_file(config_data)


if __name__ == "__main__":
    generator = ProjectStructureGenerator(project_name="my_project")
    generator.generate()
