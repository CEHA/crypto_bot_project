import logging
from typing import TYPE_CHECKING, Dict, List, Optional

from modules.core.task_queue import TaskQueue
from modules.self_improvement.pull_request_monitor import PullRequestMonitor
from modules.utils.gemini_client import GeminiClient as GeminiInteraction
from modules.utils.json_analyzer import JsonAnalyzer


if TYPE_CHECKING:
    from dev_agent import DevAgent

logger = logging.getLogger(__name__)


class SelfImprover:
    """Модуль SelfImprover відповідає за ініціацію та управління процесом самовдосконалення агента.

    Він координує аналіз, планування, застосування виправлень та оцінку результатів.
    """

    def __init__(
        self,
        gemini_interaction: GeminiInteraction,
        json_analyzer: JsonAnalyzer,
        output_dir: str,
        task_queue: TaskQueue,
        test_integration_module,
        agent_config: Dict,
        pull_request_monitor: Optional[PullRequestMonitor] = None,
    ) -> None:
        self.gemini_interaction = gemini_interaction
        self.json_analyzer = json_analyzer
        self.output_dir = output_dir
        self.task_queue = task_queue
        self.test_integration_module = test_integration_module
        self.agent_config = agent_config
        self.pull_request_monitor = pull_request_monitor
        logger.info("SelfImprover ініціалізовано")

    def improve_codebase(self, analysis_results: Dict[str, object], agent: "DevAgent") -> Dict[str, object]:
        """Запускає процес покращення кодової бази на основі результатів аналізу.

        Args:
            analysis_results (Dict[str, object]): Результати аналізу від SelfAnalyzer.
            agent (DevAgent): Екземпляр головного агента для доступу до інших модулів.

        Returns:
            Dict[str, object]: Результат виконання.
        """
        logger.info("Початок покращення кодової бази на основі результатів аналізу...")

        # Приклад логіки:
        # 1. Аналіз (використовуючи SelfAnalyzer)
        # 2. Планування (використовуючи PlanningModule)
        # 3. Застосування виправлень (використовуючи CodeFixer)
        # 4. Тестування (використовуючи TestIntegrationModule)
        # 5. Оцінка (використовуючи ScoringSystem)

        # Ця логіка буде деталізована в міру розвитку системи.
        # Наразі це заглушка.
        try:
            # Генеруємо реальні завдання на основі аналізу
            logger.info("Генерація завдань самовдосконалення на основі аналізу...")

            # Створюємо завдання для виправлення виявлених проблем
            improvement_tasks: List = []

            if "issues" in analysis_results:
                for issue in analysis_results["issues"]:
                    if issue.get("type") == "code_quality":
                        improvement_tasks.append(
                            {
                                "type": "refactoring",
                                "refactoring_type": "code_quality",
                                "target_files": [issue.get("file", "modules/self_improvement/code_fixer.py")],
                                "description": f"Виправити проблему якості коду: {issue.get('description', 'Покращення коду')}",
                            }
                        )
                    elif issue.get("type") == "documentation":
                        improvement_tasks.append(
                            {
                                "type": "documentation",
                                "doc_type": "improve_docstrings",
                                "description": f"Покращити документацію: {issue.get('description', 'Оновлення документації')}",
                            }
                        )

            # Додаємо базові завдання самовдосконалення
            improvement_tasks.extend(
                [
                    {
                        "type": "analysis",
                        "analysis_type": "performance_review",
                        "description": "Аналіз продуктивності агента та виявлення вузьких місць",
                    },
                    {
                        "type": "refactoring",
                        "refactoring_type": "optimize_imports",
                        "target_files": ["dev_agent.py", "modules/self_improvement/code_fixer.py"],
                        "description": "Оптимізація імпортів та структури коду",
                    },
                    {
                        "type": "test",
                        "test_type": "coverage_improvement",
                        "target_files": ["modules/utils/error_memory.py"],
                        "description": "Покращення покриття тестами критичних модулів",
                    },
                ]
            )

            # Додаємо завдання до черги
            if improvement_tasks:
                self.task_queue.add_tasks(improvement_tasks)
                logger.info(f"Додано {len(improvement_tasks)} завдань самовдосконалення до черги")

            return {
                "status": "success",
                "tasks_created": len(improvement_tasks),
                "message": f"Створено {len(improvement_tasks)} завдань для самовдосконалення",
            }
        except Exception as e:
            logger.error(f"Помилка під час покращення кодової бази: {e}", exc_info=True)
            return {"status": "error", "message": f"Помилка під час покращення кодової бази: {e}"}

    def _evaluate_improvement(
        self, changes: List[Dict[str, object]], test_results: Dict[str, object]
    ) -> Dict[str, object]:
        """Оцінює ефективність застосованих покращень."""
        logger.info("Оцінка ефективності покращень...")
        # Тут буде логіка взаємодії з ScoringSystem
        # Наразі це заглушка
        score = 0
        if test_results.get("tests_passed"):
            score += 50
        if changes:
            score += 30
        return {"score": score, "feedback": "Оцінка покращень завершена (симуляція)."}

    def run_full_cycle(self, options: Dict[str, object]) -> Dict[str, object]:
        """Запускає повний цикл самовдосконалення: аналіз, планування, виправлення, оновлення документації."""
        logger.info("Запуск повного циклу самовдосконалення...")

        # 1. Аналіз кодової бази
        # Припускаємо, що SelfAnalyzer вже ініціалізований і доступний через DevAgent
        # self_analyzer = self.registry.get_instance('self_analyzer') # Це буде зроблено в DevAgent
        # if self_analyzer:
        #     analysis_results = self_analyzer.analyze_codebase(self.output_dir)
        #     logger.info(f"Результати аналізу: {analysis_results}")
        # else:
        #     logger.warning("SelfAnalyzer не ініціалізовано. Пропускаємо аналіз.")
        #     analysis_results = {"status": "skipped", "message": "SelfAnalyzer not available."}

        # 2. Планування (генерація завдань на основі аналізу)
        # planning_module = self.registry.get_instance('planning')
        # if planning_module:
        #     planning_results = planning_module.generate_tasks_from_analysis(analysis_results)
        #     logger.info(f"Результати планування: {planning_results}")
        # else:
        #     logger.warning("PlanningModule не ініціалізовано. Пропускаємо планування.")
        #     planning_results = {"status": "skipped", "message": "PlanningModule not available."}

        # 3. Застосування виправлень (додавання завдань до черги)
        # if planning_results.get("status") == "success" and planning_results.get("tasks"):
        #     for task in planning_results["tasks"]:
        #         self.task_queue.add_task(task)
        #     logger.info(f"Додано {len(planning_results['tasks'])} завдань до черги.")
        # else:
        #     logger.info("Немає завдань для застосування виправлень.")

        # 4. Оновлення документації
        # documentation_updater = self.registry.get_instance('documentation_updater')
        # if documentation_updater:
        #     doc_update_results = documentation_updater.update_all_documentation(self.output_dir)
        #     logger.info(f"Результати оновлення документації: {doc_update_results}")
        # else:
        #     logger.warning("DocumentationUpdater не ініціалізовано. Пропускаємо оновлення документації.")
        #     doc_update_results = {"status": "skipped", "message": "DocumentationUpdater not available."}

        # 5. Запуск тестів (якщо потрібно)
        if options.get("run_tests", False) and self.test_integration_module:
            test_results = self.test_integration_module.run_all_tests()
            logger.info(f"Результати тестів: {test_results}")
        else:
            logger.info("Тести не запускалися.")
            test_results = {"status": "skipped", "message": "Тести не запускалися."}

        # 6. Оцінка (якщо потрібно)
        # scoring_system = self.registry.get_instance('scoring_system')
        # if scoring_system:
        #     evaluation_results = scoring_system.evaluate_changes(analysis_results, test_results)
        #     logger.info(f"Результати оцінки: {evaluation_results}")
        # else:
        #     logger.warning("ScoringSystem не ініціалізовано. Пропускаємо оцінку.")
        #     evaluation_results = {"status": "skipped", "message": "ScoringSystem not available."}

        # Генеруємо додаткові завдання для наступного циклу
        next_cycle_tasks = [
            {
                "type": "analysis",
                "analysis_type": "code_metrics",
                "description": "Збір метрик коду для оцінки покращень",
            },
            {
                "type": "self_improvement",
                "improvement_type": "error_analysis",
                "description": "Аналіз помилок та створення стратегій їх уникнення",
            },
        ]

        self.task_queue.add_tasks(next_cycle_tasks)
        logger.info(f"Додано {len(next_cycle_tasks)} завдань для наступного циклу")

        return {
            "status": "success",
            "message": "Повний цикл самовдосконалення завершено",
            "next_cycle_tasks": len(next_cycle_tasks),
        }
