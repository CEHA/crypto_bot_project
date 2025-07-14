"""Safe task queue cleaner for removing obsolete tasks."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List

from modules.core.task_queue import TaskQueue


logger = logging.getLogger(__name__)


class TaskCleaner:
    """Safely cleans obsolete tasks from the queue."""

    def __init__(self, task_queue: TaskQueue) -> None:
        """Метод __init__."""
        self.task_queue = task_queue

    def clean_safe(self, max_age_days: int = 7, backup: bool = True) -> Dict[str, int]:
        """Safely removes old completed/failed tasks.

        Args:
            max_age_days: Remove tasks older than this many days
            backup: Create backup before cleaning

        Returns:
            Dict with cleanup statistics
        """
        if backup:
            self._create_backup()

        cutoff_date = datetime.now() - timedelta(days=max_age_days)

        original_count = len(self.task_queue.tasks)
        removed_tasks = []

        # Keep tasks that are safe to remove
        self.task_queue.tasks = [
            task for task in self.task_queue.tasks if not self._should_remove_task(task, cutoff_date, removed_tasks)
        ]

        removed_count = len(removed_tasks)
        if removed_count > 0:
            self.task_queue._save_tasks()
            logger.info(f"Cleaned {removed_count} obsolete tasks")

        return {
            "original_count": original_count,
            "removed_count": removed_count,
            "remaining_count": len(self.task_queue.tasks),
            "backup_created": backup,
        }

    def _should_remove_task(self, task: Dict, cutoff_date: datetime, removed_tasks: List) -> bool:
        """Determines if a task should be removed."""
        status = task.get("status")

        # Never remove pending or processing tasks
        if status in ["pending", "processing"]:
            return False

        # Remove old completed tasks
        if status == "completed":
            completed_time = task.get("completed_time")
            if completed_time and self._is_older_than(completed_time, cutoff_date):
                removed_tasks.append(task)
                return True

        # Remove old failed tasks (but keep recent ones for debugging)
        if status == "failed":
            completed_time = task.get("completed_time")
            if completed_time and self._is_older_than(completed_time, cutoff_date):
                removed_tasks.append(task)
                return True

        return False

    def _is_older_than(self, timestamp_str: str, cutoff_date: datetime) -> bool:
        """Checks if timestamp is older than cutoff date."""
        try:
            task_date = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            return task_date < cutoff_date
        except (ValueError, AttributeError):
            return False

    def _create_backup(self) -> None:
        """Creates backup of current task queue."""
        backup_file = f"{self.task_queue.queue_file_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        try:
            import shutil

            shutil.copy2(self.task_queue.queue_file_path, backup_file)
            logger.info(f"Backup created: {backup_file}")
        except Exception as e:
            logger.warning(f"Failed to create backup: {e}")

    def get_cleanup_preview(self, max_age_days: int = 7) -> Dict:
        """Preview what would be cleaned without actually removing."""
        cutoff_date = datetime.now() - timedelta(days=max_age_days)

        to_remove = []
        for task in self.task_queue.tasks:
            if self._should_remove_task(task, cutoff_date, to_remove):
                pass  # Task added to to_remove in _should_remove_task

        return {
            "total_tasks": len(self.task_queue.tasks),
            "tasks_to_remove": len(to_remove),
            "tasks_to_keep": len(self.task_queue.tasks) - len(to_remove),
            "removal_details": [
                {"type": task.get("type"), "status": task.get("status"), "age_days": self._get_task_age_days(task)}
                for task in to_remove[:5]  # Show first 5
            ],
        }

    def _get_task_age_days(self, task: Dict) -> int:
        """Gets task age in days."""
        completed_time = task.get("completed_time") or task.get("added_time")
        if not completed_time:
            return 0
        try:
            task_date = datetime.fromisoformat(completed_time.replace("Z", "+00:00"))
            return (datetime.now() - task_date).days
        except (ValueError, AttributeError):
            return 0
