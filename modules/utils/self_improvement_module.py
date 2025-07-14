import json
import logging
import random
from datetime import datetime
from typing import Dict, List

from modules.core.agent_core import AgentCore, TaskHandler


# Ймовірно, застарілий модуль. Функціонал розділено між
# SelfAnalyzer, SelfImprover, DocumentationUpdater.
# Налаштування логування
# logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - [SelfImprovement] - %(message)s") # Використовуємо глобальну конфігурацію
logger = logging.getLogger(__name__)


class SelfImprovementModule(AgentCore, TaskHandler):
    """Модуль самополіпшення для Meta-Agent."""

    def __init__(self, gemini_interaction, json_analyzer, config_file="dev_agent_config.json") -> None:
        """Ініціалізує SelfImprovementModule.

        Args:
            gemini_interaction: Екземпляр GeminiInteraction для взаємодії з Gemini API.
            json_analyzer: Екземпляр JsonAnalyzer для обробки JSON.
            config_file (str): Шлях до файлу конфігурації агента.
        """
        super().__init__(gemini_interaction, json_analyzer)
        self.config_file = config_file
        logger.info("SelfImprovementModule ініціалізовано")

    def handle_task(self, task: Dict[str, object]) -> Dict[str, object]:
        """Обробляє завдання самополіпшення.

        Диспетчеризує завдання до відповідних методів на основі `improvement_type`.

        Args:
            task (Dict[str, object]): Словник, що містить деталі завдання самополіпшення.

        Returns:
            Dict[str, object]: Результат виконання завдання.
        """
        improvement_type = task.get("improvement_type")
        config = task.get("config", {})

        if improvement_type == "optimize_parameters":
            result = self.optimize_parameters(config)
            return {"status": "success", "config": result, "message": "Параметри успішно оптимізовано"}
        elif improvement_type == "analyze_performance":
            results = task.get("results", [])
            report = self.analyze_performance(results)
            return {"status": "success", "report": report, "message": "Аналіз продуктивності успішно виконано"}
        elif improvement_type == "improve_code_quality":
            file_path = task.get("file_path", "")
            result = self.improve_code_quality(file_path)
            return result
        else:
            return {"status": "error", "message": f"Тип самополіпшення '{improvement_type}' не підтримується"}

    def optimize_parameters(self, config: Dict[str, object]) -> Dict[str, object]:
        """Оптимізує параметри моделі на основі попередніх результатів.

        Вибирає нові значення параметрів з визначеного простору пошуку
        та зберігає оновлену конфігурацію.

        Args:
            config (Dict[str, object]): Поточна конфігурація для оптимізації.

        Returns:
            Dict[str, object]: Оновлена конфігурація.
        """
        logger.info("Оптимізація параметрів моделі")

        # Завантажуємо поточну конфігурацію
        current_config: Dict = {}
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                current_config = json.load(f)
        except Exception as e:
            logger.error(f"Помилка при завантаженні конфігурації: {e}")
            current_config: Dict = {}

        # Копіюємо конфігурацію, щоб не змінювати оригінал
        new_config = current_config.copy()

        # Визначаємо простір пошуку для параметрів
        search_space = {
            "temperature": [0.5, 0.7, 0.9],
            "max_output_tokens": [4096, 8192, 16384],
            "max_retries": [3, 5, 7],
            "initial_delay": [1, 2, 3],
            "max_delay": [5, 10, 15],
            "max_repair_attempts": [2, 3, 5],
        }

        # Оптимізуємо параметри моделі
        if "model_parameters" not in new_config:
            new_config["model_parameters"] = {}

        # Вибираємо нові значення параметрів
        new_config["model_parameters"]["temperature"] = random.choice(search_space["temperature"])
        new_config["model_parameters"]["max_output_tokens"] = random.choice(search_space["max_output_tokens"])
        new_config["max_retries"] = random.choice(search_space["max_retries"])
        new_config["initial_delay"] = random.choice(search_space["initial_delay"])
        new_config["max_delay"] = random.choice(search_space["max_delay"])
        new_config["max_repair_attempts"] = random.choice(search_space["max_repair_attempts"])

        # Зберігаємо час останньої оптимізації
        new_config["last_optimization_time"] = datetime.now().isoformat()

        logger.info(
            f"Нові параметри: temperature={new_config['model_parameters']['temperature']}, "
            f"max_output_tokens={new_config['model_parameters']['max_output_tokens']}, "
            f"max_retries={new_config['max_retries']}"
        )

        # Зберігаємо оновлену конфігурацію
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(new_config, f, indent=2, ensure_ascii=False)
            logger.info(f"Оновлену конфігурацію збережено у {self.config_file}")
        except Exception as e:
            logger.error(f"Помилка при збереженні конфігурації: {e}")

        return new_config

    def analyze_performance(self, results: List[Dict[str, object]]) -> Dict[str, object]:
        """Аналізує результати виконання завдань для виявлення проблем продуктивності.

        Підраховує статистику успішних/невдалих завдань та типи помилок.

        Args:
            results (List[Dict[str, object]]): Список результатів виконання завдань.

        Returns:
            Dict[str, object]: Звіт про аналіз продуктивності.
        """
        logger.info("Аналіз продуктивності")

        # Підраховуємо статистику
        total_tasks = len(results)
        successful_tasks = sum(1 for r in results if r.get("status") == "success")
        failed_tasks = sum(1 for r in results if r.get("status") == "error")

        # Аналізуємо помилки
        error_types: Dict = {}
        for result in results:
            if result.get("status") == "error":
                error_message = result.get("message", "")
                error_type = "unknown"

                if "timeout" in error_message.lower():
                    error_type = "timeout"
                elif "api" in error_message.lower():
                    error_type = "api_error"
                elif "import" in error_message.lower():
                    error_type = "import_error"
                elif "json" in error_message.lower():
                    error_type = "json_error"

                error_types[error_type] = error_types.get(error_type, 0) + 1

        # Формуємо звіт
        report = {
            "total_tasks": total_tasks,
            "successful_tasks": successful_tasks,
            "failed_tasks": failed_tasks,
            "success_rate": successful_tasks / total_tasks if total_tasks > 0 else 0,
            "error_types": error_types,
        }

        logger.info(
            f"Успішно виконано {successful_tasks}/{total_tasks} завдань (успішність: {report['success_rate']:.2%})"
        )

        return report

    def improve_code_quality(self, file_path: str) -> Dict[str, object]:
        """Покращує якість коду у вказаному файлі за допомогою Gemini.

        Надсилає вміст файлу Gemini та отримує покращений код,
        який потім зберігається у файлі.

        Args:
            file_path (str): Шлях до файлу для покращення.

        Returns:
            Dict[str, object]: Результат покращення якості коду.
        """
        logger.info(f"Покращення якості коду у файлі {file_path}")

        try:
            # Перевіряємо існування файлу
            import os

            if not os.path.exists(file_path):
                return {"status": "error", "message": f"Файл {file_path} не існує"}

            # Читаємо вміст файлу
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Формуємо запит для Gemini
            prompt_parts = [
                "Ти - AI-асистент для покращення якості коду.",
                f"Потрібно покращити якість коду у файлі {file_path}:",
                f"```python\n{content}\n```",
                "Покращ код, дотримуючись наступних принципів:",
                "1. Дотримання PEP 8",
                "2. Покращення читабельності",
                "3. Оптимізація продуктивності",
                "4. Додавання документації",
                "Поверни покращений код. Не додавай жодних пояснень.",
            ]

            response = self.gemini_interaction.generate_content(
                prompt_parts=prompt_parts, generation_config={"response_mime_type": "text/plain"}
            )

            if response:
                improved_code = response.strip()

                # Зберігаємо покращений код
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(improved_code)

                return {"status": "success", "file_path": file_path, "message": "Код успішно покращено"}

            return {"status": "error", "message": "Не вдалося покращити код"}
        except Exception as e:
            logger.error(f"Помилка при покращенні коду: {e}")
            return {"status": "error", "message": str(e)}

    def optimize_agent(self, config: Dict[str, object]) -> Dict[str, object]:
        """Головна функція для самополіпшення агента.

        Args:
            config (Dict[str, object]): Поточна конфігурація агента.

        Returns:
            Dict[str, object]: Оновлена конфігурація агента.
        """
        logger.info("Запуск самополіпшення агента")

        # Оптимізуємо параметри
        new_config = self.optimize_parameters(config)

        return new_config
