# УВАГА: НЕ ВНОСИТИ ЗМІНИ В ПАПКУ backups !!! Це резервна копія.

"""Основний модуль DevAgent для crypto_bot_project."""

import json
import logging
import os  # Перенесено сюди для кращої організації
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional

from dotenv import load_dotenv

from modules.core.agent_core import AgentCore


# Додаємо поточну директорію до шляху пошуку модулів
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Імпорт компонентів системи управління завданнями
from modules.core.module_registry import ModuleRegistry
from modules.core.task_dispatcher import TaskDispatcher
from modules.core.task_queue import TaskQueue
from modules.self_improvement.pull_request_monitor import PullRequestMonitor  # New import

# Імпорт модулів агента
from modules.utils.gemini_client import GeminiClient as GeminiInteraction, GeminiClient as GeminiStatsCollector
from modules.utils.json_analyzer import JsonAnalyzer


# Отримуємо логер, налаштований у run.py  # type: ignore
logger = logging.getLogger(__name__)

_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))


class DevAgent(AgentCore):
    """Основний клас DevAgent для управління завданнями."""

    def __init__(self, config_manager, output_dir, tasks_file, queue_file) -> None:
        """Метод __init__."""
        # Встановлюємо вихідну директорію якомога раніше
        self.output_dir = output_dir
        self.tasks_file = tasks_file
        self.queue_file = queue_file
        self.config_manager = config_manager

        self._setup_core_services()
        self._setup_task_management()
        self._requeue_stuck_tasks()  # Повертаємо "завислі" завдання в чергу
        self._setup_module_registry()

        # Завантаження та застосування конфігурації
        self.config = self.config_manager.config  # type: ignore
        self._apply_config()

        self.improvement_scheduler = None  # Ініціалізуємо за замовчуванням
        self.pull_request_monitor: Optional[PullRequestMonitor] = None  # Initialize here

        # Ініціалізуємо аналізатор логів
        try:
            from modules.utils.log_analyzer import LogAnalyzer

            self.log_analyzer = LogAnalyzer(self.output_dir)
        except Exception as e:
            logger.warning(f"Не вдалося ініціалізувати аналізатор логів: {e}")
            self.log_analyzer = None
        self._initialize_agent_modules()  # Реєструємо та ініціалізуємо всі модулі
        self._init_scheduler()  # Ініціалізуємо планувальник самовдосконалення після модулів
        logger.info("DevAgent ініціалізовано")

    def _requeue_stuck_tasks(self) -> None:
        """Знаходить завдання, що 'зависли' в статусі 'processing', і повертає їх у чергу."""
        requeued_count = self.task_queue.requeue_processing_tasks()
        if requeued_count > 0:
            logger.info(f"Повернуто {requeued_count} 'processing' завдань до статусу 'pending'.")

    def _setup_core_services(self) -> None:
        """Ініціалізує базові сервіси, такі як JsonAnalyzer та GeminiInteraction."""
        logger.debug("Ініціалізація базових сервісів...")

        # Спочатку ініціалізуємо колектор статистики
        self.gemini_stats_collector = GeminiStatsCollector()
        # Потім ініціалізуємо GeminiInteraction, передаючи колектор
        self.json_analyzer = JsonAnalyzer()
        self.gemini_interaction = GeminiInteraction()

        # Патчимо GeminiInteraction для кешування
        try:
            from modules.utils.gemini_cache import patch_gemini_interaction

            patch_gemini_interaction(self.gemini_interaction)
            logger.info("GeminiInteraction успішно патчено для кешування")
        except ImportError:  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa  # noqa
            logger.warning("Модуль gemini_cache не знайдено")

        super().__init__(self.gemini_interaction, self.json_analyzer)

    def _setup_task_management(self) -> None:
        """Ініціалізує систему управління завданнями (TaskQueue та TaskDispatcher)."""
        logger.debug("Ініціалізація системи управління завданнями...")
        # Ініціалізація системи управління завданнями
        self.task_queue = TaskQueue(self.queue_file)
        # Розгляньте можливість передавати лише необхідні залежності замість усього екземпляра DevAgent
        self.task_dispatcher = TaskDispatcher(self.task_queue, agent_instance=self)

    def _setup_module_registry(self) -> None:
        """Ініціалізує реєстр модулів та реєструє базові/основні модулі."""
        logger.debug("Ініціалізація реєстру модулів...")
        # Ініціалізація реєстру модулів
        self.registry = ModuleRegistry()

        # Реєструємо базові модулі (тільки якщо вони ще не зареєстровані)
        if "json_analyzer" not in self.registry.modules:
            self.registry.register("json_analyzer", JsonAnalyzer)
        if "gemini_interaction" not in self.registry.modules:
            self.registry.register("gemini_interaction", GeminiInteraction)

        # Завантажуємо основні модулі
        self.registry.load_core_modules()

        # Реєструємо екземпляри
        self.registry.instances["json_analyzer"] = self.json_analyzer  # type: ignore
        self.registry.instances["gemini_interaction"] = self.gemini_interaction  # type: ignore
        self.registry.instances["task_queue"] = self.task_queue  # type: ignore
        self.registry.instances["task_dispatcher"] = self.task_dispatcher  # type: ignore

    def _create_and_assign_module(
        self, name: str, attribute_name: str, extra_deps: Optional[Dict[str, object]] = None
    ) -> None:
        """Створює екземпляр модуля через реєстр та призначає його атрибуту агента."""
        deps = {
            "gemini_interaction": self.gemini_interaction,
            "output_dir": self.output_dir,
            "json_analyzer": self.json_analyzer,
        }
        if extra_deps:
            deps.update(extra_deps)

        instance = self.registry.create(name, **deps)
        setattr(self, attribute_name, instance)

        if instance is None:
            logger.error(f"ПОМИЛКА: Модуль '{name}' не було створено! self.registry.create(...) повернув None.")

    def _initialize_agent_modules(self) -> None:
        """Реєструє та ініціалізує всі функціональні модулі та модулі самовдосконалення."""
        logger.debug("Реєстрація та ініціалізація модулів агента...")

        # --- Реєстрація класів модулів самовдосконалення ---
        try:
            from modules.self_improvement.code_fixer import CodeFixer
            from modules.self_improvement.documentation_updater import DocumentationUpdater
            from modules.self_improvement.self_analyzer import SelfAnalyzer
            from modules.self_improvement.self_improver import SelfImprover

            modules_to_register = [
                ("self_analyzer", SelfAnalyzer),
                ("self_improver", SelfImprover),
                ("documentation_updater", DocumentationUpdater),
                ("code_fixer", CodeFixer),
            ]

            for name, cls in modules_to_register:
                if name not in self.registry.modules:
                    self.registry.register(name, cls)
        except ImportError as e:
            logger.warning(f"Не вдалося зареєструвати модулі самовдосконалення: {e}")

        # --- Створення екземплярів модулів ---
        # Спочатку створюємо модулі, які можуть бути залежностями для інших
        self._create_and_assign_module("test_integration", "test_integration_module")

        # Отримуємо облікові дані GitHub з середовища для передачі в CodeFixer
        github_token = os.getenv("GITHUB_TOKEN")
        github_repo_owner = os.getenv("GITHUB_REPO_OWNER")
        github_repo_name = os.getenv("GITHUB_REPO_NAME")

        # Create CodeFixer first to get its git_module for PullRequestMonitor
        self._create_and_assign_module(
            "code_fixer",
            "code_fixer",
            extra_deps={
                "task_queue": self.task_queue,
                "agent_config": self.config,  # Pass agent_config here
                "test_integration_module": self.test_integration_module,  # Pass test_integration_module
                # Передаємо облікові дані GitHub до CodeFixer
                "github_token": github_token,
                "repo_owner": github_repo_owner,
                "repo_name": github_repo_name,
            },
        )

        self._create_and_assign_module(
            "code_generation", "code_generation_module"
        )  # This name is correct for module_registry

        # Initialize PullRequestMonitor using the git_module from code_fixer
        if self.code_fixer and hasattr(self.code_fixer, "git_module"):
            self.pull_request_monitor = PullRequestMonitor(
                git_module=self.code_fixer.git_module,
                task_queue=self.task_queue,
                output_dir=self.output_dir,  # type: ignore
            )
            logger.info("PullRequestMonitor успішно ініціалізовано.")
        else:
            logger.warning("GitModule або CodeFixer не ініціалізовано, PullRequestMonitor не буде доступний.")

        self._create_and_assign_module("refactoring_executor", "refactoring_executor_module")  # Changed name here

        # Initialize DependencyAnalyzer first, as ProjectAnalyzer depends on it
        self._create_and_assign_module("dependency_analyzer", "dependency_analyzer")

        # Initialize ProjectAnalyzer, passing DependencyAnalyzer as a dependency
        self._create_and_assign_module(
            "project_analyzer", "project_analyzer", extra_deps={"dependency_analyzer": self.dependency_analyzer}
        )
        self._create_and_assign_module(
            "planning", "planning_module", extra_deps={"project_analyzer": self.project_analyzer}
        )
        self._create_and_assign_module("self_analyzer", "self_analyzer")
        self._create_and_assign_module("documentation_updater", "documentation_updater")

        # Створюємо SelfImprover, який залежить від test_integration_module
        self._create_and_assign_module(
            "self_improver",
            "self_improver",
            extra_deps={
                "task_queue": self.task_queue,
                "test_integration_module": self.test_integration_module,
                "agent_config": self.config,  # Pass agent_config
                "pull_request_monitor": self.pull_request_monitor,  # Pass the monitor
            },
        )
        self._create_and_assign_module("code_reviewer", "code_reviewer_module")  # Add this line
        logger.info("Функціональні модулі та модулі самовдосконалення ініціалізовано.")

    def _init_scheduler(self) -> None:
        """Ініціалізує планувальник самовдосконалення."""
        logger.debug("Ініціалізація планувальника самовдосконалення...")
        try:  # Імпортуємо ImprovementScheduler тут, щоб уникнути циклічних залежностей на рівні модуля
            from modules.self_improvement.improvement_scheduler import ImprovementScheduler

            if "improvement_scheduler" not in self.registry.modules:
                logger.debug("Реєстрація ImprovementScheduler в ModuleRegistry.")
                self.registry.register("improvement_scheduler", ImprovementScheduler)
            else:
                logger.debug("ImprovementScheduler вже зареєстровано в ModuleRegistry.")

            logger.debug(f"Спроба створити екземпляр ImprovementScheduler з output_dir='{self.output_dir}'")
            instance = self.registry.create(
                "improvement_scheduler",
                output_dir=self.output_dir,  # Передаємо self.output_dir, який вже є абсолютним шляхом
            )

            if instance is not None:
                self.improvement_scheduler = instance
                self.registry.instances["improvement_scheduler"] = self.improvement_scheduler  # type: ignore
                logger.info("Планувальник самовдосконалення успішно ініціалізовано.")
            else:
                logger.error(
                    "self.registry.create('improvement_scheduler', ...) повернуло None. Планувальник не ініціалізовано."
                )
                self.improvement_scheduler = None
        except ImportError as e:  # Більш конкретний виняток для проблем з імпортом
            logger.error(f"Помилка імпорту ImprovementScheduler: {e}", exc_info=True)
            self.improvement_scheduler = None
        except Exception as e:
            logger.error(f"Виняток під час ініціалізації планувальника самовдосконалення: {e}", exc_info=True)
            self.improvement_scheduler = None

    def _apply_config(self) -> None:
        """Застосовує параметри з конфігурації."""
        logger.debug("Застосування параметрів конфігурації...")

        # --- Параметри для GeminiInteraction ---
        # Параметри, що стосуються логіки самого класу (ретираї, затримки)
        self.gemini_interaction.max_retries = self.config.get("max_retries", self.gemini_interaction.max_retries)
        self.gemini_interaction.initial_delay = self.config.get("initial_delay", self.gemini_interaction.initial_delay)
        # Примітка: max_delay та post_call_delay не використовуються в поточній реалізації GeminiInteraction.

        # Параметри, що стосуються генерації контенту моделлю (температура, токени)
        model_params = self.config.get("model_parameters", {})
        generation_params_to_update = {
            "temperature": model_params.get("temperature"),
            "max_output_tokens": model_params.get("max_output_tokens"),
        }
        # Фільтруємо None значення, щоб не передавати їх, і викликаємо метод оновлення
        filtered_params = {k: v for k, v in generation_params_to_update.items() if v is not None}
        if filtered_params:
            # Skip update_generation_params as it's not available in GeminiClient
            pass

        # --- Параметри для JsonAnalyzer ---
        self.json_analyzer.max_repair_attempts = self.config.get("max_repair_attempts", 3)

        logger.info("Параметри з конфігурації застосовано")

    def register_handlers(self) -> None:
        """Реєструє обробники завдань у диспетчері."""
        # Реєструємо обробники для виправлення помилок
        self.task_dispatcher.register_handler("code_fix", "modules.core.task_handlers", "handle_code_fix_task")
        self.task_dispatcher.register_handler(
            "dependency_fix", "modules.core.task_handlers", "handle_dependency_fix_task"
        )

        # Існуючі обробники
        self.task_dispatcher.register_handler(
            "code_generation", "modules.core.task_handlers", "handle_code_generation_task"
        )
        self.task_dispatcher.register_handler("refactoring", "modules.core.task_handlers", "handle_refactoring_task")
        self.task_dispatcher.register_handler("query", "modules.core.task_handlers", "handle_query_task")
        self.task_dispatcher.register_handler("test", "modules.core.task_handlers", "handle_test_task")
        self.task_dispatcher.register_handler(
            "self_improvement", "modules.core.task_handlers", "handle_self_improvement_task"
        )
        self.task_dispatcher.register_handler("analysis", "modules.core.task_handlers", "handle_analysis_task")
        self.task_dispatcher.register_handler("planning", "modules.core.task_handlers", "handle_planning_task")
        self.task_dispatcher.register_handler(
            "documentation", "modules.core.task_handlers", "handle_documentation_task"
        )
        self.task_dispatcher.register_handler(
            "code_review", "modules.core.task_handlers", "handle_code_review_task"
        )  # Реєструємо новий обробник
        logger.info("Обробники завдань зареєстровано")

    def load_tasks(self) -> None:
        """Завантажує завдання з файлу та пендинг завдань."""
        # Завантажуємо основні завдання
        tasks = self.task_queue.load_tasks_from_file(self.tasks_file)

        # Завантажуємо завдання для виправлення помилок
        pending_tasks_file = os.path.join(self.output_dir, "pending_error_fixes.json")
        if os.path.exists(pending_tasks_file):
            try:
                with open(pending_tasks_file, "r", encoding="utf-8") as f:
                    error_tasks = json.load(f)
                if error_tasks:
                    tasks.extend(error_tasks)
                    logger.info(f"Додано {len(error_tasks)} завдань для виправлення помилок")
                    # Очищаємо файл після завантаження
                    os.remove(pending_tasks_file)
            except Exception as e:
                logger.error(f"Помилка завантаження завдань для виправлення помилок: {e}")

        if tasks:
            self.task_queue.add_tasks(tasks)
            logger.info(f"Додано {len(tasks)} завдань у чергу")
        else:
            logger.warning("Немає завдань для виконання")

    def self_improve(self, direct: bool = False) -> Dict[str, object]:
        """Запускає процес самовдосконалення."""
        logger.info("Запуск процесу самовдосконалення...")

        if not self.code_fixer or not hasattr(self.code_fixer, "git_module"):
            logger.error("GitModule не ініціалізовано. Процес самовдосконалення неможливий.")
            return {"status": "error", "message": "GitModule not initialized."}

        git = self.code_fixer.git_module  # type: ignore
        original_branch = git.get_current_branch()
        if not git.is_working_directory_clean():
            logger.info("Робоча директорія не чиста. Автоматичний коміт змін...")
            git.add_all()
            auto_commit_msg = (
                f"auto: Автоматичний коміт перед самовдосконаленням {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            if not git.commit(auto_commit_msg):
                logger.warning("Не вдалося створити автоматичний коміт, продовжуємо...")
            else:
                logger.info("Автоматичний коміт створено успішно.")

        improvement_branch = f"self-improvement-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        if not direct:
            if not git.create_and_checkout_branch(improvement_branch):
                return {"status": "error", "message": f"Не вдалося створити гілку '{improvement_branch}'."}

        try:
            if not direct:
                logger.info(f"Створено та переключено на гілку '{improvement_branch}' для самовдосконалення.")
            self._create_documentation_dirs()

            self.task_queue.add_task(
                {
                    "type": "self_improvement",
                    "improvement_type": "full_cycle",
                    "options": {
                        "analyze_architecture": True,
                        "improve_code_quality": True,
                        "update_documentation": True,
                        "run_tests": True,
                        "auto_fix": self.config.get("auto_fix", True),
                    },
                }
            )

            self.task_dispatcher.process_all_tasks()

            if not git.is_working_directory_clean():
                logger.info("Зміни виявлено. Створення коміту...")
                git.add_all()
                commit_message = (
                    f"feat(self-improve): Автоматичні покращення {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
                if not git.commit(commit_message):
                    raise RuntimeError("Не вдалося створити коміт зі змінами.")

                if not direct:
                    # Push опціонально (для локального режиму)
                    push_enabled = self.config.get("git", {}).get("auto_push", False)
                    if push_enabled:
                        logger.info(f"Pushing branch '{improvement_branch}' to remote...")
                        if not git.push(improvement_branch):
                            logger.warning(
                                f"Не вдалося виконати push гілки '{improvement_branch}', продовжуємо локально."
                            )
                    else:
                        logger.info("Auto-push відключено, зміни збережено локально.")

                    # Створюємо PR тільки якщо push увімкнено та GitHub API доступний
                    if push_enabled and hasattr(self.code_fixer, 'git_module') and self.code_fixer.git_module.repo:
                        pr_title = f"Автоматичне самовдосконалення {datetime.now().strftime('%Y-%m-%d')}"
                        pr_body = "Цей Pull Request містить автоматичні покращення, згенеровані DevAgent."
                        pr_info = git.create_pull_request(pr_title, pr_body, improvement_branch, "master")
                        if pr_info and self.pull_request_monitor:
                            self.pull_request_monitor.add_pr_to_monitor(pr_info["number"], improvement_branch, pr_title)
                    elif push_enabled:
                        logger.info("GitHub API недоступний, PR не створено. Зміни збережено локально.")
            else:
                logger.info("Немає змін для коміту після циклу самовдосконалення.")

            if not direct:
                git.checkout_branch(original_branch)
            return {
                "status": "success",
                "message": f"Процес самовдосконалення завершено. Зміни у гілці '{improvement_branch}' (локально).",
            }

        except Exception as e:
            logger.error(f"Критична помилка під час самовдосконалення: {e}", exc_info=True)
            if not direct:
                logger.info("Відкат змін...")
                git.checkout_branch(original_branch)
                git.delete_branch(improvement_branch)
                logger.info(f"Гілку '{improvement_branch}' видалено. Повернено до '{original_branch}'.")
            return {"status": "error", "message": f"Self-improvement failed and was rolled back: {e}"}

    def _create_documentation_dirs(self) -> None:
        """Створює директорії для документації та необхідні файли."""
        # Створюємо директорії
        os.makedirs(os.path.join(self.output_dir, "info"), exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "docs"), exist_ok=True)

        # Створюємо базові файли документації, якщо вони не існують
        docs_files = {
            os.path.join(
                self.output_dir, "info", "architecture_vision.md"
            ): "# Архітектурне бачення\n\nЦей файл містить опис архітектурного бачення проєкту.\n",
            os.path.join(
                self.output_dir, "info", "self_improvement_strategy.md"
            ): "# Стратегія самовдосконалення\n\nЦей файл містить опис стратегії самовдосконалення системи.\n",
            os.path.join(
                self.output_dir, "info", "refactoring_capabilities.md"
            ): "# Можливості рефакторингу\n\nЦей файл містить опис можливостей рефакторингу системи.\n",
            os.path.join(
                self.output_dir, "info", "analysis_capabilities.md"
            ): "# Можливості аналізу\n\nЦей файл містить опис можливостей аналізу системи.\n",
            os.path.join(
                self.output_dir, "info", "master_development_plan.md"
            ): "# Головний план розвитку\n\nЦей файл містить високорівневий план розвитку проєкту.\n\n## 1. Початкова ініціалізація\n\nОпис: Налаштування базової структури проєкту та залежностей.\n\n## 2. Розробка модуля торгівлі\n\nОпис: Реалізація основної логіки для виконання торгових операцій.\n\n## 3. Інтеграція з Binance API\n\nОпис: Підключення до Binance API для отримання даних та виконання угод.\n\n## 4. Модуль аналізу ринку\n\nОпис: Розробка функціоналу для аналізу ринкових даних та виявлення торгових можливостей.\n\n## 5. Модуль управління ризиками\n\nОпис: Впровадження стратегій управління ризиками для захисту капіталу.\n\n## 6. Тестування та оптимізація\n\nОпис: Проведення комплексного тестування та оптимізація продуктивності бота.\n",
        }

        for file_path, content in docs_files.items():
            if not os.path.exists(file_path):
                try:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    logger.info(f"Створено файл {file_path}")
                except Exception as e:
                    logger.error(f"Помилка при створенні файлу {file_path}: {e}")

        for file_path, content in docs_files.items():
            if not os.path.exists(file_path):
                try:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    logger.info(f"Створено файл {file_path}")
                except Exception as e:
                    logger.error(f"Помилка при створенні файлу {file_path}: {e}")

    def check_scheduled_tasks(self) -> Optional[Dict[str, object]]:
        """Перевіряє наявність запланованих завдань.

        Returns:
            Результат виконання завдання або None, якщо немає завдань
        """
        if not self.improvement_scheduler:
            logger.warning("Планувальник самовдосконалення не ініціалізовано")
            return None

        # Отримуємо наступне завдання
        task = self.improvement_scheduler.get_next_task()
        if not task:
            # logger.info("Немає запланованих завдань для виконання") # Занадто часто логується
            return None

        # Додаємо опцію auto_fix з конфігурації
        if "options" in task:
            task["options"]["auto_fix"] = self.config.get("auto_fix", True)

        # Додаємо завдання в чергу
        self.task_queue.add_task(task)

        # Обробляємо завдання
        self.task_dispatcher.process_next_task()

        # Отримуємо результат
        task_id = task.get("id")  # Припускаємо, що завдання має 'id'
        for t in self.task_queue.tasks:  # Перебираємо актуальний список завдань
            if t.get("id") == task_id and t.get("status") in ["completed", "failed"]:
                return {
                    "status": t.get("status"),
                    "result": t.get("result") if t.get("status") == "completed" else t.get("error"),
                }

        return None  # Якщо завдання ще не завершилося або не знайдено

    def run_daemon(self, check_interval: int = 10) -> None:
        """Запускає агента в режимі демона для безперервної обробки завдань.

        В цьому режимі агент:
        1. Періодично перевіряє та виконує заплановані завдання самовдосконалення.
        2. Обробляє всі завдання, що знаходяться в основній черзі.

        Args:
            check_interval (int): Інтервал перевірки нових завдань (в секундах).
        """
        logger.info(f"Запуск DevAgent в режимі демона з інтервалом перевірки {check_interval} секунд")

        self._create_documentation_dirs()
        self.register_handlers()

        try:
            while True:
                logger.debug("Початок циклу демона...")

                # 1. Перевіряємо та виконуємо заплановані завдання самовдосконалення
                scheduled_result = self.check_scheduled_tasks()
                if scheduled_result:
                    logger.info(
                        f"Виконано заплановане завдання самовдосконалення: {scheduled_result.get('status', 'unknown')}"
                    )

                # 1.5. Перевіряємо та закриваємо злиті Pull Request-и
                if self.pull_request_monitor:
                    pr_monitor_result = self.pull_request_monitor.check_and_close_merged_prs()
                    if pr_monitor_result.get("closed_prs_count", 0) > 0:
                        logger.info(f"Закрито {pr_monitor_result['closed_prs_count']} злитих Pull Request-ів.")

                # 2. Обробляємо всі завдання з основної черги
                processed_count = self.task_dispatcher.process_all_tasks()
                if processed_count > 0:
                    logger.info(f"Оброблено {processed_count} завдань з основної черги.")

                if not scheduled_result and processed_count == 0:
                    logger.debug(f"Немає активних завдань. Очікування {check_interval} секунд.")

                time.sleep(check_interval)
        except KeyboardInterrupt:  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa  # noqa
            logger.info("Отримано сигнал переривання. Завершення роботи демона...")
        except Exception as e:
            logger.error(f"Критична помилка в режимі демона: {e}", exc_info=True)

    def run(self) -> None:
        """Запускає процес виконання завдань, доки черга не стане порожньою.

        Цей режим призначений для обробки всіх наявних та новостворених завдань до повного їх завершення.
        """
        logger.info("Запуск DevAgent...")
        self._create_documentation_dirs()
        self.register_handlers()

        stats = self.task_queue.get_stats()
        if stats["pending"] == 0 and stats["processing"] == 0:
            logger.info("Немає завдань у черзі. Завантажуємо з файлу.")
            self.load_tasks()

        # Головний цикл виконання, який працює, доки є завдання для обробки
        while True:
            processed_count = self.task_dispatcher.process_all_tasks()
            if processed_count == 0:
                logger.info("Черга завдань порожня. Завершення роботи.")
                break
            logger.info(f"Оброблено {processed_count} завдань у поточному циклі. Перевірка наявності нових завдань...")

        stats = self.task_queue.get_stats()
        logger.info(f"Загалом оброблено завдань: {stats['completed'] + stats['failed']}")
        logger.info(f"Успішно виконано: {stats['completed']}")
        logger.info(f"Завершено з помилками: {stats['failed']}")


# Глобальний екземпляр агента для доступу з обробників завдань
agent_instance: Optional[DevAgent] = None  # Додано анотацію типу


def get_agent_instance() -> DevAgent:
    """Повертає глобальний екземпляр DevAgent."""
    global agent_instance
    if agent_instance is None:
        raise RuntimeError("DevAgent не було ініціалізовано. Будь ласка, запустіть програму через run.py")
    return agent_instance


if __name__ == "__main__":
    # Завантажуємо змінні середовища
    load_dotenv()

    # Отримуємо API ключі
    api_keys_str = os.getenv("GOOGLE_API_KEY")
    api_keys: List = []

    if api_keys_str:
        api_keys = [key.strip() for key in api_keys_str.split(",") if key.strip()]

    if not api_keys:
        logger.error("Не знайдено API ключів Gemini. Встановіть змінну середовища GOOGLE_API_KEY.")
        sys.exit(1)

    logger.info(f"Знайдено {len(api_keys)} API ключ(ів) Gemini")

    # Створюємо та запускаємо агента
    from modules.utils.config_manager import ConfigManager

    config_manager = ConfigManager()
    agent = DevAgent(
        config_manager=config_manager, output_dir=".", tasks_file="tasks.json", queue_file="task_queue.json"
    )
    agent.run()
