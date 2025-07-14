import json
import logging
import os
from datetime import datetime
from typing import Dict, List

from modules.core.task_queue import TaskQueue
from modules.utils.git_module import GitModule


logger = logging.getLogger(__name__)


class PullRequestMonitor:
    """Моніторить Pull Request-и, створені DevAgent, та закриває їх після злиття."""

    def __init__(self, git_module: GitModule, task_queue: TaskQueue, output_dir: str) -> None:
        """Метод __init__."""
        self.git_module = git_module
        self.task_queue = task_queue
        self.monitor_file = os.path.join(output_dir, "monitored_prs.json")
        self.monitored_prs: List[Dict[str, object]] = self._load_monitored_prs()
        logger.info("PullRequestMonitor ініціалізовано.")

    def _load_monitored_prs(self) -> List[Dict[str, object]]:
        """Завантажує список PR, що моніторяться, з файлу."""
        if os.path.exists(self.monitor_file):
            try:
                with open(self.monitor_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Помилка завантаження файлу моніторингу PR: {e}", exc_info=True)
        return []

    def _save_monitored_prs(self) -> None:
        """Зберігає список PR, що моніторяться, у файл."""
        try:
            with open(self.monitor_file, "w", encoding="utf-8") as f:
                json.dump(self.monitored_prs, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Помилка збереження файлу моніторингу PR: {e}", exc_info=True)

    def add_pr_to_monitor(self, pr_number: int, branch_name: str, description: str) -> None:
        """Додає Pull Request до списку моніторингу."""
        pr_info = {
            "pr_number": pr_number,
            "branch_name": branch_name,
            "description": description,
            "status": "open",
            "created_at": datetime.now().isoformat(),
        }
        self.monitored_prs.append(pr_info)
        self._save_monitored_prs()
        logger.info(f"PR #{pr_number} додано до моніторингу.")

    def check_and_close_merged_prs(self) -> Dict[str, object]:
        """Перевіряє статус Pull Request-ів, що моніторяться, та закриває злиті."""
        logger.info("Початок перевірки Pull Request-ів на злиття.")
        closed_count = 0
        updated_prs: List = []

        for pr_info in self.monitored_prs:
            pr_number = pr_info.get("pr_number")
            if pr_number is None:
                updated_prs.append(pr_info)  # Keep invalid entries for manual review
                continue

            status = self.git_module.get_pull_request_status(pr_number)

            if status == "merged":
                logger.info(f"Pull Request #{pr_number} виявлено як злитий. Закриваємо...")
                if self.git_module.close_pull_request(pr_number):
                    pr_info["status"] = "merged_and_closed"
                    closed_count += 1
                else:
                    pr_info["status"] = "merged_but_close_failed"
                updated_prs.append(pr_info)  # Keep merged PRs in history for now
            elif status == "closed":
                logger.info(f"Pull Request #{pr_number} вже закрито (не через злиття). Видаляємо з моніторингу.")
                pr_info["status"] = "closed_manually"
                updated_prs.append(pr_info)  # Keep closed PRs in history for now
            elif status == "open":
                logger.debug(f"Pull Request #{pr_number} все ще відкрито.")
                updated_prs.append(pr_info)
            else:  # Error or None status
                logger.warning(f"Не вдалося отримати статус для PR #{pr_number}. Залишаємо в моніторингу.")
                updated_prs.append(pr_info)

        # Оновлюємо список моніторингу, видаляючи ті, що були успішно закриті/оброблені
        # For simplicity, let's keep all processed PRs in the file for historical tracking
        # A more advanced system might move them to a 'history' file or remove them.
        self.monitored_prs = [
            pr for pr in updated_prs if pr.get("status") not in ["merged_and_closed", "closed_manually"]
        ]
        self._save_monitored_prs()

        logger.info(f"Завершено перевірку PR. Закрито {closed_count} PR-ів.")
        return {"status": "success", "closed_prs_count": closed_count}
