"""Базові класи та інтерфейси для Meta-Agent."""

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Dict

from modules.utils.gemini_client import GeminiClient as GeminiInteraction


# Налаштування логування
logger = logging.getLogger(__name__)  # Залишаємо, оскільки це базовий клас

# Умовний імпорт для уникнення циклічних залежностей
if TYPE_CHECKING:
    from dev_agent import DevAgent
    from modules.utils.json_analyzer import JsonAnalyzer


class AgentCore:
    """Базовий клас для агентів."""

    def __init__(self, gemini_interaction: "GeminiInteraction", json_analyzer: "JsonAnalyzer") -> None:
        """Ініціалізує базовий клас агента.

        Args:
            gemini_interaction: Екземпляр GeminiInteraction для взаємодії з Gemini API
            json_analyzer: Екземпляр JsonAnalyzer для аналізу JSON
        """
        # Перевірка, чи GeminiInteraction та JsonAnalyzer є екземплярами, а не класами
        if not hasattr(gemini_interaction, "generate_content"):
            raise TypeError("gemini_interaction повинен мати метод generate_content.")
        if not hasattr(json_analyzer, "parse_json"):
            raise TypeError("json_analyzer повинен мати метод parse_json.")

        self.gemini_interaction = gemini_interaction
        self.json_analyzer = json_analyzer
        logger.info("AgentCore ініціалізовано")

    def generate_content(self, prompt_parts, **kwargs) -> object:
        """Генерує контент за допомогою Gemini API.

        Args:
            prompt_parts: Частини запиту
            **kwargs: Додаткові параметри для генерації

        Returns:
            Згенерований контент
        """
        return self.gemini_interaction.generate_content(prompt_parts, **kwargs)

    def parse_json(self, json_str) -> object:
        """Парсить JSON-рядок у Python-об'єкт.

        Args:
            json_str: JSON-рядок

        Returns:
            Python-об'єкт
        """
        return self.json_analyzer.parse_json(json_str)


class TaskHandler(ABC):
    """Інтерфейс для обробників завдань."""

    @abstractmethod
    def handle_task(self, task: Dict[str, object], agent: "DevAgent") -> Dict[str, object]:  # Додано параметр agent
        """Обробляє завдання.

        Args:
            task: Завдання для обробки
            agent: Екземпляр DevAgent для доступу до інших модулів

        Returns:
            Результат обробки завдання
        """
        pass  # Реалізація в конкретних обробниках
