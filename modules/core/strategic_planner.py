import json
import logging
from typing import Dict, List

from modules.core.planning_module import PlanningModule
from modules.core.project_analyzer import ProjectAnalyzer
from modules.core.scoring_system import ScoringSystem
from modules.gemini_client import GeminiClient


# Припускаємо, що ці модулі існують і мають відповідні методи


# Ініціалізуємо логер для цього модуля
logger = logging.getLogger(__name__)


class StrategicPlanner:
    """Модуль для аналізу стану проєкту, генерації ідей для покращення.

    та створення завдань для DevAgent.
    """

    def __init__(self, project_path: str) -> None:
        """Ініціалізує стратегічний планувальник.

        :param project_path: Шлях до кореневої директорії проєкту.
        """
        self.project_path = project_path
        self.project_analyzer = ProjectAnalyzer(project_path)
        self.planning_module = PlanningModule()
        self.scoring_system = ScoringSystem()
        self.gemini_client = GeminiClient()

    def run_self_improvement_cycle(self) -> List[Dict[str, object]]:
        """Запускає повний цикл самовдосконалення: аналіз, пропозиція, планування.

        :return: Список нових завдань для DevAgent.
        """
        logger.info("Запуск циклу стратегічного планування та самовдосконалення...")

        # 1. Фаза аналізу
        analysis_data = self._analyze_project()
        if not analysis_data:
            logger.warning("Аналіз проєкту не дав результатів. Пропускаємо цикл.")
            return []

        # 2. Фаза генерації ідей
        improvement_ideas = self._generate_improvement_ideas(analysis_data)

        # 3. Фаза пріоритезації
        if not improvement_ideas:
            logger.info("Не знайдено ідей для покращення. Проєкт у відмінному стані.")
            return []

        prioritized_idea = self.scoring_system.get_highest_priority_idea(improvement_ideas)
        logger.info(f"Обрано ідею з найвищим пріоритетом: {prioritized_idea.get('title', 'Без назви')}")

        # 4. Фаза декомпозиції (планування)
        new_tasks: List[Dict[str, object]] = self.planning_module.decompose_idea_into_tasks(prioritized_idea)
        logger.info(f"Згенеровано {len(new_tasks)} нових завдань.")

        return new_tasks

    def _analyze_project(self) -> Dict[str, object]:
        """Збирає аналітичні дані про проєкт."""
        logger.info("Проведення комплексного аналізу проєкту...")
        analysis_results: Dict[str, object] = {}
        try:
            logger.info("Аналіз складності коду...")
            analysis_results["complexity_report"] = self.project_analyzer.analyze_complexity()

            logger.info("Аналіз покриття тестами...")
            # Припускаємо, що в ProjectAnalyzer є або буде метод для аналізу покриття.
            # Наприклад, він може запускати `pytest --cov` і парсити результат.
            analysis_results["test_coverage_report"] = self.project_analyzer.analyze_test_coverage()

            # TODO: Додати виклики для аналізу продуктивності (cProfile), лінтерів (pylint/flake8) тощо.

            return analysis_results
        except Exception as e:
            logger.error(f"Помилка під час комплексного аналізу проєкту: {e}", exc_info=True)
            return analysis_results  # Повертаємо часткові результати, якщо вони є

    def _generate_improvement_ideas(self, analysis_data: Dict[str, object]) -> List[Dict[str, object]]:
        """Використовує Gemini для генерації ідей на основі аналітики."""
        logger.info("Генерація ідей для покращення за допомогою Gemini...")
        prompt = f"""Проаналізуй наступні метрики коду і запропонуй список ідей для покращення. Для кожної ідеї дай назву, детальний опис та оцінку важливості (priority) від 1 до 10. Відповідь надай у форматі JSON-масиву об'єктів. Кожен об'єкт повинен мати ключі: "title", "description", "priority". Дані аналізу: {json.dumps(analysis_data, indent=2, ensure_ascii=False)}"""

        try:
            response_text = self.gemini_client.generate_content(prompt)
            if response_text.strip().startswith("```json"):
                response_text = response_text.strip()[7:-3].strip()
            ideas: List[Dict[str, object]] = json.loads(response_text)
            logger.info(f"Gemini згенерував {len(ideas)} ідей для покращення.")
            return ideas
        except Exception as e:
            logger.error(f"Не вдалося обробити відповідь від Gemini: {e}")
            return []
