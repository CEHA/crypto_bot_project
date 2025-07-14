import ast  # New import
import logging
import os
import re
import subprocess
from typing import TYPE_CHECKING, Dict, Optional

from modules.core.agent_core import AgentCore, TaskHandler


# code_generation_module.py  # type: ignore


if TYPE_CHECKING:
    from dev_agent import DevAgent

logger = logging.getLogger(__name__)


class CodeGenerationModule(AgentCore, TaskHandler):
    """Модуль для генерації коду за описом."""

    def __init__(self, gemini_interaction, json_analyzer, output_dir: str) -> None:
        """Метод __init__."""
        super().__init__(gemini_interaction, json_analyzer)
        self.output_dir = output_dir
        logger.info("CodeGenerationModule ініціалізовано")

    def handle_task(self, task: Dict[str, object], agent: Optional["DevAgent"] = None) -> Dict[str, object]:
        """Обробляє завдання генерації коду."""
        description = task.get("description")
        output_file_rel = task.get("output_file")
        overwrite = task.get("overwrite", False)

        if not description or not output_file_rel:
            return {"status": "error", "message": "Завдання генерації коду не містить 'description' або 'output_file'."}

        output_file_abs = os.path.join(self.output_dir, output_file_rel)

        if os.path.exists(output_file_abs) and not overwrite:
            return {"status": "skipped", "message": f"Файл {output_file_rel} вже існує, і перезапис не дозволено."}

        logger.info(f"Генерація коду у файл '{output_file_rel}' за описом: {description[:100]}...")

        prompt_parts = [
            "Ти - експерт-розробник програмного забезпечення на Python. Твоє завдання - написати чистий, ефективний та добре документований код.",
            "Згенеруй повний код для Python-модуля на основі наступного опису:",
            f"--- ОПИС ЗАВДАННЯ ---\n{description}\n--- КІНЕЦЬ ОПИСУ ---",
            "Вимоги до коду:",
            "- Код має бути повним і готовим до запису у файл.",
            "- Дотримуйся стандартів PEP 8.",
            "- Додай докстрінги у стилі Google для всіх класів та публічних методів.",
            "- Використовуй сучасні можливості Python (наприклад, анотації типів).",
            "Твоя відповідь повинна містити ТІЛЬКИ Python код. Не додавай жодних пояснень, коментарів чи markdown-обгорток (```python ... ```).",
        ]  # Ensure Gemini knows to only return valid Python code

        generated_code = self.gemini_interaction.generate_content(
            prompt_parts=prompt_parts, generation_config={"response_mime_type": "text/plain"}
        )

        if not generated_code or not generated_code.strip():
            logger.error(f"Gemini не повернув код для завдання: {description[:100]}...")
            return {"status": "error", "message": "Gemini не згенерував вміст."}

        cleaned_code = re.sub(r"^\s*```python\s*|\s*```\s*$", "", generated_code.strip(), flags=re.MULTILINE)

        # Add a check to ensure the generated code is not empty after cleaning
        if not cleaned_code:
            logger.error(f"Generated code is empty after cleaning for task: {description[:100]}...")
            return {"status": "error", "message": "Gemini generated empty code."}

        # New: Validate syntax before writing to file
        try:
            ast.parse(cleaned_code)
            logger.debug(f"Згенерований код для {output_file_rel} синтаксично коректний.")
        except SyntaxError as se:
            error_msg = f"Згенерований код для файлу {output_file_rel} містить синтаксичні помилки: {se}"
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}

        try:
            os.makedirs(os.path.dirname(output_file_abs), exist_ok=True)
            with open(output_file_abs, "w", encoding="utf-8") as f:
                f.write(cleaned_code)
            logger.info(f"Код успішно згенеровано та збережено у файл {output_file_rel}")

            # Format and lint the generated file
            lint_ok = self._format_and_lint(output_file_abs)
            if not lint_ok:
                error_msg = (
                    f"Згенерований код у файлі {output_file_rel} містить синтаксичні помилки, які не вдалося виправити."
                )
                logger.error(error_msg)
                # Optionally, delete the invalid file to prevent it from breaking imports
                # os.remove(output_file_abs)
                return {"status": "error", "message": error_msg}

            return {
                "status": "success",
                "message": f"Код успішно згенеровано у файл {output_file_rel}",
                "file_path": output_file_rel,
            }
        except IOError as e:
            logger.error(f"Помилка запису у файл {output_file_abs}: {e}", exc_info=True)
            return {"status": "error", "message": f"Помилка запису у файл: {e}"}

    def _format_and_lint(self, file_path: str) -> bool:
        """Форматує та перевіряє згенерований код за допомогою ruff."""
        try:
            # Run ruff check --fix. Use check=False as ruff might return non-zero even if it fixes things.
            check_result = subprocess.run(
                ["ruff", "check", file_path, "--fix", "--exit-zero"], capture_output=True, text=True, timeout=30
            )
            if check_result.returncode != 0 and "fixed" not in check_result.stderr.lower():
                logger.warning(f"Ruff check --fix повернув помилку для {file_path}: {check_result.stderr}")
                return False

            # Run ruff format after fixing
            format_result = subprocess.run(["ruff", "format", file_path], capture_output=True, text=True, timeout=30)
            if format_result.returncode != 0:
                logger.warning(f"Ruff format повернув помилку для {file_path}: {format_result.stderr}")
                return False
            logger.info(f"Згенерований файл {file_path} успішно перевірено та відформатовано.")
            return True
        except FileNotFoundError:  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa  # noqa
            logger.warning("Команда 'ruff' не знайдена. Пропускаємо форматування та лінтинг.")
            return True
        except subprocess.TimeoutExpired:
            logger.warning(f"Форматування/лінтинг файлу {file_path} перервано через перевищення часу.")
            return False
        except Exception as e:  # Catch any other unexpected errors
            logger.warning(f"Невідома помилка під час форматування/лінтингу файлу {file_path}: {e}", exc_info=True)
            return False
