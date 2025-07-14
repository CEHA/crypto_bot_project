import logging
import os
from typing import Dict

from modules.utils.gemini_client import GeminiClient as GeminiInteraction


logger = logging.getLogger(__name__)


class CodeReviewer:
    """Модуль для виконання огляду коду (code review)."""

    def __init__(self, gemini_interaction: GeminiInteraction, output_dir: str, **kwargs) -> None:
        """Метод __init__."""
        self.gemini_interaction = gemini_interaction
        self.output_dir = output_dir
        logger.info("CodeReviewer ініціалізовано")

    def handle_task(self, task: Dict[str, object]) -> Dict[str, object]:
        """Обробляє завдання огляду коду."""
        review_type = task.get("review_type")
        target_files = task.get("target_files", [])

        if review_type != "file_review":
            return {"status": "error", "message": f"Непідтримуваний тип огляду: {review_type}"}

        if not target_files:
            return {"status": "error", "message": "Для 'file_review' потрібні 'target_files'."}

        review_results: Dict = {}
        for file_path in target_files:
            full_path = os.path.join(self.output_dir, file_path)
            if not os.path.exists(full_path):
                review_results[file_path] = {"status": "error", "message": "File not found."}
                logger.warning(f"Файл для огляду не знайдено: {full_path}")
                continue

            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()

                prompt = (
                    "Ти - досвідчений розробник та code reviewer. Проаналізуй наступний код Python. "
                    "Зверни увагу на якість коду, потенційні помилки, відповідність PEP 8, "
                    "можливості для рефакторингу та загальну чистоту коду. "
                    "Надай свій відгук у форматі JSON з ключами 'assessment' (оцінка: 'good', 'needs_improvement', 'critical') "
                    "та 'recommendations' (список рядків з рекомендаціями).\n\n"
                    f"Файл: `{file_path}`\n"
                    "```python\n"
                    f"{content}\n"
                    "```"
                )

                response = self.gemini_interaction.generate_content(
                    prompt_parts=[prompt], generation_config={"response_mime_type": "application/json"}
                )

                if response:
                    review_results[file_path] = {"status": "success", "review": response}
                else:
                    review_results[file_path] = {
                        "status": "error",
                        "message": "Не вдалося отримати відповідь від Gemini.",
                    }

            except Exception as e:
                logger.error(f"Помилка під час огляду файлу {file_path}: {e}", exc_info=True)
                review_results[file_path] = {"status": "error", "message": str(e)}

        return {"status": "success", "message": "Огляд коду завершено.", "results": review_results}
