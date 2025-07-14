from typing import List


#!/usr/bin/env python3
"""Головний скрипт для запуску системи."""


import os
import site  # Import the site module
import sys


# --- BEGIN POTENTIAL FIX for user site-packages ---
# Add user site-packages directory to sys.path if not already present
# This is often handled automatically, but let's be explicit for troubleshooting
USER_SITE_PACKAGES = site.getusersitepackages()
if os.path.isdir(USER_SITE_PACKAGES) and USER_SITE_PACKAGES not in sys.path:
    sys.path.insert(0, USER_SITE_PACKAGES)  # Insert at a high-priority position
    print(f"[DEBUG] Explicitly added to sys.path: {USER_SITE_PACKAGES}")  # For debugging
# --- END POTENTIAL FIX ---
import argparse
import importlib.metadata  # type: ignore  # Замінено pkg_resources
import json
import logging
import logging.handlers  # type: ignore
import subprocess

from dotenv import load_dotenv


# Додаємо поточну директорію до шляху пошуку модулів
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# --- Розширена конфігурація логування ---
def setup_logging(debug_mode: bool = False, clear_log: bool = True) -> None:
    """Налаштовує логування у файл та консоль."""
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    # Визначаємо шляхи до лог-файлів
    main_log_path = os.path.join(log_dir, "agent.log")
    error_log_path = os.path.join(log_dir, "agent_errors.log")

    # Аналізуємо логи перед очищенням
    if clear_log:
        try:
            from modules.utils.log_analyzer import LogAnalyzer

            analyzer = LogAnalyzer(".")
            tasks = analyzer.analyze_logs_before_clear([main_log_path, error_log_path])
            if tasks:
                # Зберігаємо завдання для подальшого використання
                pending_tasks_file = "pending_error_fixes.json"
                existing_tasks = []
                if os.path.exists(pending_tasks_file):
                    try:
                        with open(pending_tasks_file, "r", encoding="utf-8") as f:
                            existing_tasks = json.load(f)
                    except Exception:  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007
                        pass

                existing_tasks.extend(tasks)
                with open(pending_tasks_file, "w", encoding="utf-8") as f:
                    json.dump(existing_tasks, f, indent=2, ensure_ascii=False)
                print(f"INFO: Створено {len(tasks)} завдань для виправлення помилок")
        except Exception as e:
            print(f"WARNING: Не вдалося проаналізувати логи: {e}")

        # Очищаємо лог-файли
        for log_path in [main_log_path, error_log_path]:
            if os.path.exists(log_path):
                try:
                    with open(log_path, "w") as f:
                        f.truncate(0)
                    print(f"INFO: Лог-файл {log_path} було очищено.")
                except Exception as e:
                    print(f"ERROR: Не вдалося очистити лог-файл {log_path}: {e}")

    log_level = logging.DEBUG if debug_mode else logging.INFO  # type: ignore

    # Створюємо ротуючий файл логів (наприклад, 10 файлів по 5MB)
    main_file_handler = logging.handlers.RotatingFileHandler(
        main_log_path, maxBytes=5 * 1024 * 1024, backupCount=10, encoding="utf-8"
    )
    main_file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    main_file_handler.setLevel(log_level)

    # Створюємо файл для помилок та попереджень (додаємо до файлу, оскільки він вже очищений)
    error_file_handler = logging.FileHandler(error_log_path, mode="a", encoding="utf-8")
    error_file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    error_file_handler.setLevel(logging.WARNING)

    # Налаштовуємо базову конфігурацію з обробниками
    if logging.root.handlers:
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
    logging.basicConfig(
        level=log_level, handlers=[main_file_handler, error_file_handler, logging.StreamHandler(sys.stdout)], force=True
    )
    logging.info("Логування налаштовано. Помилки та попередження будуть дублюватися в agent_errors.log.")


# Налаштування логування
logger = logging.getLogger(__name__)


def check_and_install_dependencies() -> bool:
    """Перевіряє та встановлює відсутні залежності з requirements.txt."""
    requirements_file = "requirements.txt"
    if not os.path.exists(requirements_file):
        logger.warning(f"Файл {requirements_file} не знайдено. Пропускаємо перевірку залежностей.")
        return False  # Повертаємо False, якщо файл не знайдено

    with open(requirements_file, "r") as f:
        dependencies = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    missing_dependencies: List = []
    installed_new_dependencies = False
    for dep in dependencies:
        try:
            # Розбираємо назву пакету (без версії, якщо вона є)
            package_name = (
                dep.split("==")[0]
                .split(">=")[0]
                .split("<=")[0]
                .split("!=")[0]
                .split("~=")[0]
                .split(">")[0]
                .split("<")[0]
            )
            importlib.metadata.distribution(package_name)
            logger.info(f"Залежність '{package_name}' вже встановлено.")
        except importlib.metadata.PackageNotFoundError:
            logger.warning(f"Залежність '{dep}' не знайдено. Буде спроба встановлення.")
            missing_dependencies.append(dep)
        except Exception as e:
            logger.error(f"Помилка при перевірці залежності '{dep}': {e}")
            missing_dependencies.append(dep)  # Спробуємо встановити на випадок помилки перевірки

    if missing_dependencies:
        logger.info("Встановлення відсутніх залежностей...")
        for dep in missing_dependencies:
            try:
                logger.info(f"Встановлення {dep}...")
                # Використовуємо sys.executable для гарантії використання правильного pip
                # Розгляньте можливість відмови від --break-system-packages на користь віртуальних середовищ
                # або принаймні зробіть це опціональним/конфігурованим.
                install_command = [sys.executable, "-m", "pip", "install", "--break-system-packages", dep]
                subprocess.check_call(install_command)
                installed_new_dependencies = True
                logger.info(f"Залежність '{dep}' успішно встановлено.")
            except subprocess.CalledProcessError as e:
                logger.error(
                    f"Помилка при встановленні залежності '{dep}': {e}. Будь ласка, встановіть її вручну.",
                    exc_info=True,
                )

    return installed_new_dependencies


_RUN_PY_DIR = os.path.dirname(os.path.abspath(__file__))  # Шлях до директорії, де знаходиться run.py  # type: ignore


def main() -> None:
    """Головна функція для запуску системи."""
    # Парсимо аргументи командного рядка
    parser = argparse.ArgumentParser(description="Запуск системи управління завданнями")
    parser.add_argument("--tasks", help="Шлях до файлу з завданнями", default="tasks.json")
    parser.add_argument("--config", help="Шлях до файлу конфігурації", default="dev_agent_config.json")
    parser.add_argument("--output", help="Директорія для вихідних файлів (корінь проекту)", default=".")
    parser.add_argument(
        "--mode", help="Режим запуску (agent, loader, auto, daemon або self-improve-direct)", default="agent"
    )
    # parser.add_argument("--self-improve", help="Запустити процес самовдосконалення", action="store_true") # Видалено, використовуйте --mode auto
    parser.add_argument(
        "--interval",
        help="Інтервал перевірки запланованих завдань (в секундах) для режиму daemon",
        type=int,
        default=60,
    )  # Змінено default на 60
    parser.add_argument("--debug", help="Увімкнути режим налагодження", action="store_true")
    parser.add_argument("--cleanup", help="Видалити файли з пропозиціями для рефакторингу", action="store_true")
    parser.add_argument("--no-clear-log", help="Не очищати файли логів перед запуском", action="store_true")
    parser.add_argument("--clear-cache", help="Очистити кеш Gemini перед запуском", action="store_true")
    args = parser.parse_args()

    # Перевіряємо та встановлюємо залежності перед іншими діями
    newly_installed = check_and_install_dependencies()
    if newly_installed:
        # Налаштовуємо логер, щоб повідомити користувача перед виходом.
        # Це важливо, оскільки setup_logging може бути ще не викликаний.
        setup_logging(debug_mode=args.debug, clear_log=not args.no_clear_log)
        logger.info("Було встановлено нові залежності. Будь ласка, перезапустіть скрипт, щоб зміни набули чинності.")
        sys.exit(0)

    # Налаштовуємо рівень логування
    setup_logging(debug_mode=args.debug, clear_log=not args.no_clear_log)
    logger.debug("Режим налагодження увімкнено" if args.debug else "Запуск у стандартному режимі.")

    # Очищуємо кеш, якщо вказано
    if args.clear_cache:
        cache_file = "gemini_cache.json"
        if os.path.exists(cache_file):
            os.remove(cache_file)
            logger.info(f"Файл кешу '{cache_file}' було видалено.")
        else:
            logger.info(f"Файл кешу '{cache_file}' не знайдено, очищення не потрібне.")

    # Імпортуємо DevAgent один раз на початку
    try:
        from dev_agent import DevAgent

        # Імпортуємо CodeFixer для функції очищення
        from modules.self_improvement.code_fixer import CodeFixer
    except ImportError:  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa  # noqa
        logger.error(
            "Не вдалося імпортувати DevAgent або CodeFixer. Перевірте, чи правильно встановлено всі залежності.",
            exc_info=True,
        )
        sys.exit(1)

    # Видаляємо файли з пропозиціями, якщо вказано
    if args.cleanup:
        try:
            # Викликаємо статичний метод для очищення файлів
            # output_dir не потрібен для цього методу, оскільки він використовує glob.
            CodeFixer.cleanup_suggestion_files()
            logger.info("Файли з пропозиціями успішно видалено.")
        except Exception as e:
            logger.error(f"Помилка під час очищення файлів з пропозиціями: {e}")
        return

    # Завантажуємо змінні середовища
    load_dotenv()

    # Перевіряємо наявність API ключів
    api_keys_str = os.getenv("GOOGLE_API_KEY")
    if not api_keys_str:
        logger.error("Не знайдено API ключів Gemini. Встановіть змінну середовища GOOGLE_API_KEY.")
        sys.exit(1)

    api_keys = [key.strip() for key in api_keys_str.split(",") if key.strip()]
    logger.info(f"Знайдено {len(api_keys)} API ключ(ів) Gemini")

    from modules.utils.config_manager import ConfigManager

    # Ініціалізуємо ConfigManager
    config_path = args.config  # type: ignore
    if not os.path.isabs(config_path):
        config_path = os.path.join(_RUN_PY_DIR, config_path)
    config_manager = ConfigManager(config_file=os.path.abspath(config_path))

    # Визначаємо шляхи: пріоритет - аргументи командного рядка, потім - конфігураційний файл, потім - значення за замовчуванням
    output_path = args.output if args.output != "." else config_manager.get("output_dir", ".")
    if not os.path.isabs(output_path):
        output_path = os.path.join(_RUN_PY_DIR, output_path)

    tasks_path = args.tasks if args.tasks != "tasks.json" else config_manager.get("tasks_file", "tasks.json")
    if not os.path.isabs(tasks_path):
        tasks_path = os.path.join(_RUN_PY_DIR, tasks_path)

    queue_path = os.path.join(output_path, "task_queue.json")

    logger.info(f"Використовується файл конфігурації: {config_manager.config_file}")
    logger.info(f"Використовується директорія виводу: {output_path}")
    logger.info(f"Використовується файл завдань: {tasks_path}")
    logger.info(f"Використовується файл черги завдань: {queue_path}")

    # Запускаємо систему в залежності від режиму
    if args.mode == "loader":
        # Запускаємо Loader
        try:
            from modules.core.loader import main as loader_main

            loader_main()
        except ImportError:  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa  # noqa
            logger.error("Не вдалося імпортувати modules.core.loader. Перевірте структуру проєкту.", exc_info=True)
            sys.exit(1)
    else:
        # Режими "agent", "auto", "daemon", "self_improve" вимагають DevAgent
        try:
            agent = DevAgent(
                config_manager=config_manager, output_dir=output_path, tasks_file=tasks_path, queue_file=queue_path
            )

            # Зберігаємо екземпляр агента глобально

            # agent_instance = agent  # Unused variable removed

            if args.mode == "auto":
                agent.register_handlers()
                agent.self_improve()
            elif args.mode == "daemon":
                agent.run_daemon(check_interval=args.interval)
            elif args.mode == "agent":
                agent.run()
            elif args.mode == "self-improve-direct":
                agent.register_handlers()
                agent.self_improve(direct=True)

        except Exception as e:
            logger.error(f"Помилка при запуску агента: {e}", exc_info=True)
            sys.exit(1)


if __name__ == "__main__":
    main()
