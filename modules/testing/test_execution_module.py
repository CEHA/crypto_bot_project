import ast
import logging
import os
import subprocess
import sys
from typing import Dict, List, Optional


# Налаштування логування
logger = logging.getLogger(__name__)


class TestExecutionModule:
    """Клас для виконання та генерації тестів."""

    def __init__(self, output_dir: str = "crypto_bot_project") -> None:
        """Ініціалізує TestExecutionModule.

        Args:
            output_dir (str): Коренева директорія проекту, де знаходяться файли для тестування.
        """
        self.output_dir = output_dir
        logger.info("TestExecutionModule ініціалізовано")

    def run_tests(self, test_files: List[str], options: Optional[Dict[str, object]] = None) -> Dict[str, object]:
        """Запускає тести для вказаних файлів.

        Args:
            test_files (List[str]): Список відносних шляхів до тестових файлів.
            options (Optional[Dict[str, object]]): Додаткові опції, такі як 'verbose' та 'coverage'.

        Returns:
            Dict[str, object]: Словник з результатами виконання тестів.
        """
        options = options or {}
        verbose = options.get("verbose", False)
        coverage = options.get("coverage", False)

        results: Dict = {}
        success = True

        for file_path in test_files:
            full_path = os.path.join(self.output_dir, file_path)
            if not os.path.exists(full_path):
                logger.warning(f"Файл '{full_path}' не існує")
                results[file_path] = {"status": "error", "message": "Файл не існує"}
                success = False
                continue

            # Формуємо команду для запуску тестів
            test_dir = os.path.dirname(full_path)
            test_pattern = os.path.basename(full_path)

            base_cmd = [sys.executable, "-m", "unittest", "discover", "-s", test_dir, "-p", test_pattern]
            if verbose:
                base_cmd.append("-v")

            cmd = base_cmd
            if coverage:
                cmd = [sys.executable, "-m", "coverage", "run", "--source=.", "-m"] + base_cmd[2:]

            try:
                process = subprocess.run(cmd, cwd=self.output_dir, capture_output=True, text=True, check=False)

                if process.returncode == 0:
                    results[file_path] = {"status": "success", "output": process.stdout}
                    if coverage:
                        coverage_cmd = [sys.executable, "-m", "coverage", "report"]
                        coverage_process = subprocess.run(
                            coverage_cmd, cwd=self.output_dir, capture_output=True, text=True, check=False
                        )
                        results[file_path]["coverage"] = coverage_process.stdout  # type: ignore
                else:
                    results[file_path] = {"status": "error", "output": process.stdout, "error": process.stderr}
                    success = False
            except Exception as e:
                logger.error(f"Помилка при запуску тестів для '{file_path}': {e}", exc_info=True)
                results[file_path] = {"status": "error", "message": str(e)}
                success = False

        return {"status": "success" if success else "error", "results": results, "files_tested": len(test_files)}

    def generate_tests(self, source_files: List[str], gemini_interaction=None) -> Dict[str, object]:
        """Генерує тести для вказаних файлів.

        Args:
            source_files (List[str]): Список файлів, для яких потрібно згенерувати тести.
            gemini_interaction: Екземпляр GeminiInteraction для генерації тестів.

        Returns:
            Dict[str, object]: Результат генерації тестів.
        """
        results: Dict = {}
        success = True

        for file_path in source_files:
            full_path = os.path.join(self.output_dir, file_path)
            if not os.path.exists(full_path):
                logger.warning(f"Файл '{file_path}' не існує")
                results[file_path] = {"status": "error", "message": "Файл не існує"}
                success = False
                continue

            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()

                test_code = None
                if gemini_interaction:
                    prompt_parts = [
                        "Ти - AI-асистент для генерації тестів.",
                        f"Потрібно згенерувати тести для файлу {file_path}:",
                        f"```python\n{content}\n```",
                        "Згенеруй модульні тести для всіх функцій та класів у файлі.",
                        "Використовуй бібліотеку unittest.",
                        "Поверни лише код тестів без пояснень.",
                    ]

                    response = gemini_interaction.generate_content(
                        prompt_parts=prompt_parts, generation_config={"response_mime_type": "text/plain"}
                    )

                    if response:
                        test_code = response.strip()
                    else:
                        results[file_path] = {
                            "status": "error",
                            "message": "Не вдалося згенерувати тести за допомогою Gemini",
                        }
                        success = False

                if not test_code:
                    logger.info(
                        f"Gemini не доступний або не зміг згенерувати тести. Генеруємо прості тести для {file_path}."
                    )
                    test_code = self._generate_simple_tests(file_path, content)

                if test_code:
                    test_file_name = f"test_{os.path.basename(file_path)}"
                    test_file_path = os.path.join(os.path.dirname(full_path), test_file_name)

                    with open(test_file_path, "w", encoding="utf-8") as f:
                        f.write(test_code)

                    results[file_path] = {"status": "success", "test_file": test_file_path}

            except Exception as e:
                logger.error(f"Помилка при генерації тестів для '{file_path}': {e}", exc_info=True)
                results[file_path] = {"status": "error", "message": str(e)}
                success = False

        return {"status": "success" if success else "error", "results": results, "files_processed": len(source_files)}

    def _generate_simple_tests(self, file_path: str, content: str) -> str:
        """Генерує прості тести-заглушки для файлу.

        Args:
            file_path (str): Шлях до файлу.
            content (str): Вміст файлу.

        Returns:
            str: Згенерований код тестів.
        """
        try:
            tree = ast.parse(content)
        except SyntaxError:  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa  # noqa
            module_name = os.path.basename(file_path).split(".")[0]
            module_name_formatted = module_name.title().replace("_", "")
            return f'''import unittest

class Test{module_name_formatted}(unittest.TestCase):
    """Клас Test{module_name_formatted}."""























    def test_syntax(self) -> None:
        \"\"\"Test method.\"\"\"
        """Метод test_syntax. Перевіряє синтаксис файлу, який не вдалося розпарсити."""























        self.fail("Файл містить синтаксичні помилки")

if __name__ == '__main__':
    unittest.main()
'''

        classes: List = []
        functions: List = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes.append(node.name)
            elif isinstance(node, ast.FunctionDef):
                # Перевіряємо, чи це функція верхнього рівня
                is_top_level = any(
                    isinstance(parent, ast.Module)
                    for parent in ast.walk(tree)
                    if hasattr(parent, "body") and node in parent.body  # type: ignore
                )
                if is_top_level:
                    functions.append(node.name)

        module_name = os.path.basename(file_path).split(".")[0]
        module_name_formatted = module_name.title().replace("_", "")
        test_code = f'''import unittest
# TODO: Додайте необхідні імпорти з {module_name}
# from {module_name} import ...

class Test{module_name_formatted}(unittest.TestCase):
    """Клас Test{module_name_formatted}. Тести для модуля {module_name}."""
'''

        if not classes and not functions:
            test_code += f'''
    def test_module_import(self) -> None:
        \"\"\"Test method.\"\"\"
        """Метод test_module_import. Перевіряє, чи модуль можна імпортувати без помилок."""























        try:
            import {module_name}
        except Exception as e:
            self.fail(f"Не вдалося імпортувати модуль {module_name}: {{e}}")
'''

        for class_name in classes:
            test_code += f'''
    def test_{class_name.lower()}_initialization(self):
        """Метод test_{class_name.lower()}_initialization. Тестує ініціалізацію класу {class_name}."""























        # TODO: Додайте тест для ініціалізації класу {class_name}
        self.skipTest("Тест для {class_name} ще не реалізовано.")
'''

        for function_name in functions:
            test_code += f'''
    def test_{function_name}(self):
        """Метод test_{function_name}. Тестує функцію {function_name}."""























        # TODO: Додайте тести для функції {function_name}
        self.skipTest("Тест для {function_name} ще не реалізовано.")
'''

        test_code += """
if __name__ == '__main__':
    unittest.main()
"""

        return test_code
