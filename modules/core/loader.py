"""Основний модуль запуску системи для crypto_bot_project."""

import logging
import os
import signal
import sys
from datetime import datetime

from dotenv import load_dotenv

from modules.core.task_dispatcher import TaskDispatcher

# Імпорт компонентів системи управління завданнями
from modules.core.task_queue import TaskQueue


# --- Конфігурація ---
QUEUE_FILE = "task_queue.json"  # Файл для збереження стану черги

# Налаштування логування
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [Loader] - %(message)s') # Використовуємо глобальну конфігурацію
logger = logging.getLogger(__name__)


def check_api_keys(self) -> None:
    """Перевіряє наявність API ключів у змінних середовища."""
    load_dotenv()
    api_keys_str = os.getenv("GOOGLE_API_KEY")
    if not api_keys_str:
        logger.error("Змінна середовища GOOGLE_API_KEY не знайдена")
        return None

    api_keys = [key.strip() for key in api_keys_str.split(",") if key.strip()]
    if not api_keys:
        logger.error("Змінна середовища GOOGLE_API_KEY порожня або містить некоректні значення")
        return None

    logger.info(f"Знайдено {len(api_keys)} API ключ(ів) Gemini")
    return api_keys


def signal_handler(sig, frame) -> None:
    """Обробник сигналів для граційного завершення."""
    logger.info(f"Отримано сигнал {sig}. Завершуємо роботу...")
    sys.exit(0)


def register_task_handlers(dispatcher) -> None:
    """Реєструє обробники завдань у диспетчері."""
    try:
        # Реєструємо обробники для різних типів завдань
        dispatcher.register_handler("refactoring", "modules.core.task_handlers", "handle_refactoring_task")
        dispatcher.register_handler("query", "modules.core.task_handlers", "handle_query_task")
        dispatcher.register_handler("code_generation", "modules.core.task_handlers", "handle_code_generation_task")
        dispatcher.register_handler("test", "modules.core.task_handlers", "handle_test_task")
        dispatcher.register_handler("self_improvement", "modules.core.task_handlers", "handle_self_improvement_task")
        dispatcher.register_handler("analysis", "modules.core.task_handlers", "handle_analysis_task")
        dispatcher.register_handler("planning", "modules.core.task_handlers", "handle_planning_task")

        logger.info("Обробники завдань зареєстровано")
    except Exception as e:
        logger.error(f"Помилка при реєстрації обробників: {e}", exc_info=True)


def main() -> None:
    """Основна функція запуску системи."""
    # Налаштування обробників сигналів
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Перевіряємо наявність API ключів
    api_keys = check_api_keys()
    if not api_keys:
        logger.critical("Не знайдено API ключів. Зупинка.")
        sys.exit(1)

    # Створюємо чергу завдань
    queue = TaskQueue(QUEUE_FILE)

    # Створюємо диспетчер завдань
    # У режимі loader екземпляр агента не потрібен для TaskDispatcher
    dispatcher = TaskDispatcher(queue, agent_instance=None)

    # Реєструємо обробники завдань (можливо, це не потрібно в режимі loader, якщо він не обробляє завдання)
    register_task_handlers(dispatcher)

    # Перевіряємо наявність завдань у черзі
    stats = queue.get_stats()
    if stats["pending"] == 0 and stats["processing"] == 0:
        # Якщо немає завдань у черзі, завантажуємо з файлу
        logger.info("Немає завдань у черзі. Завантажуємо з файлу.")
        tasks = queue.load_tasks_from_file("tasks.json")  # Використовуємо рядок напряму
        if tasks:
            queue.add_tasks(tasks)
            logger.info(f"Додано {len(tasks)} завдань у чергу")
        else:
            logger.warning("Немає завдань для виконання")
            return

    # Виконуємо завдання послідовно
    logger.info("Початок виконання завдань")
    start_time = datetime.now()

    # Обробляємо всі завдання
    dispatcher.process_all_tasks()

    # Зберігаємо результати
    end_time = datetime.now()
    execution_time = (end_time - start_time).total_seconds()

    # Отримуємо статистику
    stats = queue.get_stats()

    # Виводимо підсумок
    logger.info("=== Підсумок виконання завдань ===")
    logger.info(f"Всього завдань: {stats['total']}")
    logger.info(f"Успішно виконано: {stats['completed']}")
    logger.info(f"Завершено з помилками: {stats['failed']}")
    logger.info(f"Загальний час виконання: {execution_time:.2f} секунд")


if __name__ == "__main__":
    main()
