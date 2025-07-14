import ast
import glob
import json
import logging
import os
import re
from typing import Dict, List, Optional

from modules.core.task_queue import TaskQueue
from modules.utils.code_fixer import fix_file_automatically
from modules.utils.git_module import GitModule


logger = logging.getLogger(__name__)


class CodeFixer:
    """Клас для автоматичного виправлення коду."""

    def __init__(
        self,
        gemini_interaction,
        output_dir: str = ".",
        json_analyzer=None,
        task_queue: Optional[TaskQueue] = None,
        agent_config: Optional[Dict] = None,
        test_integration_module=None,
        github_token: Optional[str] = None,
        repo_owner: Optional[str] = None,
        repo_name: Optional[str] = None,
    ) -> None:
        self.gemini_interaction = gemini_interaction
        self.json_analyzer = json_analyzer
        self.output_dir = output_dir
        self.test_integration_module = test_integration_module
        self.task_queue = task_queue
        self.agent_config = agent_config or {}

        # Ініціалізуємо GitModule
        if not github_token:
            github_token = os.getenv("GITHUB_TOKEN")
        if not repo_owner:
            repo_owner = os.getenv("GITHUB_REPO_OWNER")
        if not repo_name:
            repo_name = os.getenv("GITHUB_REPO_NAME")

        self.git_module = GitModule(
            self.output_dir, github_token=github_token, repo_owner=repo_owner, repo_name=repo_name
        )

        self.max_fix_attempts = 3
        self.error_patterns = self._load_error_patterns()
        self.fix_history = {}

    def _load_error_patterns(self) -> Dict[str, Dict]:
        """Завантажує шаблони помилок та стратегії їх виправлення."""
        patterns = {
            "ImportError": {"strategy": "fix_import", "priority": 1, "auto_fix": True},
            "SyntaxError": {"strategy": "fix_syntax", "priority": 1, "auto_fix": True},
            "TypeError": {"strategy": "fix_type", "priority": 2, "auto_fix": True},
            "AttributeError": {"strategy": "fix_attribute", "priority": 3, "auto_fix": False},
        }

        logger.info(f"CodeFixer ініціалізовано для {self.output_dir}")
        logger.debug(f"Максимум спроб виправлення: {self.max_fix_attempts}")
        logger.debug(f"Завантажено {len(patterns)} шаблонів помилок")

        return patterns

    def apply_auto_refactoring(self, file_path: str) -> Dict[str, object]:
        """Застосовує автоматичний рефакторинг до файлу."""
        if not os.path.exists(file_path):
            return {"status": "error", "message": f"Файл {file_path} не існує"}

        try:
            if fix_file_automatically(file_path):
                return {"status": "success", "changes": 1, "file": file_path}
            return {"status": "skipped", "message": "No changes needed", "file": file_path}
        except Exception as e:
            logger.error(f"Помилка при автоматичному рефакторингу {file_path}: {e}")
            return {"status": "error", "message": str(e), "file": file_path}

    def handle_documentation_generation(self, file_path: str) -> Dict[str, object]:
        """Generates or improves docstrings for classes and functions using Gemini."""
        if not self.gemini_interaction:
            logger.error("GeminiInteraction not initialized. Cannot generate docstrings.")
            return {"status": "error", "message": "GeminiInteraction not initialized."}

        if not os.path.exists(file_path):
            logger.warning(f"File {file_path} does not exist for docstring generation.")
            return {"status": "skipped", "message": f"File {file_path} does not exist."}

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                original_content = f.read()

            tree = ast.parse(original_content)
            lines = original_content.splitlines(True)
            modifications: List = []

            # Collect nodes that need docstrings
            for node in ast.walk(tree):
                if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
                    current_docstring = ast.get_docstring(node)
                    if not current_docstring or len(current_docstring.strip()) < 20:
                        source_segment = ast.get_source_segment(original_content, node)
                        if not source_segment:
                            continue

                        # Generate docstring using Gemini
                        prompt = (
                            "Generate a comprehensive Python docstring for the following code block in Google style. "
                            "The docstring should explain its purpose, arguments (if any), and what it returns (if applicable). "
                            "Respond with ONLY the raw docstring content, without the triple quotes.\n\n"
                            "Code block:\n"
                            "```python\n"
                            f"{source_segment}\n"
                            "```"
                        )
                        docstring_content = self.gemini_interaction.generate_content(
                            prompt_parts=[prompt], generation_config={"response_mime_type": "text/plain"}
                        )

                        if docstring_content:
                            cleaned_content = docstring_content.strip()
                            if cleaned_content.startswith('"""'):
                                cleaned_content = cleaned_content[3:]
                            if cleaned_content.endswith('"""'):
                                cleaned_content = cleaned_content[:-3]
                            cleaned_content = cleaned_content.strip()

                            indent_level = node.col_offset + 4
                            indent = " " * indent_level

                            formatted_lines = [
                                f'{indent}"""{line}' if i == 0 else f"{indent}{line}"
                                for i, line in enumerate(cleaned_content.splitlines())
                            ]
                            if len(formatted_lines) > 1:
                                formatted_lines[-1] += '"""'

                            else:
                                formatted_lines[0] += '"""'

                            formatted_docstring = "\n".join(formatted_lines) + "\n"

                            if current_docstring:
                                start_lineno = node.body[0].lineno - 1
                                end_lineno = node.body[0].end_lineno
                                modifications.append(("replace", start_lineno, end_lineno, formatted_docstring))
                            else:
                                insert_lineno = node.lineno
                                modifications.append(("insert", insert_lineno, None, formatted_docstring))

            if not modifications:
                return {
                    "type": "documentation",
                    "target": file_path,
                    "description": "No docstring improvements needed.",
                    "status": "skipped",
                }

            # Apply modifications
            modifications.sort(key=lambda x: x[1], reverse=True)

            for mod_type, start, end, docstring in modifications:
                if mod_type == "replace":
                    lines[start:end] = [docstring]
                elif mod_type == "insert":
                    lines.insert(start, docstring)

            new_content = "".join(lines)
            if new_content != original_content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                # Форматування виконується в fix_file_automatically
                logger.info(f"Generated/improved docstrings for {file_path}.")
                return {
                    "type": "documentation",
                    "target": file_path,
                    "description": "Generated/improved docstrings using Gemini.",
                    "status": "success",
                }

            return {
                "type": "documentation",
                "target": file_path,
                "description": "No effective changes made to docstrings.",
                "status": "skipped",
            }

        except Exception as e:
            logger.error(f"Error generating/improving docstrings for {file_path}: {e}", exc_info=True)
            return {"status": "error", "message": str(e), "file": file_path}

    def handle_architectural_improvement(self, file_paths: List[str], description: str) -> Dict[str, object]:
        """Використовує Gemini для автоматичного рефакторингу архітектури."""
        if not self.gemini_interaction:
            logger.error("GeminiInteraction не ініціалізовано.")
            return {"status": "error", "message": "GeminiInteraction не ініціалізовано."}

        all_file_contents: Dict = {}
        for path in file_paths:
            if not os.path.exists(path):
                logger.warning(f"Файл не знайдено: {path}. Пропускаємо.")
                continue
            with open(path, "r", encoding="utf-8") as f:
                all_file_contents[path] = f.read()

        if not all_file_contents:
            return {
                "type": "architecture_improvement",
                "description": "Не знайдено файлів для рефакторингу.",
                "status": "skipped",
            }

        files_for_prompt = "\n\n".join(
            [f"### Файл: `{path}`\n```python\n{content}\n```" for path, content in all_file_contents.items()]
        )

        prompt = (
            "Ти - експерт з архітектури Python. Я виявив архітектурну проблему в моєму проекті:\n"
            f"Опис проблеми: {description}\n\n"
            "Ця проблема стосується наступних файлів:\n"
            f"{files_for_prompt}\n\n"
            "Твоє завдання - рефакторити код у цих файлах, щоб вирішити цю архітектурну проблему. "
            "Надай ПОВНИЙ, ОНОВЛЕНИЙ вміст для КОЖНОГО файлу, який ти модифікуєш. "
            "Якщо файл не потребує модифікації, НЕ включай його у свою відповідь. "
            "Твоя відповідь ПОВИННА бути JSON-масивом об'єктів, де кожен об'єкт має два ключі: "
            "'file_path' (рядок, абсолютний шлях до файлу) та 'new_content' (рядок, повний новий вміст для цього файлу). "
            "НЕ включай жодного іншого тексту чи markdown поза JSON."
        )

        try:
            gemini_response_str = self.gemini_interaction.generate_content(
                prompt_parts=[prompt], generation_config={"response_mime_type": "application/json"}
            )

            if gemini_response_str and isinstance(gemini_response_str, str):
                if gemini_response_str.startswith("```json"):
                    gemini_response_str = gemini_response_str[len("```json") :].strip()
                if gemini_response_str.endswith("```"):
                    gemini_response_str = gemini_response_str[: -len("```")].strip()

            modified_files_data = json.loads(gemini_response_str)

            if not isinstance(modified_files_data, list):
                raise ValueError("Відповідь Gemini не є JSON-масивом.")

            changes_applied = 0
            for file_data in modified_files_data:
                file_path = file_data.get("file_path")
                new_content = file_data.get("new_content")

                if not file_path or not new_content:
                    logger.warning(f"Некоректний об'єкт файлу: {file_data}")
                    continue

                original_content = all_file_contents.get(file_path)
                if original_content is None:
                    logger.warning(f"Gemini запропонував змінити неіснуючий файл: {file_path}")
                    continue

                if original_content.strip() != new_content.strip():
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    # Форматування виконується в fix_file_automatically
                    changes_applied += 1
                    logger.info(f"Архітектурний рефакторинг застосовано: {file_path}")

            if changes_applied > 0:
                return {
                    "type": "architecture_improvement",
                    "description": f"Застосовано покращення до {changes_applied} файлів.",
                    "status": "success",
                }
            else:
                return {
                    "type": "architecture_improvement",
                    "description": "Gemini не запропонував змін.",
                    "status": "skipped",
                }

        except json.JSONDecodeError as e:
            logger.error(f"Помилка декодування JSON: {e}")
            return {"status": "error", "message": f"Некоректний формат відповіді: {e}", "file": "N/A"}
        except Exception as e:
            logger.error(f"Помилка при архітектурному покращенні: {e}", exc_info=True)
            return {"status": "error", "message": str(e), "file": "N/A"}

    def auto_fix_project(self, target_dir: str = None) -> Dict[str, object]:
        """Автоматично сканує та виправляє помилки в проекті."""
        target_dir = target_dir or self.output_dir
        results = {"fixed": [], "failed": [], "skipped": []}

        for root, _, files in os.walk(target_dir):
            if any(skip in root for skip in [".git", "__pycache__", ".venv"]):
                continue

            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    fix_result = self._auto_fix_file(file_path)

                    if fix_result["status"] == "success":
                        results["fixed"].append(fix_result)
                    elif fix_result["status"] == "error":
                        results["failed"].append(fix_result)
                    else:
                        results["skipped"].append(fix_result)

        return {
            "status": "success",
            "summary": f"Виправлено: {len(results['fixed'])}, Помилок: {len(results['failed'])}, Пропущено: {len(results['skipped'])}",
            "details": results,
        }

    def _auto_fix_file(self, file_path: str) -> Dict[str, object]:
        """Автоматично виправляє один файл."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            try:
                ast.parse(content)
            except SyntaxError as e:
                return self.handle_runtime_error(f"SyntaxError in {file_path} line {e.lineno}: {e.msg}")

            if fix_file_automatically(file_path):
                return {"status": "success", "changes": 1, "file": file_path}
            return {"status": "skipped", "message": "No changes needed", "file": file_path}

        except Exception as e:
            return {"status": "error", "message": str(e), "file": file_path}

    def handle_runtime_error(self, error_description: str) -> Dict[str, object]:
        """Автоматично виправляє помилки виконання."""
        error_info = self._parse_error(error_description)
        if not error_info:
            return {"status": "skipped", "message": "Не вдалося розпарсити помилку"}

        file_path = error_info["file_path"]
        if not os.path.exists(file_path):
            return {"status": "skipped", "message": f"Файл {file_path} не існує"}

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                original_content = f.read()
        except Exception as e:
            return {"status": "error", "message": f"Помилка читання файлу: {e}"}

        for attempt in range(self.max_fix_attempts):
            logger.info(f"Спроба {attempt + 1}/{self.max_fix_attempts} для {file_path}")

            fix_result = self._attempt_fix(file_path, error_info, original_content, attempt)
            if fix_result["status"] == "success":
                return fix_result

            error_info["previous_attempts"] = error_info.get("previous_attempts", []) + [fix_result]

        return {"status": "error", "message": f"Не вдалося виправити після {self.max_fix_attempts} спроб"}

    def _parse_error(self, error_description: str) -> Optional[Dict[str, object]]:
        """Розширений парсинг помилок."""
        patterns = [
            r'File "([^"]+)", line (\d+).*?([\w\s]+Error): (.+)',
            r"([a-zA-Z/][a-zA-Z0-9/._-]+\.py)",
            r"([^:]+):(\d+):(\d+): (.+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, error_description)
            if match:
                groups = match.groups()
                return {
                    "file_path": self._resolve_path(groups[0]),
                    "line_number": int(groups[1]) if len(groups) > 1 and groups[1].isdigit() else None,
                    "error_type": groups[2] if len(groups) > 2 else "Unknown",
                    "message": groups[-1] if len(groups) > 1 else error_description,
                    "full_error": error_description,
                }
        return None

    def _resolve_path(self, path: str) -> str:
        """Розв'язує відносний шлях до абсолютного."""
        if os.path.isabs(path):
            return path
        return os.path.join(self.output_dir, path)

    def _attempt_fix(self, file_path: str, error_info: Dict, original_content: str, attempt: int) -> Dict[str, object]:
        """Одна спроба виправлення з контекстом."""
        prompt = self._build_fix_prompt(error_info, original_content, attempt)

        try:
            fixed_content = self.gemini_interaction.generate_content(
                prompt_parts=[prompt], generation_config={"response_mime_type": "text/plain"}
            )

            if not fixed_content or fixed_content.strip() == original_content.strip():
                return {"status": "failed", "message": "Gemini не надав змін"}

            validation_result = self._validate_fix(fixed_content)
            if validation_result["status"] != "success":
                return validation_result

            return self._apply_and_test_fix(file_path, error_info, original_content, fixed_content)

        except Exception as e:
            logger.error(f"Помилка під час виправлення: {e}")
            return {"status": "error", "message": str(e)}

    def _build_fix_prompt(self, error_info: Dict, content: str, attempt: int) -> str:
        """Створює контекстний промпт для виправлення."""
        base_prompt = f"""
Ти експерт Python розробник. Виправ наступну помилку:

Помилка: {error_info["message"]}
Тип: {error_info["error_type"]}
Файл: {error_info["file_path"]}
{f"Рядок: {error_info['line_number']}" if error_info.get("line_number") else ""}

Код:
{content}
Поверни ТІЛЬКИ виправлений код без пояснень.
"""

        if attempt > 0 and error_info.get("previous_attempts"):
            base_prompt += "\nПопередні спроби не вдалися. Спробуй інший підхід.\n"

        return base_prompt

    def _validate_fix(self, content: str) -> Dict[str, object]:
        """Валідує виправлений код."""
        try:
            ast.parse(content)
            return {"status": "success"}
        except SyntaxError as e:
            return {"status": "failed", "message": f"Синтаксична помилка: {e}"}

    def _apply_and_test_fix(self, file_path: str, error_info: Dict, original: str, fixed: str) -> Dict[str, object]:
        """Застосовує виправлення та тестує."""
        backup_path = f"{file_path}.backup"
        with open(backup_path, "w", encoding="utf-8") as f:
            f.write(original)

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(fixed)

            # Форматування виконується автоматично
            fix_file_automatically(file_path)

            if self.test_integration_module:
                test_result = self.test_integration_module.run_unit_tests(
                    target_files=[file_path], options={"quick": True}
                )

                if not test_result.get("tests_passed", False):
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(original)
                    return {"status": "failed", "message": "Тести не пройшли"}

            os.remove(backup_path)

            return {
                "status": "success",
                "type": "runtime_error_fix",
                "target": file_path,
                "description": f"Виправлено: {error_info['message']}",
            }

        except Exception as e:
            if os.path.exists(backup_path):
                with open(backup_path, "r", encoding="utf-8") as f:
                    with open(file_path, "w", encoding="utf-8") as out_f:
                        out_f.write(f.read())
                os.remove(backup_path)

            return {"status": "error", "message": f"Помилка застосування: {e}"}

    @staticmethod
    def cleanup_suggestion_files() -> None:
        """Видаляє файли з пропозиціями для рефакторингу."""
        patterns = ["**/*refactoring_suggestions.txt", "**/*dead_code_suggestions.txt", "**/*.backup", "**/*_fixed.py"]

        for pattern in patterns:
            for file in glob.glob(pattern, recursive=True):
                try:
                    os.remove(file)
                    logger.info(f"Видалено: {file}")
                except Exception as e:
                    logger.error(f"Помилка видалення {file}: {e}")
