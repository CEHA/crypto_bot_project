"""Аналізатор логів для виявлення помилок та створення завдань."""

import hashlib
import json
import logging
import os
import re
from datetime import datetime
from typing import Dict, List, Optional


logger = logging.getLogger(__name__)


class LogAnalyzer:
    """Аналізує логи та створює завдання для виправлення помилок."""

    def __init__(self, output_dir: str) -> None:
        """Ініціалізує аналізатор логів."""
        self.output_dir = output_dir
        self.error_cache_file = os.path.join(output_dir, "error_cache.json")
        self.error_cache = self._load_error_cache()

    def _load_error_cache(self) -> Dict:
        """Завантажує кеш помилок."""
        if os.path.exists(self.error_cache_file):
            try:
                with open(self.error_cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007
                pass
        return {"errors": {}, "last_check": None}

    def _save_error_cache(self) -> None:
        """Зберігає кеш помилок."""
        try:
            with open(self.error_cache_file, "w", encoding="utf-8") as f:
                json.dump(self.error_cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Помилка збереження кешу помилок: {e}")

    def _get_error_id(self, error_text: str, file_path: str = "") -> str:
        """Генерує унікальний ID для помилки."""
        content = f"{error_text}:{file_path}"
        return hashlib.md5(content.encode()).hexdigest()[:12]

    def analyze_logs_before_clear(self, log_paths: List[str]) -> List[Dict]:
        """Аналізує логи перед їх очищенням та повертає завдання."""
        tasks = []

        for log_path in log_paths:
            if not os.path.exists(log_path):
                continue

            try:
                with open(log_path, "r", encoding="utf-8") as f:
                    content = f.read()

                if not content.strip():
                    continue

                errors = self._extract_errors(content)
                for error in errors:
                    error_id = self._get_error_id(error["message"], error.get("file", ""))

                    # Перевіряємо чи помилка ще існує
                    if self._error_still_exists(error):
                        if error_id not in self.error_cache["errors"]:
                            task = self._create_fix_task(error, error_id)
                            if task:
                                tasks.append(task)
                                self.error_cache["errors"][error_id] = {
                                    "message": error["message"],
                                    "file": error.get("file", ""),
                                    "created": datetime.now().isoformat(),
                                    "attempts": 0,
                                }
                    else:
                        # Помилка виправлена, видаляємо з кешу
                        if error_id in self.error_cache["errors"]:
                            del self.error_cache["errors"][error_id]

            except Exception as e:
                logger.error(f"Помилка аналізу логу {log_path}: {e}")

        self.error_cache["last_check"] = datetime.now().isoformat()
        self._save_error_cache()
        return tasks

    def _extract_errors(self, log_content: str) -> List[Dict]:
        """Витягує помилки з логів."""
        errors = []

        # Патерни для різних типів помилок
        patterns = [
            # Python traceback
            (r"Traceback \(most recent call last\):(.*?)(?=\n\d{4}-\d{2}-\d{2}|\n[A-Z]+:|\Z)", "python_traceback"),
            # Import errors
            (r"ImportError: (.+)", "import_error"),
            # Syntax errors
            (r"SyntaxError: (.+)", "syntax_error"),
            # Module not found
            (r"ModuleNotFoundError: (.+)", "module_not_found"),
            # Attribute errors
            (r"AttributeError: (.+)", "attribute_error"),
            # General ERROR logs
            (r"ERROR:[^:]+:(.+)", "general_error"),
        ]

        for pattern, error_type in patterns:
            matches = re.finditer(pattern, log_content, re.DOTALL | re.MULTILINE)
            for match in matches:
                error_text = match.group(1).strip()
                file_match = re.search(r'File "([^"]+)"', error_text)

                errors.append(
                    {
                        "type": error_type,
                        "message": error_text[:500],  # Обмежуємо довжину
                        "file": file_match.group(1) if file_match else "",
                        "full_text": match.group(0),
                    }
                )

        return errors

    def _error_still_exists(self, error: Dict) -> bool:
        """Перевіряє чи помилка ще існує."""
        if error["type"] == "syntax_error" and error.get("file"):
            try:
                import ast

                with open(error["file"], "r", encoding="utf-8") as f:
                    ast.parse(f.read())
                return False  # Синтаксис виправлено
            except (SyntaxError, FileNotFoundError):
                return True

        if error["type"] == "import_error":
            module_name = re.search(r"No module named '([^']+)'", error["message"])
            if module_name:
                try:
                    __import__(module_name.group(1))
                    return False  # Модуль тепер доступний
                except ImportError:  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007
                    return True

        # Для інших типів помилок припускаємо що вони ще існують
        return True

    def _create_fix_task(self, error: Dict, error_id: str) -> Optional[Dict]:
        """Створює завдання для виправлення помилки."""
        task_id = f"fix-{error['type']}-{error_id}"

        if error["type"] == "syntax_error":
            return {
                "id": task_id,
                "type": "code_fix",
                "priority": "high",
                "description": f"Виправити синтаксичну помилку: {error['message'][:100]}",
                "target_file": error.get("file", ""),
                "error_type": "syntax",
                "error_details": error["message"],
                "created": datetime.now().isoformat(),
                "source": "log_analyzer",
            }

        elif error["type"] == "import_error":
            return {
                "id": task_id,
                "type": "dependency_fix",
                "priority": "medium",
                "description": f"Виправити помилку імпорту: {error['message'][:100]}",
                "error_type": "import",
                "error_details": error["message"],
                "created": datetime.now().isoformat(),
                "source": "log_analyzer",
            }

        elif error["type"] == "attribute_error":
            return {
                "id": task_id,
                "type": "code_fix",
                "priority": "medium",
                "description": f"Виправити помилку атрибуту: {error['message'][:100]}",
                "target_file": error.get("file", ""),
                "error_type": "attribute",
                "error_details": error["message"],
                "created": datetime.now().isoformat(),
                "source": "log_analyzer",
            }

        return None

    def mark_error_fixed(self, error_id: str) -> None:
        """Позначає помилку як виправлену."""
        if error_id in self.error_cache["errors"]:
            del self.error_cache["errors"][error_id]
            self._save_error_cache()

    def get_pending_errors(self) -> List[str]:
        """Повертає список ID невиправлених помилок."""
        return list(self.error_cache["errors"].keys())
