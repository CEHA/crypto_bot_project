import json
import logging
from typing import Dict, List, Optional

from modules.core.module_registry import ModuleRegistry  # To get CodeFixer instance
from modules.utils.gemini_client import GeminiClient as GeminiInteraction
from modules.utils.json_analyzer import JsonAnalyzer


logger = logging.getLogger(__name__)


class RefactoringExecutor:
    """Модуль RefactoringExecutor відповідає за виконання завдань рефакторингу.

    Він взаємодіє з Gemini для генерації пропозицій рефакторингу та CodeFixer для їх застосування.
    """

    def __init__(self, gemini_interaction: GeminiInteraction, json_analyzer: JsonAnalyzer, output_dir: str) -> None:
        """Метод __init__."""
        self.gemini_interaction = gemini_interaction
        self.json_analyzer = json_analyzer
        self.output_dir = output_dir
        # CodeFixer will be retrieved when needed, as it's initialized separately in DevAgent
        self.registry = ModuleRegistry()  # Get the singleton registry
        logger.info("RefactoringExecutor ініціалізовано")

    def execute_refactoring_task(
        self, refactoring_type: str, files: List[str], description: Optional[str] = None
    ) -> Dict[str, object]:
        """Виконує завдання рефакторингу певного типу для вказаних файлів.

        Цей метод буде делегувати виклики до відповідних методів CodeFixer.
        """
        logger.info(f"Виконання завдання рефакторингу типу '{refactoring_type}' для файлів: {files}")

        code_fixer = self.registry.get_instance("code_fixer")
        if not code_fixer:
            logger.error("CodeFixer не ініціалізовано. Неможливо виконати рефакторинг.")
            return {"status": "error", "message": "CodeFixer not initialized."}

        # Some refactoring types might not require files (e.g., handle_runtime_error, handle_pylance_issues)
        if not files and refactoring_type not in ["handle_runtime_error", "handle_pylance_issues"]:
            return {
                "status": "error",
                "message": f"Некоректне завдання на рефакторинг: refactoring_type='{refactoring_type}', кількість файлів=0.",
            }

        if refactoring_type == "handle_complex_methods":
            results: List = []
            for file_path in files:
                result = code_fixer.handle_complex_methods(file_path)
                results.append(result)
            return {"status": "success", "message": "Рефакторинг складних методів завершено.", "results": results}
        elif refactoring_type == "handle_dead_code":
            results: List = []
            for file_path in files:
                result = code_fixer.handle_dead_code(file_path)
                results.append(result)
            return {"status": "success", "message": "Видалення мертвого коду завершено.", "results": results}
        elif refactoring_type == "handle_general_refactoring":
            if not description:
                return {"status": "error", "message": "Для загального рефакторингу потрібен опис."}
            results: List = []
            for file_path in files:
                result = code_fixer.handle_general_refactoring(file_path, description)
                results.append(result)
            return {"status": "success", "message": "Загальний рефакторинг завершено.", "results": results}
        elif refactoring_type == "handle_architectural_improvement":
            if not description:
                return {"status": "error", "message": "Для архітектурного покращення потрібен опис."}
            result = code_fixer.handle_architectural_improvement(files, description)
            return {"status": "success", "message": "Архітектурне покращення завершено.", "results": [result]}
        elif refactoring_type == "handle_runtime_error":
            if not description:
                return {"status": "error", "message": "Для виправлення помилки виконання потрібен опис."}
            result = code_fixer.handle_runtime_error(description)
            return {"status": "success", "message": "Виправлення помилки виконання завершено.", "results": [result]}
        elif refactoring_type == "apply_auto_refactoring":
            results: List = []
            for file_path in files:
                result = code_fixer.apply_auto_refactoring(file_path)
                results.append(result)
            return {"status": "success", "message": "Автоматичний рефакторинг завершено.", "results": results}
        elif refactoring_type == "handle_pylance_issues":
            if not description:  # Assuming description contains the pylance report JSON string
                return {"status": "error", "message": "Для виправлення Pylance помилок потрібен звіт."}
            try:
                pylance_report = json.loads(description)
                result = code_fixer.handle_pylance_issues(pylance_report)
                return {"status": "success", "message": "Виправлення Pylance помилок завершено.", "results": [result]}
            except json.JSONDecodeError:
                return {"status": "error", "message": "Некоректний формат Pylance звіту (не JSON)."}
        elif refactoring_type == "handle_async_migration":
            result = code_fixer.handle_async_migration(files)
            return {"status": "success", "message": "Міграція на asyncio завершено.", "results": [result]}
        elif refactoring_type == "handle_instrumentation_addition":
            result = code_fixer.handle_instrumentation_addition(files)
            return {"status": "success", "message": "Додавання інструментації завершено.", "results": [result]}
        else:
            return {"status": "error", "message": f"Невідомий тип рефакторингу: {refactoring_type}"}
