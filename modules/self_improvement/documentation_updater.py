import logging
import os
import re
from datetime import datetime
from typing import Dict, List, Optional

from modules.core.module_registry import ModuleRegistry
from modules.self_improvement.code_fixer import CodeFixer  # For type hinting, or direct use if needed
from modules.utils.json_analyzer import JsonAnalyzer


logger = logging.getLogger(__name__)


class DocumentationUpdater:
    """Клас для оновлення документації системи."""

    def __init__(self, gemini_interaction, json_analyzer: JsonAnalyzer, output_dir: str) -> None:
        """Метод __init__."""
        self.gemini_interaction = gemini_interaction
        self.json_analyzer = json_analyzer
        self.output_dir = output_dir
        self.registry = ModuleRegistry()  # To get CodeFixer instance
        logger.info("DocumentationUpdater ініціалізовано")

    def handle_task(self, task: Dict[str, object]) -> Dict[str, object]:
        """Обробляє завдання, пов'язані з документацією.

        Args:
            task (Dict[str, object]): Словник, що описує завдання.
                                   Очікувані поля:
                                   - 'documentation_type': Тип документаційного завдання (наприклад, 'generate_docstrings', 'update_system_status_report').
                                   - 'target_files' (опціонально): Список файлів для обробки.
                                   - 'description' (опціонально): Опис завдання.

        Returns:
            Dict[str, object]: Результат виконання завдання.
        """
        documentation_type = task.get("doc_type")  # Changed from "documentation_type" to "doc_type"
        description = task.get("description", "Оновлення документації")
        target_files = task.get("target_files", [])

        logger.info(f"Обробка завдання документації типу: {documentation_type}")

        if documentation_type == "generate_docstrings":
            if not target_files:
                return {"status": "error", "message": "Для генерації докстрінгів потрібні target_files."}

            code_fixer: Optional[CodeFixer] = self.registry.get_instance("code_fixer")
            if not code_fixer:
                logger.error("CodeFixer не ініціалізовано. Неможливо генерувати докстрінги.")
                return {"status": "error", "message": "CodeFixer not initialized."}

            results: List = []
            for file_path in target_files:
                full_file_path = os.path.join(self.output_dir, file_path)
                result = code_fixer.handle_documentation_generation(full_file_path)
                results.append(result)
            return {"status": "success", "message": "Генерація докстрінгів завершена.", "results": results}

        elif documentation_type == "update_system_status_report":
            # This task type would typically involve reading current system state
            # and generating a report. For now, it's a conceptual placeholder.
            return self._update_system_status_report(description)

        elif documentation_type == "update_all_documentation":
            # This is a high-level task, likely orchestrating other documentation tasks
            # For now, it's a conceptual placeholder.
            return self._update_all_documentation(description)

        elif documentation_type == "update_readme":
            return self._update_readme(description)

        elif documentation_type == "update_info_docs":  # NEW TYPE
            return self._update_info_documentation(description)

        elif documentation_type == "update_gitignore":
            return self._update_gitignore(description)

        elif documentation_type == "release_notes":
            return self._generate_release_notes(description)

        elif documentation_type == "pull_request_report":
            return self._generate_pull_request_report(description)

        else:
            return {"status": "error", "message": f"Невідомий тип документаційного завдання: {documentation_type}"}

    def _update_system_status_report(self, description: str) -> Dict[str, object]:
        """Оновлює звіт про стан системи.

        Це концептуальний метод, який в реальності збирав би дані з різних модулів.
        """
        logger.info(f"Оновлення звіту про стан системи: {description}")
        # Тут буде логіка збору даних про стан системи (кількість файлів, помилок, тощо)
        # та генерація Markdown звіту.
        # Для прикладу, просто повернемо успіх.
        report_path = os.path.join(self.output_dir, "docs", "system_status_report.md")
        try:
            # Simulate updating the report
            with open(report_path, "a", encoding="utf-8") as f:
                f.write(f"\n\n## Оновлення: {description} ({os.path.basename(report_path)})")
            logger.info(f"Звіт про стан системи оновлено: {report_path}")
            return {"status": "success", "message": f"Звіт про стан системи оновлено: {report_path}"}
        except Exception as e:
            logger.error(f"Помилка при оновленні звіту про стан системи: {e}", exc_info=True)
            return {"status": "error", "message": f"Помилка при оновленні звіту про стан системи: {e}"}

    def _update_all_documentation(self, description: str) -> Dict[str, object]:
        """Оновлює всю документацію в проекті.

        Цей метод буде оркеструвати інші завдання документації.
        """
        logger.info(f"Оновлення всієї документації: {description}")
        # In a real scenario, this would iterate through files,
        # identify documentation needs, and add tasks to the queue.
        # For now, it's a conceptual placeholder.
        return {"status": "success", "message": "Оновлення всієї документації завершено (концептуально)."}

    def _update_readme(self, description: str) -> Dict[str, object]:
        """Оновлює README.md на основі наданого опису.

        Це концептуальний метод. В реальності він би використовував Gemini
        для генерації нового вмісту README.
        """
        logger.info(f"Оновлення README.md: {description}")
        readme_path = os.path.join(self.output_dir, "README.md")
        try:
            with open(readme_path, "a", encoding="utf-8") as f:
                f.write(f"\n\n<!-- Оновлення: {description} ({datetime.now().isoformat()}) -->")
            return {"status": "success", "message": f"README.md оновлено: {readme_path}"}
        except Exception as e:
            logger.error(f"Помилка при оновленні README.md: {e}", exc_info=True)
            return {"status": "error", "message": f"Помилка при оновленні README.md: {e}"}

    def _update_info_documentation(self, description: str) -> Dict[str, object]:
        """Оновлює файли документації в папці 'info' за допомогою Gemini."""
        logger.info(f"Оновлення файлів документації в папці 'info': {description}")
        info_dir = os.path.join(self.output_dir, "info")
        os.makedirs(info_dir, exist_ok=True)

        doc_files_to_update = {
            "architecture_vision.md": "Опиши поточне архітектурне бачення проекту. Включи основні компоненти, їх взаємодію та загальні принципи дизайну.",
            "self_improvement_strategy.md": "Опиши стратегію самовдосконалення DevAgent. Як агент ідентифікує, планує, виконує та оцінює власні покращення?",
            "refactoring_capabilities.md": "Детально опиши можливості DevAgent щодо рефакторингу коду. Які типи рефакторингу він може виконувати?",
            "analysis_capabilities.md": "Детально опиши можливості DevAgent щодо аналізу коду та проекту. Які типи аналізу він може виконувати?",
        }

        overall_status = "success"
        results: Dict = {}

        for filename, prompt_description in doc_files_to_update.items():
            file_path = os.path.join(info_dir, filename)
            logger.info(f"Генерація вмісту для {filename}...")

            prompt_parts = [
                "Ти - експерт з документації та архітектури програмного забезпечення. "
                "Твоє завдання - створити або оновити документ, який детально описує аспект проекту.",
                f"Напиши вміст для файлу `{filename}` на основі наступного запиту:",
                f"--- ЗАПИТ ---\n{prompt_description}\n--- КІНЕЦЬ ЗАПИТУ ---",
                "Поверни ТІЛЬКИ вміст документа у форматі Markdown. Не додавай жодних пояснень, коментарів чи markdown-обгорток.",
            ]

            try:
                generated_content = self.gemini_interaction.generate_content(
                    prompt_parts=prompt_parts, generation_config={"response_mime_type": "text/plain"}
                )

                if generated_content:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(generated_content.strip())
                    results[filename] = {"status": "success", "message": "Файл успішно оновлено."}
                    logger.info(f"Файл {filename} успішно оновлено.")
                else:
                    results[filename] = {"status": "error", "message": "Gemini не згенерував вміст."}
                    overall_status = "error"
                    logger.error(f"Gemini не згенерував вміст для {filename}.")
            except Exception as e:
                results[filename] = {"status": "error", "message": str(e)}
                overall_status = "error"
                logger.error(f"Помилка при оновленні файлу {filename}: {e}", exc_info=True)

        return {
            "status": overall_status,
            "message": "Оновлення файлів документації в папці 'info' завершено.",
            "results": results,
        }

    def _update_gitignore(self, description: str) -> Dict[str, object]:
        """Оновлює файл .gitignore, додаючи до нього згенеровані файли та папки."""
        logger.info(f"Оновлення .gitignore: {description}")
        gitignore_path = os.path.join(self.output_dir, ".gitignore")

        # Список записів, які потрібно перевірити та додати, якщо вони відсутні
        entries_to_add = [
            "task_queue.json",
            # Додайте інші згенеровані файли/папки, які мають бути ігноровані, якщо вони не є частиною стандартного шаблону .gitignore
        ]

        try:
            current_content = ""
            if os.path.exists(gitignore_path):
                with open(gitignore_path, "r", encoding="utf-8") as f:
                    current_content = f.read()

            updated_content = current_content
            added_count = 0
            for entry in entries_to_add:
                if entry not in updated_content:
                    if not updated_content.endswith("\n"):  # Переконаємося, що є новий рядок перед додаванням
                        updated_content += "\n"
                    updated_content += f"{entry}\n"
                    added_count += 1
                    logger.info(f"Додано '{entry}' до .gitignore.")

            if added_count > 0:
                with open(gitignore_path, "w", encoding="utf-8") as f:
                    f.write(updated_content)
                return {
                    "status": "success",
                    "message": f".gitignore успішно оновлено: {gitignore_path}. Додано {added_count} нових записів.",
                }
            else:
                return {
                    "status": "success",
                    "message": ".gitignore вже містить усі необхідні записи. Оновлення не потрібне.",
                }

        except Exception as e:
            logger.error(f"Помилка при оновленні .gitignore: {e}", exc_info=True)
            return {"status": "error", "message": f"Помилка при оновленні .gitignore: {e}"}

    def _generate_release_notes(self, description: str) -> Dict[str, object]:
        """Генерує примітки до релізу на основі останніх змін. (Заглушка)."""
        logger.info(f"Генерація приміток до релізу: {description}")

        git_module = self.registry.get_instance("git_module")
        if not git_module:
            logger.error("GitModule не ініціалізовано. Неможливо згенерувати release notes.")
            return {"status": "error", "message": "GitModule not initialized."}

        # 1. Отримати останній тег, щоб визначити, звідки починати історію
        latest_tag = git_module.get_latest_tag()
        logger.info(f"Генерація release notes з комітів після тегу: {latest_tag if latest_tag else 'початку історії'}")

        # 2. Отримати історію комітів з моменту останнього тегу
        commit_history = git_module.get_commit_history(since_ref=latest_tag)

        if not commit_history:
            logger.info("Не знайдено нових комітів для генерації release notes.")
            return {"status": "success", "message": "Нових комітів для release notes не знайдено."}

        # 3. Згрупувати коміти за типом (Conventional Commits)
        commit_groups = {
            "feat": [],
            "fix": [],
            "refactor": [],
            "docs": [],
            "test": [],
            "chore": [],
            "other": [],
        }

        conventional_commit_pattern = re.compile(r"^(feat|fix|refactor|docs|test|chore)(\(.*\))?:\s.*")

        for commit in commit_history:
            match = conventional_commit_pattern.match(commit["subject"])
            commit_type = match.group(1) if match else "other"
            commit_groups.get(commit_type, commit_groups["other"]).append(commit)

        # 4. Сформувати структурований Markdown з історії комітів
        markdown_summary = ""
        group_titles = {
            "feat": "🚀 Нові можливості",
            "fix": "🐛 Виправлення помилок",
            "refactor": "🔨 Рефакторинг",
            "docs": "📚 Документація",
            "test": "✅ Тести",
            "chore": "🔧 Інші зміни та обслуговування",
            "other": "📝 Інші коміти",
        }

        for group, title in group_titles.items():
            if commit_groups[group]:
                markdown_summary += f"### {title}\n"
                for commit in commit_groups[group]:
                    markdown_summary += f"- {commit['subject']} (`{commit['hash'][:7]}`)\n"
                markdown_summary += "\n"

        # 5. Використати Gemini для створення більш "людського" опису
        prompt_parts = [
            "Ти - технічний письменник, який створює примітки до релізу (release notes).",
            "На основі наступного списку комітів, згрупованих за типом, напиши короткий, але інформативний опис змін для користувачів та розробників.",
            "Збережи структуру та додай короткий вступний параграф. Використовуй Markdown для форматування.",
            "--- ЗГРУПОВАНІ КОМІТИ ---",
            markdown_summary,
            "--- КІНЕЦЬ ЗГРУПОВАНИХ КОМІТІВ ---",
            "Поверни ТІЛЬКИ готовий текст для release notes у форматі Markdown.",
        ]

        try:
            release_notes_content = self.gemini_interaction.generate_content(
                prompt_parts=prompt_parts, generation_config={"response_mime_type": "text/plain"}
            )

            if not release_notes_content:
                logger.warning("Gemini не згенерував вміст для release notes. Використовується базовий список комітів.")
                release_notes_content = markdown_summary

            # 6. Зберегти результат у файл
            release_notes_path = os.path.join(self.output_dir, "RELEASE_NOTES.md")
            new_version_name = f"v{datetime.now().strftime('%Y.%m.%d')}"  # Проста версіонізація

            final_content = f"# Примітки до релізу {new_version_name}\n\n"
            final_content += release_notes_content.strip()

            with open(release_notes_path, "w", encoding="utf-8") as f:
                f.write(final_content)

            logger.info(f"Примітки до релізу успішно згенеровано та збережено у файл: {release_notes_path}")

            # 7. Створити та запушити Git-тег
            # Використовуємо більш унікальний тег, щоб уникнути конфліктів при частих запусках
            new_tag_name = f"v{datetime.now().strftime('%Y.%m.%d-%H%M%S')}"
            tag_message = f"Реліз {new_version_name}"

            if git_module.create_tag(new_tag_name, tag_message):
                git_module.push_tags()  # Push the new tag to remote
            else:
                logger.warning(f"Не вдалося створити Git-тег {new_tag_name}.")

            return {
                "status": "success",
                "message": "Примітки до релізу успішно згенеровано.",
                "file_path": release_notes_path,
                "tag_created": new_tag_name,
            }

        except Exception as e:
            logger.error(f"Помилка під час генерації release notes: {e}", exc_info=True)
            return {"status": "error", "message": f"Помилка під час генерації release notes: {e}"}

    def _generate_pull_request_report(self, description: str) -> Dict[str, object]:
        """Генерує звіт для pull-request. (Заглушка)."""
        logger.info(f"Генерація звіту для pull-request: {description} (заглушка).")
        return {"status": "success", "message": "Функціональність генерації звіту для pull-request ще не реалізована."}
