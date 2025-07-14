import logging
import os
import subprocess
import sys
from typing import TYPE_CHECKING, Dict, List, Optional

from modules.core.agent_core import AgentCore, TaskHandler


if TYPE_CHECKING:
    from dev_agent import DevAgent

"""
Модуль інтеграції тестів для Meta-Agent.
"""
# Імпортуємо базові класи
# Налаштування логування
# logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - [TestIntegration] - %(message)s") # Використовуємо глобальну конфігурацію
logger = logging.getLogger(__name__)


class TestIntegrationModule(AgentCore, TaskHandler):
    """Модуль інтеграції тестів для Meta-Agent."""

    def __init__(self, gemini_interaction, json_analyzer, output_dir) -> None:
        """Ініціалізує TestIntegrationModule.

        Args:
            gemini_interaction: Екземпляр GeminiInteraction для взаємодії з Gemini API.
            json_analyzer: Екземпляр JsonAnalyzer для обробки JSON.
            output_dir (str): Коренева директорія проекту для пошуку файлів.
        """
        super().__init__(gemini_interaction, json_analyzer)
        self.output_dir = output_dir
        logger.info("TestIntegrationModule ініціалізовано")

    def handle_task(self, task: Dict[str, object], agent: Optional["DevAgent"] = None) -> Dict[str, object]:
        """Обробляє завдання тестування.

        Диспетчеризує завдання до відповідних методів тестування
        на основі `test_type`.

        Args:
            task (Dict[str, object]): Словник, що містить деталі завдання тестування.
            agent (Optional["DevAgent"]): Екземпляр агента. Defaults to None.

        Returns:
            Dict[str, object]: Результат виконання тестування.
        """
        test_type = task.get("test_type")
        target_files = task.get("target_files", [])
        options = task.get("options", {})

        logger.info(f"Виконання тестування типу '{test_type}' для {len(target_files)} файлів")

        if test_type == "run_unit_tests":
            result = self.run_unit_tests(target_files, options)
            return result
        elif test_type == "run_integration_tests":
            result = self.run_integration_tests(target_files, options)
            return result
        elif test_type == "generate_tests":
            result = self.generate_tests(target_files, options)
            return result
        elif test_type == "coverage_analysis":
            # Додаємо обробник-заглушку для аналізу покриття
            return self.run_coverage_analysis(target_files, options)
        elif test_type == "code_coverage_analysis":
            # Додаємо синонім для аналізу покриття
            return self.run_coverage_analysis(target_files, options)
        elif test_type == "regression_testing":
            # Додаємо обробник-заглушку для регресійного тестування
            return self.run_regression_testing(target_files, options)
        elif test_type == "unification":
            # Додаємо обробник-заглушку для уніфікації
            return self.handle_unification(target_files, options)
        else:
            return {"status": "error", "message": f"Тип тестування '{test_type}' не підтримується"}

    def run_unit_tests(self, target_files: List[str], options: Dict[str, object]) -> Dict[str, object]:
        """Запускає модульні тести для вказаних файлів за допомогою `unittest`.

        Args:
            target_files (List[str]): Список відносних шляхів до тестових файлів.
            options (Dict[str, object]): Додаткові опції, такі як 'verbose' та 'coverage'.

        Returns:
            Dict[str, object]: Словник з результатами виконання тестів.
        """
        logger.info(f"Запуск модульних тестів для {len(target_files)} файлів")

        verbose = options.get("verbose", False)
        coverage = options.get("coverage", False)

        results: Dict = {}
        success = True

        for file_path in target_files:
            full_path = os.path.join(self.output_dir, file_path)
            if not os.path.exists(full_path):
                logger.warning(f"Файл '{full_path}' не існує")
                results[file_path] = {"status": "error", "message": "Файл не існує"}
                success = False
                continue

            # Формуємо команду для запуску тестів
            test_dir = os.path.join(self.output_dir, "tests")  # Припускаємо, що тести в директорії tests
            test_file_name = "test_" + os.path.basename(file_path)  # Шаблон імені тестового файлу

            if not os.path.exists(os.path.join(test_dir, test_file_name)):
                results[file_path] = {"status": "skipped", "message": f"Тести для '{file_path}' не знайдені."}
                continue

            # Base pytest command
            cmd = [sys.executable, "-m", "pytest", os.path.join(test_dir, test_file_name)]

            # Додаємо coverage, якщо потрібно
            if coverage:
                # pytest-cov інтегрується безпосередньо з pytest.
                # Додаємо --cov для конкретного вихідного файлу та --cov-report.
                cmd.extend(["--cov", file_path, "--cov-report", "term-missing"])

            if verbose:
                cmd.append("-v")

            try:
                # Запускаємо тести
                process = subprocess.run(
                    cmd, cwd=self.output_dir, capture_output=True, text=True, check=False
                )  # cwd=self.output_dir для правильного пошуку модулів

                if process.returncode == 0:
                    results[file_path] = {"status": "success", "output": process.stdout, "tests_passed": True}
                else:
                    results[file_path] = {
                        "status": "error",
                        "output": process.stdout,
                        "error": process.stderr,
                        "tests_passed": False,
                    }
                    success = False
            except Exception as e:
                logger.error(f"Помилка при запуску тестів для '{file_path}': {e}", exc_info=True)
                results[file_path] = {"status": "error", "message": str(e)}
                success = False

        # Агрегуємо результати для загального повернення
        overall_status = "success" if success else "error"
        overall_tests_passed = all(r.get("tests_passed", False) for r in results.values())

        return {
            "status": overall_status,
            "results": results,
            "files_tested": len(target_files),
            "tests_passed": overall_tests_passed,  # Додаємо загальний статус проходження тестів
        }

    def run_integration_tests(self, target_files: List[str], options: Dict[str, object]) -> Dict[str, object]:
        """Запускає інтеграційні тести для вказаних файлів.

        (Наразі це заглушка, яка повертає успішний результат).

        Args:
            target_files (List[str]): Список відносних шляхів до файлів.
            options (Dict[str, object]): Додаткові опції.

        Returns:
            Dict[str, object]: Словник з результатом виконання інтеграційних тестів.
        """
        logger.info(f"Запуск інтеграційних тестів для {len(target_files)} файлів")

        # Логіка запуску інтеграційних тестів аналогічна до модульних тестів,
        # але з іншими параметрами та налаштуваннями

        return {
            "status": "success",
            "message": "Інтеграційні тести успішно виконано (заглушка)",
            "files_tested": len(target_files),
        }

    def generate_tests(self, target_files: List[str], options: Dict[str, object]) -> Dict[str, object]:
        """Генерує тести для вказаних файлів за допомогою Gemini.

        Надсилає вміст файлу Gemini та отримує згенерований код тестів,
        який потім зберігається у новому файлі.

        Args:
            target_files (List[str]): Список відносних шляхів до файлів.
            options (Dict[str, object]): Додаткові опції (наразі не використовуються).

        Returns:
            Dict[str, object]: Словник з результатами генерації тестів.
        """
        logger.info(f"Генерація тестів для {len(target_files)} файлів")

        results: Dict = {}
        success = True

        for file_path in target_files:
            full_path = os.path.join(self.output_dir, file_path)
            if not os.path.exists(full_path):
                logger.warning(f"Файл '{file_path}' не існує")
                results[file_path] = {"status": "error", "message": "Файл не існує"}
                success = False
                continue

            try:
                # Читаємо вміст файлу
                with open(full_path, encoding="utf-8") as f:
                    content = f.read()

                # Формуємо запит для Gemini
                prompt_parts = [
                    "Ти - AI-асистент для генерації тестів.",
                    f"Потрібно згенерувати тести для файлу {file_path}:",
                    f"```python\n{content}\n```",
                    "Згенеруй модульні тести для всіх функцій та класів у файлі.",
                    "Використовуй бібліотеку unittest.",
                    "Поверни лише код тестів без пояснень.",
                ]

                response = self.gemini_interaction.generate_content(
                    prompt_parts=prompt_parts, generation_config={"response_mime_type": "text/plain"}
                )

                if response:
                    test_code = response.strip()

                    # Формуємо шлях до файлу з тестами
                    test_file_name = f"test_{os.path.basename(file_path)}"
                    # Зберігаємо тести в директорії modules/tests
                    tests_dir = os.path.join(self.output_dir, "modules", "tests")
                    os.makedirs(tests_dir, exist_ok=True)
                    test_file_path = os.path.join(tests_dir, test_file_name)

                    # Зберігаємо тести у файл
                    with open(test_file_path, "w", encoding="utf-8") as f:
                        f.write(test_code)

                    results[file_path] = {
                        "status": "success",
                        "test_file": os.path.relpath(test_file_path, self.output_dir),
                    }
                else:
                    results[file_path] = {"status": "error", "message": "Не вдалося згенерувати тести"}
                    success = False
            except Exception as e:
                logger.error(f"Помилка при генерації тестів для '{file_path}': {e}", exc_info=True)
                results[file_path] = {"status": "error", "message": str(e)}
                success = False

        return {"status": "success" if success else "error", "results": results, "files_tested": len(target_files)}

    def run_coverage_analysis(self, target_files: List[str], options: Dict[str, object]) -> Dict[str, object]:
        """Виконує аналіз покриття коду тестами. (Заглушка)."""
        logger.info(f"Запуск аналізу покриття коду для {len(target_files)} файлів (заглушка).")
        return {
            "status": "success",
            "message": "Функціональність аналізу покриття коду ще не реалізована.",
            "files_analyzed": len(target_files),
        }

    def run_regression_testing(self, target_files: List[str], options: Dict[str, object]) -> Dict[str, object]:
        """Виконує регресійне тестування. (Заглушка)."""
        logger.info(f"Запуск регресійного тестування для {len(target_files)} файлів (заглушка).")
        return {
            "status": "success",
            "message": "Функціональність регресійного тестування ще не реалізована.",
            "files_tested": len(target_files),
        }

    def handle_unification(self, target_files: List[str], options: Dict[str, object]) -> Dict[str, object]:
        """Обробляє завдання з уніфікації тестових модулів. (Заглушка)."""
        logger.info("Обробка уніфікації тестових модулів (заглушка).")
        return {
            "status": "success",
            "message": "Функціональність уніфікації тестових модулів ще не реалізована.",
            "files_analyzed": len(target_files),
        }
