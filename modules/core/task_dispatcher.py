"""Модуль диспетчера завдань для crypto_bot_project."""

import importlib
import logging
from typing import TYPE_CHECKING, Callable, Dict, Optional

from modules.core.task_queue import TaskQueue


# Налаштування логування
logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from dev_agent import DevAgent  # Для анотації типів, щоб уникнути циклічного імпорту


class TaskDispatcher:
    """Диспетчер завдань, який розподіляє завдання між обробниками."""

    def __init__(self, queue: TaskQueue, agent_instance: Optional["DevAgent"] = None) -> None:
        """Метод __init__."""
        # Черга завдань
        self.queue = queue
        # Реєстр обробників завдань: {тип_завдання: обробник}
        self.handlers: Dict[str, Callable] = {}
        # Реєстр модулів: {назва_модуля: модуль}
        self.modules = {}
        # Зберігаємо екземпляр агента
        self.agent_instance = agent_instance
        if self.agent_instance:
            logger.debug(f"TaskDispatcher ініціалізовано з екземпляром агента: {self.agent_instance}")
        else:
            logger.warning("TaskDispatcher ініціалізовано БЕЗ екземпляра агента. Це може призвести до помилок.")

    def register_handler(self, task_type: str, module_name: str, function_name: str) -> None:
        """Реєструє обробник для певного типу завдань."""
        try:
            # Динамічно імпортуємо модуль, якщо він ще не імпортований
            if module_name not in self.modules:
                self.modules[module_name] = importlib.import_module(module_name)

            # Отримуємо функцію-обробник з модуля
            module = self.modules[module_name]
            handler = getattr(module, function_name)

            # Реєструємо обробник для типу завдання
            self.handlers[task_type] = handler
            logger.info(f"Зареєстровано обробник для типу '{task_type}': {module_name}.{function_name}")
        except ImportError:  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa  # noqa  # noqa: B007
            logger.error(f"Не вдалося імпортувати модуль '{module_name}'", exc_info=True)
        except AttributeError:  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa  # noqa  # noqa: B007
            logger.error(f"Функція '{function_name}' не знайдена в модулі '{module_name}'", exc_info=True)

    def process_next_task(self) -> bool:
        """Обробляє наступне завдання з черги."""
        # Отримуємо наступне завдання
        task = self.queue.get_next_task()
        if not task:
            # logger.info("Немає завдань для обробки") # Може бути занадто багато логів
            return False

        # Отримуємо тип завдання
        task_type = task.get("type")
        if not task_type:
            self.queue.mark_failed(task, "Завдання не містить поля 'type'")
            return True

        # Отримуємо обробник для типу завдання
        handler = self.handlers.get(task_type)
        if not handler:
            self.queue.mark_failed(task, f"Не знайдено обробник для типу '{task_type}'")
            return True

        # Виконуємо завдання
        try:
            logger.info(f"Виконання завдання типу '{task_type}' (ID: {task.get('added_time', 'N/A')})")
            if not self.agent_instance:
                logger.error(
                    f"Agent instance not available in TaskDispatcher for task type '{task_type}'. Cannot proceed."
                )
                self.queue.mark_failed(task, "Agent instance not available in TaskDispatcher.")
                return True  # Повертаємо True, щоб обробити наступне завдання, якщо є
            result = handler(task, agent=self.agent_instance)

            # Перевіряємо, чи обробник повернув помилку
            if isinstance(result, dict) and result.get("status") == "error":
                error_message = result.get("message", "Handler returned an error status.")
                logger.error(
                    f"Завдання типу '{task_type}' (ID: {task.get('added_time', 'N/A')}) завершилося з помилкою: {error_message}",
                    extra={"task_id": task.get("added_time"), "task_type": task_type, "error_message": error_message},
                )
                self.queue.mark_failed(task, error_message)
            else:
                self.queue.mark_completed(task, result)
        except Exception as e:
            logger.error(f"Помилка при виконанні завдання типу '{task_type}': {e}", exc_info=True)
            self.queue.mark_failed(task, str(e))

        return True

    def process_all_tasks(self) -> int:
        """Обробляє всі завдання в черзі."""
        count = 0
        while self.process_next_task():
            count += 1
        return count
