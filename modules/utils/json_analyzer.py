import json
import logging
import re
from typing import Dict, List, Optional, Union


"""
Модуль аналізу та обробки JSON для Meta-Agent.
"""
# Отримуємо логер, налаштований у run.py  # type: ignore
logger = logging.getLogger(__name__)

# Схема для валідації JSON
DETAILED_PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "project_description": {"type": "string"},
        "next_steps": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "step_number": {"type": "integer"},
                    "task": {"type": "string"},
                    "file_name": {"type": "string"},
                    "output_format": {"type": "string"},
                    "status": {"type": "string"},
                    "dependencies": {"type": "array", "items": {"type": "integer"}},
                },
                "required": ["step_number", "task", "file_name", "output_format", "status"],
            },
        },
        "completed_steps": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "step_number": {"type": "integer"},
                    "task": {"type": "string"},
                    "file_name": {"type": "string"},
                    "output_format": {"type": "string"},
                    "status": {"type": "string"},
                    "dependencies": {"type": "array", "items": {"type": "integer"}},
                },
                "required": ["step_number", "task", "file_name", "output_format", "status"],
            },
        },
    },
    "required": ["project_description", "next_steps"],
    "additionalProperties": True,
}


class JsonAnalyzer:
    """Клас для аналізу та обробки JSON."""

    def __init__(self, max_repair_attempts: int = 3) -> None:
        """Ініціалізує JsonAnalyzer."""
        self.max_repair_attempts = max_repair_attempts
        logger.info("JsonAnalyzer ініціалізовано")

    def parse_json(self, json_str: str) -> Optional[Union[Dict[str, object], List[object]]]:
        """Парсить JSON-рядок у Python-об'єкт."""
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.warning(f"Помилка парсингу JSON: {e}")

            # Спроба виправити JSON
            repaired_json = self.repair_json(json_str)
            if repaired_json:
                try:
                    return json.loads(repaired_json)
                except json.JSONDecodeError:
                    logger.error("Не вдалося виправити JSON")

            return None

    def repair_json(self, json_str: str) -> Optional[str]:
        """Намагається виправити некоректний JSON."""
        # Спроба 1: Виправлення одинарних лапок на подвійні
        json_str = json_str.replace("'", '"')

        # Спроба 2: Виправлення незакритих лапок
        json_str = self._fix_unclosed_quotes(json_str)

        # Спроба 3: Виправлення відсутніх ком
        json_str = self._fix_missing_commas(json_str)

        # Спроба 4: Виправлення зайвих ком
        json_str = self._fix_trailing_commas(json_str)

        return json_str

    def _fix_unclosed_quotes(self, json_str: str) -> str:
        """Виправляє незакриті лапки в JSON."""
        # Знаходимо всі відкриті лапки
        quote_positions: List = []
        in_string = False
        escape_next = False

        for i, char in enumerate(json_str):
            if char == "\\" and not escape_next:
                escape_next = True
                continue

            if char == '"' and not escape_next:
                in_string = not in_string
                quote_positions.append(i)

            escape_next = False

        # Якщо кількість лапок непарна, додаємо закриваючу лапку в кінці
        if len(quote_positions) % 2 == 1:
            json_str += '"'

        return json_str

    def _fix_missing_commas(self, json_str: str) -> str:
        """Виправляє відсутні коми в JSON."""
        # Шаблон для пошуку місць, де має бути кома
        pattern = r"([\]\}])\s*([\{\[])"
        json_str = re.sub(pattern, r"\1,\2", json_str)

        return json_str

    """
    Метод validate_json.
    """

    """
    Метод validate_json.
    """

    """
    Метод validate_json.
    """

    """
    Метод validate_json.
    """

    """
    Метод validate_json.
    """

    """
    Метод validate_json.
    """

    """
    Метод validate_json.
    """

    """
    Метод validate_json.
    """

    """
    Метод validate_json.
    """

    def validate_json(self, json_obj: object, schema: Dict[str, object]) -> bool:
        """Валідує JSON-об'єкт за схемою."""
        # Перевіряємо тип
        if schema.get("type") == "object" and not isinstance(json_obj, dict):
            logger.warning(f"Очікувався об'єкт, отримано {type(json_obj)}")
            return False

        if schema.get("type") == "array" and not isinstance(json_obj, list):
            logger.warning(f"Очікувався масив, отримано {type(json_obj)}")
            return False

        # Перевіряємо обов'язкові поля
        if schema.get("type") == "object" and "required" in schema:
            for field in schema["required"]:
                if field not in json_obj:
                    logger.warning(f"Відсутнє обов'язкове поле: {field}")
                    return False

        # Перевіряємо властивості об'єкта
        if schema.get("type") == "object" and "properties" in schema:
            for field, field_schema in schema["properties"].items():
                if field in json_obj:
                    if not self.validate_json(json_obj[field], field_schema):
                        return False

        # Перевіряємо елементи масиву
        if schema.get("type") == "array" and "items" in schema:
            for item in json_obj:
                if not self.validate_json(item, schema["items"]):
                    return False

        return True

    def format_json(self, json_obj: object) -> str:
        """Форматує JSON-об'єкт у рядок."""
        return json.dumps(json_obj, indent=2, ensure_ascii=False)
