"""Обробники завдань для різних типів операцій."""

import logging
from typing import Dict


logger = logging.getLogger(__name__)


def handle_code_fix_task(task: Dict, agent) -> Dict:
    """Обробляє завдання виправлення коду."""
    try:
        error_type = task.get("error_type", "unknown")
        target_file = task.get("target_file", "")
        error_details = task.get("error_details", "")

        logger.info(f"Виправлення {error_type} помилки в файлі {target_file}")

        if error_type == "syntax" and target_file:
            # Використовуємо code_fixer для виправлення синтаксичних помилок
            if hasattr(agent, "code_fixer") and agent.code_fixer:
                result = agent.code_fixer.fix_syntax_error(target_file, error_details)
                if result.get("status") == "success":
                    # Позначаємо помилку як виправлену
                    if hasattr(agent, "log_analyzer"):
                        error_id = task.get("id", "").replace("fix-", "").split("-", 2)[-1]
                        agent.log_analyzer.mark_error_fixed(error_id)
                    return {"status": "success", "message": f"Синтаксичну помилку виправлено: {target_file}"}
                else:
                    return {
                        "status": "failed",
                        "message": f"Не вдалося виправити синтаксичну помилку: {result.get('message', 'Unknown error')}",
                    }

        elif error_type == "attribute":
            # Для помилок атрибутів використовуємо загальний підхід
            if hasattr(agent, "code_fixer") and agent.code_fixer:
                result = agent.code_fixer.fix_attribute_error(target_file, error_details)
                if result.get("status") == "success":
                    return {"status": "success", "message": f"Помилку атрибуту виправлено: {target_file}"}

        return {"status": "skipped", "message": f"Не вдалося обробити {error_type} помилку"}

    except Exception as e:
        logger.error(f"Помилка при обробці завдання виправлення коду: {e}")
        return {"status": "failed", "message": str(e)}


def handle_dependency_fix_task(task: Dict, agent) -> Dict:
    """Обробляє завдання виправлення залежностей."""
    try:
        error_details = task.get("error_details", "")

        # Витягуємо назву модуля з помилки
        import re

        module_match = re.search(r"No module named '([^']+)'", error_details)
        if not module_match:
            return {"status": "failed", "message": "Не вдалося визначити назву модуля"}

        module_name = module_match.group(1)
        logger.info(f"Спроба встановлення модуля: {module_name}")

        # Спробуємо встановити модуль
        import subprocess
        import sys

        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", module_name])
            logger.info(f"Модуль {module_name} успішно встановлено")

            # Позначаємо помилку як виправлену
            if hasattr(agent, "log_analyzer"):
                error_id = task.get("id", "").replace("fix-", "").split("-", 2)[-1]
                agent.log_analyzer.mark_error_fixed(error_id)

            return {"status": "success", "message": f"Модуль {module_name} встановлено"}

        except subprocess.CalledProcessError as e:
            return {"status": "failed", "message": f"Не вдалося встановити модуль {module_name}: {e}"}

    except Exception as e:
        logger.error(f"Помилка при обробці завдання виправлення залежностей: {e}")
        return {"status": "failed", "message": str(e)}


# Існуючі обробники (скорочені версії)
def handle_code_generation_task(task: Dict, agent) -> Dict:
    """Обробляє завдання генерації коду."""
    logger.info(f"Handling code generation task: {task.get('description', 'No description')}")
    return {"status": "success", "message": "Code generation completed"}


def handle_refactoring_task(task: Dict, agent) -> Dict:
    """Обробляє завдання рефакторингу."""
    logger.info(f"Handling refactoring task: {task.get('description', 'No description')}")
    return {"status": "success", "message": "Refactoring completed"}


def handle_query_task(task: Dict, agent) -> Dict:
    """Обробляє завдання запитів."""
    logger.info(f"Handling query task: {task.get('description', 'No description')}")
    return {"status": "success", "message": "Query processed"}


def handle_test_task(task: Dict, agent) -> Dict:
    """Обробляє завдання тестування."""
    logger.info(f"Handling test task: {task.get('description', 'No description')}")
    return {"status": "success", "message": "Test completed"}


def handle_self_improvement_task(task: Dict, agent) -> Dict:
    """Обробляє завдання самовдосконалення."""
    logger.info(f"Handling self-improvement task: {task.get('description', 'No description')}")
    return {"status": "success", "message": "Self-improvement completed"}


def handle_analysis_task(task: Dict, agent) -> Dict:
    """Обробляє завдання аналізу."""
    logger.info(f"Handling analysis task: {task.get('description', 'No description')}")
    return {"status": "success", "message": "Analysis completed"}


def handle_planning_task(task: Dict, agent) -> Dict:
    """Обробляє завдання планування."""
    logger.info(f"Handling planning task: {task.get('description', 'No description')}")
    return {"status": "success", "message": "Planning completed"}


def handle_documentation_task(task: Dict, agent) -> Dict:
    """Обробляє завдання документації."""
    logger.info(f"Handling documentation task: {task.get('description', 'No description')}")
    return {"status": "success", "message": "Documentation updated"}


def handle_code_review_task(task: Dict, agent) -> Dict:
    """Обробляє завдання огляду коду."""
    logger.info(f"Handling code review task: {task.get('description', 'No description')}")
    return {"status": "success", "message": "Code review completed"}
