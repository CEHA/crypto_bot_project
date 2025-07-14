import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional


"""
Модуль для планування та розкладу самовдосконалення.
"""
# Налаштування логування
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [ImprovementScheduler] - %(message)s') # Використовуємо глобальну конфігурацію
logger = logging.getLogger(__name__)


class ImprovementScheduler:
    """Клас для планування та розкладу завдань самовдосконалення.

    Керує чергою завдань для покращення системи, завантажуючи, зберігаючи
    та надаючи завдання для виконання. Також веде історію виконаних покращень.
    """

    def __init__(self, output_dir: str = ".") -> None:
        """Ініціалізує ImprovementScheduler.

        Args:
            output_dir (str): Коренева директорія для збереження файлів
                              завдань та історії самовдосконалення.
        """
        # Переконуємося, що output_dir є абсолютним шляхом
        if not os.path.isabs(output_dir):
            self.output_dir = os.path.abspath(output_dir)
        else:
            self.output_dir = output_dir

        self.tasks_file = os.path.join(self.output_dir, "improvement_tasks.json")
        self.history_file = os.path.join(self.output_dir, "improvement_history.json")

        # Створюємо директорію, якщо вона не існує
        os.makedirs(self.output_dir, exist_ok=True)

        tasks_file_existed = os.path.exists(self.tasks_file)

        self.tasks = self._load_tasks()
        self.history = self._load_history()

        # Якщо файл завдань не існував і ми завантажили завдання за замовчуванням, збережемо його
        if not tasks_file_existed and self.tasks:
            self._save_tasks()
            logger.info(f"Створено файл завдань за замовчуванням: {self.tasks_file}")

        logger.info(f"ImprovementScheduler ініціалізовано. Файл завдань: {self.tasks_file}")

    def _load_tasks(self) -> List[Dict[str, object]]:
        """Завантажує чергу завдань самовдосконалення з файлу.

        Якщо файл не існує або порожній, створює чергу за замовчуванням
        з одним завданням повного циклу самовдосконалення.

        Returns:
            List[Dict[str, object]]: Список завдань.
        """
        if os.path.exists(self.tasks_file):
            try:
                with open(self.tasks_file, "r", encoding="utf-8") as f:
                    tasks = json.load(f)
                    if tasks:  # Тільки якщо є завдання
                        logger.debug(f"Завантажено {len(tasks)} завдань з {self.tasks_file}")
                    return tasks
            except Exception as e:
                logger.error(
                    f"Помилка завантаження завдань з {self.tasks_file}: {e}. Створюється черга за замовчуванням."
                )

        logger.info(f"Файл завдань {self.tasks_file} не знайдено або порожній. Створення черги за замовчуванням.")
        # Створюємо стандартний список завдань для одного запуску.
        default_tasks = [
            {
                "id": f"default_full_cycle_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
                "type": "self_improvement",
                "improvement_type": "full_cycle",
                "description": "Стандартний повний цикл самовдосконалення.",
                "options": {
                    "analyze_architecture": True,
                    "improve_code_quality": True,
                    "update_documentation": True,
                    "run_tests": True,
                },
            }
        ]
        return default_tasks

    def _load_history(self) -> List[Dict[str, object]]:
        """Завантажує історію самовдосконалення з файлу.

        Returns:
            List[Dict[str, object]]: Список записів історії.
                                  Повертає порожній список у разі помилки або відсутності файлу.
        """
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Помилка при завантаженні історії: {e}")

        return []

    def _save_tasks(self) -> None:
        """Зберігає поточну чергу завдань самовдосконалення у файл."""
        try:
            with open(self.tasks_file, "w", encoding="utf-8") as f:
                json.dump(self.tasks, f, indent=2, ensure_ascii=False)
            logger.debug(f"Чергу завдань збережено у файл {self.tasks_file}")
        except Exception as e:
            logger.error(f"Помилка при збереженні черги завдань: {e}")

    def _save_history(self) -> None:
        """Зберігає поточну історію самовдосконалення у файл."""
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Помилка при збереженні історії: {e}")

    def add_task(
        self, improvement_type: str, options: Optional[Dict[str, object]] = None, description: str = ""
    ) -> None:
        """Додає завдання самовдосконалення в чергу.

        Args:
            improvement_type (str): Тип самовдосконалення (наприклад, 'full_cycle').
            options (Optional[Dict[str, object]]): Додаткові опції для завдання.
            description (str): Опис завдання.
        """
        task_id = f"{improvement_type}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        task = {
            "id": task_id,
            "type": "self_improvement",
            "improvement_type": improvement_type,
            "description": description or f"Завдання на самовдосконалення типу '{improvement_type}'",
            "options": options or {},
        }
        self.tasks.append(task)
        self._save_tasks()
        logger.info(f"Додано завдання самовдосконалення '{improvement_type}' в чергу.")

    def get_next_task(self) -> Optional[Dict[str, object]]:
        """Повертає наступне завдання з черги для виконання.

        Видаляє завдання з черги та повертає його.

        Returns:
            Optional[Dict[str, object]]: Словник з даними завдання або None, якщо черга порожня.
        """
        if not self.tasks:
            return None

        task = self.tasks.pop(0)
        self._save_tasks()
        logger.info(
            f"Взято в обробку завдання самовдосконалення '{task.get('improvement_type')}' (ID: {task.get('id')})."
        )
        return task

    def record_improvement(self, task: Dict[str, object], result: Dict[str, object]) -> None:
        """Записує результат самовдосконалення в історію.

        Args:
            task (Dict[str, object]): Виконане завдання самовдосконалення.
            result (Dict[str, object]): Результат виконання завдання.
        """
        record = {
            "timestamp": datetime.now().isoformat(),
            "task_id": task.get("id", "unknown_task_id"),  # Використовуємо ID завдання
            "task_type": task.get("improvement_type", "unknown_type"),
            "status": result.get("status"),
            "changes_applied": len(result.get("improvement_results", {}).get("changes", [])),
            "backup_id": result.get("improvement_results", {}).get("backup_id"),
        }

        self.history.append(record)
        self._save_history()
        logger.info(f"Записано результат самовдосконалення для завдання {record['task_id']}: {record['status']}")

    def get_improvement_history(self, limit: int = 10) -> List[Dict[str, object]]:
        """Повертає історію самовдосконалення, відсортовану за часом.

        Args:
            limit (int): Максимальна кількість записів для повернення.

        Returns:
            List[Dict[str, object]]: Список останніх записів історії самовдосконалення.
        """
        return sorted(self.history, key=lambda x: x["timestamp"], reverse=True)[:limit]
