import ast
import datetime
import json
import logging
import os
import subprocess
import sys
from typing import List, Optional


# Налаштування мінімального логування для bootstrap скрипта
logging.basicConfig(level=logging.INFO, format="%(asctime)s - [BOOTSTRAP] - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class StructuredJsonFormatter(logging.Formatter):
    """A custom formatter to output log records as structured JSON.

    This makes logs machine-readable, which is crucial for an autonomous agent
    that might need to parse its own logs to diagnose failures.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Метод format."""
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger_name": record.name,
        }
        # Add extra fields passed to the logger for more context
        if hasattr(record, "step"):
            log_record["step"] = record.step  # type: ignore
        if hasattr(record, "file_path"):
            log_record["file_path"] = record.file_path  # type: ignore
        if hasattr(record, "details"):
            log_record["details"] = record.details  # type: ignore

        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_record, ensure_ascii=False)


# Шлях до кореня проекту (де знаходиться bootstrap.py)
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")
REQUIREMENTS_FILE = os.path.join(PROJECT_ROOT, "requirements.txt")
MAIN_RUN_SCRIPT = os.path.join(PROJECT_ROOT, "run.py")

# Код виходу для критичної помилки, що потребує відкату
UNRECOVERABLE_ERROR_EXIT_CODE = 10


def _check_and_install_dependencies(requirements_path: str) -> bool:
    """Перевіряє та встановлює відсутні залежності з requirements.txt."""
    if not os.path.exists(requirements_path):
        logger.warning(f"Файл залежностей '{requirements_path}' не знайдено. Пропускаємо перевірку.")
        return True

    logger.info("Залежності вже встановлені.", extra={"step": "deps_check"})
    return True


def _attempt_ruff_fix(file_path: str) -> bool:
    """Спроба автоматично виправити синтаксичні помилки за допомогою ruff format."""
    logger.info(f"Спроба виправити синтаксис '{file_path}' за допомогою ruff format...")
    try:
        # Використовуємо ruff format, оскільки він може виправити базові синтаксичні проблеми
        result = subprocess.run(["ruff", "format", file_path], capture_output=True, text=True, check=False)
        if result.returncode == 0:
            logger.info(
                "Ruff успішно відформатував файл.",
                extra={"step": "syntax_fix_attempt", "tool": "ruff", "file_path": file_path},
            )
            return True
        else:
            logger.warning(
                "Ruff format не зміг виправити файл.",
                extra={"step": "syntax_fix_attempt", "tool": "ruff", "file_path": file_path, "details": result.stderr},
            )
            return False
    except FileNotFoundError:  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa  # noqa
        logger.warning("Ruff не знайдено. Переконайтеся, що він встановлений.")
        return False
    except Exception:  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa  # noqa
        logger.error(
            "Помилка під час виклику ruff для файлу.",
            extra={"step": "syntax_fix_attempt", "tool": "ruff", "file_path": file_path},
            exc_info=True,
        )
        return False


def _attempt_gemini_syntax_fix(file_path: str, error_message: str) -> Optional[str]:
    """Спроба виправити синтаксичну помилку за допомогою Gemini."""
    logger.info(f"Спроба виправити синтаксис у '{file_path}' за допомогою Gemini...")
    try:
        # Ця частина вимагає, щоб google-generativeai був встановлений
        import google.generativeai as genai
        from dotenv import load_dotenv

        load_dotenv()
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            logger.error("API ключ GOOGLE_API_KEY не знайдено для виправлення синтаксису.")
            return None

        genai.configure(api_key=api_key.split(",")[0])  # Використовуємо перший ключ
        model = genai.GenerativeModel("gemini-1.5-flash")

        with open(file_path, "r", encoding="utf-8") as f:
            original_content = f.read()

        prompt = (
            "Ти - експерт з Python, який виправляє синтаксичні помилки. Проаналізуй наступний код та повідомлення про помилку.\n"
            f"Помилка: ```\n{error_message}\n```\n\n"
            f"Оригінальний код файлу `{os.path.basename(file_path)}`:\n"
            "```python\n"
            f"{original_content}\n"
            "```\n\n"
            "Твоє завдання - виправити синтаксичну помилку в коді. Поверни ТІЛЬКИ повний оновлений код файлу. "
            "Не додавай жодних пояснень, коментарів чи ```python ... ``` обгорток."
        )

        response = model.generate_content(prompt)
        return response.text.strip()

    except ImportError:  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa  # noqa
        logger.error(
            "Не вдалося імпортувати google.generativeai. Пропускаємо виправлення.",
            extra={"step": "syntax_fix_attempt", "tool": "gemini", "file_path": file_path},
        )
        return None
    except Exception:  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa  # noqa
        logger.error(
            "Помилка під час виправлення синтаксису за допомогою Gemini.",
            extra={"step": "syntax_fix_attempt", "tool": "gemini", "file_path": file_path},
            exc_info=True,
        )
        return None


def _check_project_syntax(project_root: str) -> bool:
    """Перевіряє синтаксичну коректність всіх Python файлів у проекті, намагаючись їх виправити.

    Також виконує статичний аналіз за допомогою Ruff та Mypy.
    """
    logger.info("Початок перевірки синтаксису та статичного аналізу Python файлів...")
    all_ok = True
    python_files_to_check: List = []

    # Збираємо всі Python файли, виключаючи директорії, які не потрібно перевіряти
    for root, _, files in os.walk(project_root):
        # Пропускаємо директорії, які не потрібно перевіряти
        if any(d in root for d in [".venv", ".git", "__pycache__", "backups"]):
            continue
        for file in files:
            if file.endswith(".py"):
                python_files_to_check.append(os.path.join(root, file))

    # --- 1. Перевірка синтаксису (з Ruff та Gemini спробами виправлення) ---
    syntax_check_ok = True
    for full_path in python_files_to_check:
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                ast.parse(f.read(), filename=full_path)
        except SyntaxError as e:
            error_details = {"line": e.lineno, "offset": e.offset, "text": e.text.strip(), "message": e.msg}
            logger.error(
                f"Синтаксична помилка у файлі '{full_path}'.",
                extra={"step": "syntax_check", "file_path": full_path, "details": error_details},
            )
            syntax_check_ok = False  # Позначаємо, що є помилка

            # 1.1. Спробувати виправити за допомогою ruff format
            if _attempt_ruff_fix(full_path):
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        ast.parse(f.read(), filename=full_path)
                    logger.info(
                        "Ruff успішно виправив синтаксис у файлі.",
                        extra={"step": "syntax_fix_success", "tool": "ruff", "file_path": full_path},
                    )
                    syntax_check_ok = True  # Помилку виправлено
                    continue
                except SyntaxError:  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa  # noqa
                    logger.warning(
                        "Ruff не зміг виправити синтаксичну помилку. Спроба з Gemini.",
                        extra={"step": "syntax_fix_fail", "tool": "ruff", "file_path": full_path},
                    )

            # 1.2. Якщо ruff не допоміг, спробувати виправити за допомогою Gemini
            fixed_code = _attempt_gemini_syntax_fix(full_path, str(e))
            if fixed_code:
                try:
                    ast.parse(fixed_code, filename=full_path)
                    with open(full_path, "w", encoding="utf-8") as f:
                        f.write(fixed_code)
                    logger.info(
                        "Gemini успішно виправив синтаксис у файлі.",
                        extra={"step": "syntax_fix_success", "tool": "gemini", "file_path": full_path},
                    )
                    syntax_check_ok = True  # Помилку виправлено
                except SyntaxError as se_after_gemini:
                    logger.error(
                        "Gemini згенерував некоректний код.",
                        extra={
                            "step": "syntax_fix_fail",
                            "tool": "gemini",
                            "file_path": full_path,
                            "details": str(se_after_gemini),
                        },
                    )
            else:
                logger.error(
                    "Не вдалося виправити синтаксичну помилку у файлі.",
                    extra={"step": "syntax_fix_fail", "tool": "gemini", "file_path": full_path},
                )

    if not syntax_check_ok:
        all_ok = False  # Якщо синтаксичні помилки залишилися, загальна перевірка завершується невдачею

    # --- 2. Перевірка лінтингу за допомогою Ruff ---
    logger.info("Запуск Ruff Linting Check...", extra={"step": "ruff_lint_check"})
    try:
        # Запускаємо ruff check без --fix, щоб просто повідомити про проблеми
        # Використовуємо --exit-code-violations, щоб забезпечити ненульовий код виходу, якщо знайдені порушення
        ruff_result = subprocess.run(
            ["ruff", "check", project_root],  # Перевіряємо весь корінь проекту
            capture_output=True,
            text=True,
            check=False,
        )
        if ruff_result.returncode != 0:
            logger.error(
                f"Ruff Linting виявив проблеми:\n{ruff_result.stdout}\n{ruff_result.stderr}",
                extra={"step": "ruff_lint_check", "details": ruff_result.stdout + ruff_result.stderr},
            )
            all_ok = False
        else:
            logger.info("Ruff Linting пройшов успішно. Код відповідає стандартам.", extra={"step": "ruff_lint_check"})
    except FileNotFoundError:  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa  # noqa
        logger.warning("Ruff не знайдено. Пропускаємо Ruff Linting Check.")
    except Exception as e:
        logger.error(f"Помилка під час Ruff Linting Check: {e}", exc_info=True)
        all_ok = False

    # --- 3. Перевірка типів за допомогою Mypy ---
    logger.info("Запуск Mypy Type Checking...", extra={"step": "mypy_type_check"})
    try:
        # Mypy потрібно запускати з кореня проекту, щоб правильно знайти pyproject.toml  # type: ignore
        mypy_result = subprocess.run(
            [sys.executable, "-m", "mypy", project_root],  # Перевіряємо весь корінь проекту
            cwd=project_root,  # Запускаємо з кореня проекту
            capture_output=True,
            text=True,
            check=False,
        )
        if mypy_result.returncode != 0:
            logger.error(
                f"Mypy Type Checker виявив проблеми:\n{mypy_result.stdout}\n{mypy_result.stderr}",
                extra={"step": "mypy_type_check", "details": mypy_result.stdout + mypy_result.stderr},
            )
            all_ok = False
        else:
            logger.info("Mypy Type Checker пройшов успішно. Типи коректні.", extra={"step": "mypy_type_check"})
    except FileNotFoundError:  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa  # noqa
        logger.warning("Mypy не знайдено. Пропускаємо Mypy Type Checking.")
    except Exception as e:
        logger.error(f"Помилка під час Mypy Type Checking: {e}", exc_info=True)
        all_ok = False

    return all_ok


def setup_bootstrap_logging() -> None:
    """Налаштовує логування для bootstrap скрипта: структуроване у файл та читабельне у консоль."""
    # Видаляємо існуючі обробники, щоб уникнути дублювання
    root_logger = logging.getLogger()
    if root_logger.handlers:
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

    os.makedirs(LOGS_DIR, exist_ok=True)
    bootstrap_log_path = os.path.join(LOGS_DIR, "bootstrap.log")

    # Очищаємо лог-файл при запуску
    with open(bootstrap_log_path, "w") as f:
        f.truncate(0)

    # Обробник для запису структурованих JSON логів у файл
    json_file_handler = logging.FileHandler(bootstrap_log_path, encoding="utf-8")
    json_file_handler.setFormatter(StructuredJsonFormatter())

    # Обробник для виводу читабельних логів у консоль
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter("%(asctime)s - [BOOTSTRAP] - %(levelname)s - %(message)s"))

    # Налаштовуємо базову конфігурацію з обома обробниками
    logging.basicConfig(level=logging.INFO, handlers=[json_file_handler, console_handler], force=True)


def main() -> None:
    """Головна функція bootstrap скрипта."""
    setup_bootstrap_logging()
    logger.info("Запуск bootstrap скрипта...")

    if not _check_and_install_dependencies(REQUIREMENTS_FILE):
        logger.critical("Не вдалося встановити всі необхідні залежності. Запуск програми неможливий.")
        sys.exit(UNRECOVERABLE_ERROR_EXIT_CODE)

    # Автоматичний коміт перед перевіркою
    try:
        result = subprocess.run(["git", "add", "."], cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)
        if result.returncode == 0:
            commit_result = subprocess.run(
                [
                    "git",
                    "commit",
                    "-m",
                    f"auto: Автоматичний коміт перед bootstrap {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                ],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            if commit_result.returncode == 0:
                logger.info("Автоматичний коміт створено успішно.")
    except Exception as e:
        logger.debug(f"Автоматичний коміт не вдався: {e}")

    # Автоматичне виправлення помилок
    syntax_ok = _check_project_syntax(PROJECT_ROOT)
    if not syntax_ok:
        logger.warning("Виявлено помилки, спроба автовиправлення...")
        try:
            subprocess.run([sys.executable, MAIN_RUN_SCRIPT, "--mode", "auto"], check=True)
            logger.info("Автовиправлення завершено, продовжуємо запуск.")
        except subprocess.CalledProcessError:
            logger.error("Автовиправлення не вдалося, продовжуємо запуск.")

    logger.info("Запуск основної програми...")

    logger.info("Запуск основної програми...")

    try:
        subprocess.run([sys.executable, MAIN_RUN_SCRIPT] + sys.argv[1:], check=True)
    except subprocess.CalledProcessError as e:
        logger.critical("Основна програма завершилася з помилкою.", extra={"exit_code": e.returncode}, exc_info=True)
        sys.exit(e.returncode)
    except Exception:  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa  # noqa
        logger.critical("Невідома помилка під час запуску основної програми.", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
