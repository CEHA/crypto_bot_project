import ast
import json  # Додано для json.dumps  # type: ignore
import logging
import os
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple


# Налаштування логування
logger = logging.getLogger(__name__)

# Додаємо імпорт GeminiStats
try:
    from modules.utils.gemini_stats import GeminiStatsCollector
except ImportError:  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa  # noqa
    GeminiStatsCollector = None
from modules.core.agent_core import AgentCore, TaskHandler


logger.warning("Не вдалося імпортувати GeminiStats. Аналіз продуктивності Gemini буде недоступний.")


if TYPE_CHECKING:
    from dev_agent import DevAgent
    from modules.analysis.dependency_analyzer import DependencyAnalyzer  # New import for type hinting


class ProjectAnalyzer(AgentCore, TaskHandler):
    """Модуль аналізу проекту для Meta-Agent."""

    def __init__(
        self, gemini_interaction, json_analyzer, output_dir, dependency_analyzer: Optional["DependencyAnalyzer"] = None
    ) -> None:  # Added dependency_analyzer
        """Ініціалізує ProjectAnalyzer.

        Args:
            gemini_interaction: Екземпляр GeminiInteraction для взаємодії з Gemini API.
            json_analyzer: Екземпляр JsonAnalyzer для обробки JSON.
            output_dir (str): Коренева диреторія проекту для аналізу.
            dependency_analyzer (Optional[DependencyAnalyzer]): Екземпляр DependencyAnalyzer для аналізу залежностей.
        """
        super().__init__(gemini_interaction, json_analyzer)
        self.output_dir = output_dir
        # Переконуємося, що output_dir є абсолютним шляхом
        if not os.path.isabs(self.output_dir):
            self.output_dir = os.path.abspath(self.output_dir)
        logger.info("ProjectAnalyzer ініціалізовано")
        self.dependency_analyzer = dependency_analyzer  # Store it

    def handle_task(self, task: Dict[str, object], agent: "DevAgent" = None) -> Dict[str, object]:
        """Обробляє завдання аналізу проекту.

        Диспетчеризує завдання до відповідних методів на основі `analysis_type`.

        Args:
            task (Dict[str, object]): Словник, що містить деталі завдання.
            agent (DevAgent, optional): Екземпляр агента. Defaults to None.

        Returns:
            Dict[str, object]: Результат аналізу.
        """
        analysis_type = task.get("analysis_type")
        target_files = task.get("target_files", [])  # Може бути порожнім для аналізу архітектури
        options = task.get("options", {})

        logger.info(
            f"Виконання аналізу типу '{analysis_type}' для {len(target_files) if target_files else 'всього проекту'} файлів/проекту"
        )

        if analysis_type == "code_quality_review":
            if not target_files:
                return {"status": "error", "message": "Для аналізу якості коду потрібен список файлів."}
            result = self.analyze_code_quality(target_files, options)
            return result
        elif analysis_type == "architecture_review":
            # Для аналізу архітектури target_files можуть бути необов'язковими,
            # оскільки аналізується вся структура проекту в output_dir
            result = self.analyze_architecture(
                target_files, options
            )  # target_files можуть використовуватися для фокусування
            return result
        elif analysis_type == "dependency_analysis":
            if not self.dependency_analyzer:
                return {"status": "error", "message": "DependencyAnalyzer не ініціалізовано в ProjectAnalyzer."}
            # За замовчуванням, для загального аналізу залежностей, шукаємо циклічні залежності
            logger.info("Запуск пошуку циклічних залежностей через DependencyAnalyzer.")
            result = self.dependency_analyzer.find_circular_dependencies(target_files, options)
            return result
        elif analysis_type == "identify_key_modules":
            result = self.identify_key_modules(options)
            return result
        elif analysis_type == "gemini_parameter_performance":
            return self._handle_gemini_parameter_performance(task)
        elif analysis_type == "gemini_impact_complexity_assessment":
            return self._handle_gemini_impact_complexity_assessment(task)
        else:
            if not hasattr(self, f"analyze_{analysis_type}"):
                return {"status": "error", "message": f"Тип аналізу '{analysis_type}' не підтримується ProjectAnalyzer"}
            analysis_method = getattr(self, f"analyze_{analysis_type}")
            return analysis_method(target_files, options)

    def analyze_dependency_graph(self, target_files: List[str], options: Dict[str, object]) -> Dict[str, object]:
        """Метод analyze_dependency_graph."""
        return {"status": "not_implemented", "message": "Побудова графа залежностей ще не реалізована."}

    def analyze_semantic_search(self, target_files: List[str], options: Dict[str, object]) -> Dict[str, object]:
        """Метод analyze_semantic_search."""
        return {"status": "not_implemented", "message": "Семантичний пошук ще не реалізований."}

    def analyze_code_complexity(self, target_files: List[str], options: Dict[str, object]) -> Dict[str, object]:
        """Метод analyze_code_complexity."""
        return {"status": "not_implemented", "message": "Аналіз складності коду ще не реалізований."}

    def analyze_pull_request_analysis(self, target_files: List[str], options: Dict[str, object]) -> Dict[str, object]:
        """Метод analyze_pull_request_analysis."""
        return {"status": "not_implemented", "message": "Аналіз pull request'ів ще не реалізований."}

    def analyze_code_complexity_analysis(
        self, target_files: List[str], options: Dict[str, object]
    ) -> Dict[str, object]:
        """Метод analyze_code_complexity_analysis."""
        return {"status": "not_implemented", "message": "Аналіз складності коду (детальний) ще не реалізований."}

    def _handle_gemini_impact_complexity_assessment(
        self, task: Dict[str, object]
    ) -> Dict[
        str, object
    ]:  # NOTE: Збережено, оскільки використовується. Можливо потрібно інтегрувати в загальну систему.
        """Handles Gemini impact/complexity assessment. (Placeholder)."""
        logger.info("Виконання оцінки впливу та складності за допомогою Gemini (placeholder).")
        return {"status": "success", "message": "Оцінка впливу та складності виконана (placeholder)."}

    def _handle_gemini_parameter_performance(self, task: Dict[str, object]) -> Dict[str, object]:
        """Аналізує статистику викликів Gemini API."""
        if not GeminiStatsCollector:
            return {"status": "error", "message": "Модуль GeminiStats не імпортовано або недоступний."}

        logger.info("Аналіз продуктивності параметрів Gemini...")
        try:
            stats_collector = GeminiStatsCollector(output_dir=self.output_dir)
            summary = stats_collector.get_stats_summary()

            return {
                "status": "success",
                "message": "Аналіз продуктивності Gemini завершено.",
                "summary": summary,
            }
        except Exception as e:
            logger.error(f"Помилка під час аналізу продуктивності Gemini: {e}", exc_info=True)
            return {"status": "error", "message": f"Помилка під час аналізу продуктивності Gemini: {str(e)}"}

    def analyze_code_quality(self, target_files: List[str], options: Dict[str, object]) -> Dict[str, object]:
        """Аналізує якість коду у вказаних файлах.

        Використовує Gemini для оцінки коду за різними критеріями.

        Args:
            target_files (List[str]): Список відносних шляхів до файлів для аналізу.
            options (Dict[str, object]): Додаткові опції (наразі не використовуються).

        Returns:
            Dict[str, object]: Словник з результатами аналізу якості коду.
        """
        logger.info(f"Аналіз якості коду для {len(target_files)} файлів")

        results: Dict = {}
        for file_path_rel in target_files:
            full_path = os.path.join(self.output_dir, file_path_rel)
            if not os.path.exists(full_path):
                results[file_path_rel] = {"status": "error", "message": f"Файл '{full_path}' не існує"}
                continue

            try:
                with open(full_path, encoding="utf-8") as f:
                    content = f.read()

                # Формуємо запит для Gemini
                prompt_parts = [
                    "Ти - AI-асистент для аналізу якості коду.",
                    f"Проаналізуй якість коду у файлі {file_path_rel}:",
                    f"```python\n{content}\n```",
                    "Оціни код за наступними критеріями:",
                    "1. Дотримання PEP 8 (стиль коду, іменування, відступи)",
                    "2. Читабельність та зрозумілість коду (логіка, коментарі, документація)",
                    "3. Ефективність та потенційні проблеми продуктивності",
                    "4. Обробка помилок та виняткових ситуацій",
                    "5. Можливі рефакторинги для покращення структури та дизайну",
                    "Поверни результат у форматі JSON з оцінками (наприклад, 'good', 'needs_improvement', 'poor') та конкретними рекомендаціями для кожного критерію.",
                ]

                response = self.gemini_interaction.generate_content(
                    prompt_parts=prompt_parts, generation_config={"response_mime_type": "application/json"}
                )

                if response and isinstance(response, dict):
                    results[file_path_rel] = {"status": "success", "analysis": response}
                else:
                    results[file_path_rel] = {"status": "error", "message": "Не вдалося проаналізувати код"}
            except Exception as e:
                logger.error(f"Помилка при аналізі файлу '{full_path}': {e}", exc_info=True)
                results[file_path_rel] = {"status": "error", "message": str(e)}

        return {"status": "success", "results": results, "files_analyzed": len(target_files)}

    def analyze_architecture(self, target_files: List[str], options: Dict[str, object]) -> Dict[str, object]:
        """Аналізує архітектуру проекту.

        Збирає структуру файлів та директорій, а потім використовує Gemini
        для генерації детального звіту про архітектуру.

        Args:
            target_files (List[str]): Список файлів для фокусування (наразі аналізується весь проект).
            options (Dict[str, object]): Додаткові опції.

        Returns:
            Dict[str, object]: Словник з результатами аналізу архітектури.
        """
        logger.info(f"Аналіз архітектури для {'всього проекту' if not target_files else f'{len(target_files)} файлів'}")

        # Збираємо інформацію про структуру проекту
        project_structure: Dict = {}
        # Аналізуємо всю директорію self.output_dir  # type: ignore
        # TODO: Додати можливість фокусуватися на target_files, якщо вони надані
        for root, dirs, files in os.walk(self.output_dir):
            # Ігноруємо директорію .git та backups
            if ".git" in dirs:
                dirs.remove(".git")
            if "backups" in dirs:
                dirs.remove("backups")
            if "__pycache__" in dirs:
                dirs.remove("__pycache__")

            rel_path = os.path.relpath(root, self.output_dir)
            if rel_path == ".":
                rel_path = ""  # Корінь проекту

            # Фільтруємо тільки Python файли для аналізу структури
            py_files = [f for f in files if f.endswith(".py")]

            project_structure[rel_path if rel_path else "/"] = {  # Використовуємо / для кореня
                "dirs": dirs,
                "files": py_files,  # Тільки .py файли
            }

        # Формуємо запит для Gemini
        prompt_parts = [
            "Ти - AI-асистент для аналізу архітектури програмного забезпечення.",
            ("Проаналізуй архітектуру проекту на основі його структури файлів тадиректорій (тільки Python файли):"),
            f"Структура проекту:\n```json\n{json.dumps(project_structure, indent=2)}\n```",
            "Надай детальний аналіз архітектури, включаючи:",
            "1. Основні компоненти/модулі та їх призначення.",
            "2. Взаємозв'язки між компонентами (якщо можливо визначити зі структури).",
            ("3. Можливі архітектурні патерни, що використовуються (наприклад, MVC,Layered, Microservices тощо)."),
            "4. Потенційні проблеми або слабкі місця в архітектурі (наприклад, висока зв'язаність, низька згуртованість, відсутність чітких меж відповідальності).",
            "5. Рекомендації щодо покращення архітектури.",
            "Поверни результат у форматі JSON.",
        ]

        response = self.gemini_interaction.generate_content(
            prompt_parts=prompt_parts, generation_config={"response_mime_type": "application/json"}
        )

        if response and isinstance(response, dict):
            return {
                "status": "success",
                "architecture_analysis": response,
                "project_structure_analyzed": project_structure,  # Додаємо структуру для довідки
            }

        return {"status": "error", "message": "Не вдалося проаналізувати архітектуру"}

    def identify_key_modules(self, options: Dict[str, object]) -> Dict[str, object]:
        """Автоматично визначає ключові модулі в проекті на основі заданих стратегій.

        Args:
            options (Dict[str, object]): Словник опцій.
                - "strategy" (str): Стратегія для використання. Наразі підтримується "complexity".
                - "top_n" (int): Кількість файлів для повернення.

        Returns:
            Dict[str, object]: Словник, що містить список визначених ключових файлів.
        """
        strategy = options.get("strategy", "complexity")
        top_n = options.get("top_n", 5)

        logger.info(f"Визначення {top_n} ключових модулів за стратегією '{strategy}'.")

        all_py_files = self._get_all_project_files()

        if not all_py_files:
            return {"status": "error", "message": "Не знайдено Python файлів у проекті."}

        scored_files: List = []
        if strategy == "complexity":
            scored_files = self._score_by_complexity(all_py_files)
        # TODO: Додати інші стратегії, наприклад, 'centrality' або 'recency'
        else:
            return {"status": "error", "message": f"Невідома стратегія: {strategy}"}

        if not scored_files:
            return {"status": "success", "key_modules": [], "message": "Не вдалося оцінити файли."}

        # Сортуємо файли за оцінкою у спадаючому порядку
        scored_files.sort(key=lambda x: x[1], reverse=True)

        # Отримуємо top N файлів
        key_modules = [file for file, score in scored_files[:top_n]]

        # Створюємо конкретні пропозиції завдань
        suggested_tasks: List = []
        for module_path in key_modules:
            suggested_tasks.append(
                {
                    "type": "analysis",
                    "analysis_type": "code_quality_review",
                    "target_files": [module_path],
                    "description": f"Виконати огляд якості коду для автоматично визначеного ключового модуля: {module_path}",
                }
            )
            suggested_tasks.append(
                {
                    "type": "test",
                    "test_type": "generate_tests",
                    "target_files": [module_path],
                    "description": f"Згенерувати модульні тести для автоматично визначеного ключового модуля: {module_path}",
                }
            )

        return {
            "status": "success",
            "strategy": strategy,
            "key_modules": key_modules,
            "details": scored_files[:top_n],
            "suggested_tasks": suggested_tasks,  # Повертаємо список завдань
        }

    def _get_all_project_files(self) -> List[str]:
        """Сканує вихідну директорію та повертає список всіх .py файлів."""
        py_files: List = []
        # Виключаємо директорії, пов'язані з тестами, на рівні обходу
        excluded_dirs = [".git", "__pycache__", "venv", "env", "backups", "tests", "test"]
        for root, dirs, files in os.walk(self.output_dir):
            # Модифікуємо dirs "на місці", щоб os.walk не заходив у виключені директорії
            dirs[:] = [d for d in dirs if d not in excluded_dirs]
            for file in files:
                # Додатково перевіряємо імена файлів, щоб виключити ті, що починаються з test_
                if file.endswith(".py") and not file.startswith("test_"):
                    py_files.append(os.path.join(root, file))
        return py_files

    def _score_by_complexity(self, file_paths: List[str]) -> List[Tuple[str, int]]:
        """Оцінює файли на основі цикломатичної складності та кількості рядків."""
        try:
            from radon.visitors import ComplexityVisitor
        except ImportError:  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa  # noqa
            logger.warning(
                "Бібліотеку 'radon' не знайдено. Використовується спрощений аналіз складності. Встановіть 'radon' для більш точних результатів."
            )
            return self._simple_score_by_complexity(file_paths)

        scored_files: List = []
        for file_path in file_paths:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                if not content.strip():  # Handle empty files
                    scored_files.append((os.path.relpath(file_path, self.output_dir), 0))
                    continue

                visitor = ComplexityVisitor.from_code(content)
                total_complexity = sum(f.complexity for f in visitor.functions)
                line_count = len(content.splitlines())
                # Комбінована оцінка
                score = total_complexity + (line_count // 50)  # Adjust weight if needed
                rel_path = os.path.relpath(file_path, self.output_dir)
                scored_files.append((rel_path, score))
            except SyntaxError as e:
                logger.warning(f"Не вдалося розрахувати складність для {file_path}: invalid syntax ({e})")
            except Exception as e:
                logger.warning(f"Не вдалося розрахувати складність для {file_path}: {e}")
        return scored_files

    def _simple_score_by_complexity(self, file_paths: List[str]) -> List[Tuple[str, int]]:
        """Резервний метод оцінки, якщо 'radon' не встановлено."""
        scored_files: List = []
        for file_path in file_paths:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                if not content.strip():
                    scored_files.append((os.path.relpath(file_path, self.output_dir), 0))
                    continue
                tree = ast.parse(content)
                complexity = sum(
                    1
                    for node in ast.walk(tree)
                    if isinstance(node, (ast.If, ast.For, ast.While, ast.Try, ast.With, ast.BoolOp, ast.ExceptHandler))
                )
                line_count = len(content.splitlines())
                score = complexity + (line_count // 25)
                rel_path = os.path.relpath(file_path, self.output_dir)
                scored_files.append((rel_path, score))
            except SyntaxError as e:
                logger.warning(
                    f"Не вдалося розрахувати складність (спрощений метод) для {file_path}: invalid syntax ({e})"
                )
            except Exception as e:
                logger.warning(f"Не вдалося розрахувати складність (спрощений метод) для {file_path}: {e}")
        return scored_files
