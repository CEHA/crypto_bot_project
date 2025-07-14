import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional


# task_queue.py  # type: ignore


# Configure logging for the module.
# This setup ensures that the module's operations are logged,
# which is crucial for debugging and monitoring asynchronous processes.
logger = logging.getLogger(__name__)


class TaskQueue:
    """Manages a persistent queue of tasks stored in a JSON file."""

    def __init__(self, queue_file_path: str) -> None:
        """Initializes the TaskQueue.

        Args:
            queue_file_path: The path to the JSON file used for the queue.
        """
        self.queue_file_path = queue_file_path
        self.tasks: List[Dict[str, object]] = self._load_tasks()
        logger.info(f"TaskQueue initialized with queue_file_path={self.queue_file_path}")

    def _load_tasks(self) -> List[Dict[str, object]]:
        """Loads tasks from the queue file."""
        if os.path.exists(self.queue_file_path):
            try:
                with open(self.queue_file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    if not content.strip():  # Handle empty file
                        return []
                    # Reset file pointer to the beginning before loading
                    f.seek(0)
                    return json.load(f)
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding JSON from task queue file {self.queue_file_path}: {e}")
                # Optionally, backup the corrupted file and start with an empty queue
                return []
        return []

    def _save_tasks(self) -> None:
        """Saves the current list of tasks to the queue file."""
        try:
            with open(self.queue_file_path, "w", encoding="utf-8") as f:
                json.dump(self.tasks, f, indent=2, ensure_ascii=False)
        except IOError as e:
            logger.error(f"Error saving tasks to queue file {self.queue_file_path}: {e}")

    def add_task(self, task: Dict[str, object]) -> None:
        """Adds a single task to the queue."""
        if "status" not in task:
            task["status"] = "pending"
        if "added_time" not in task:
            task["added_time"] = datetime.now().isoformat()
        self.tasks.append(task)
        self._save_tasks()
        logger.debug(f"Task added: {task.get('type')}")

    def add_tasks(self, tasks: List[Dict[str, object]]) -> None:
        """Adds multiple tasks to the queue."""
        for task in tasks:
            if "status" not in task:
                task["status"] = "pending"
            if "added_time" not in task:
                task["added_time"] = datetime.now().isoformat()
            self.tasks.append(task)
        self._save_tasks()
        logger.info(f"Added {len(tasks)} tasks to the queue.")

    def get_next_task(self) -> Optional[Dict[str, object]]:
        """Gets the next 'pending' task, marks it as 'processing', and returns it."""
        for task in self.tasks:
            if task.get("status") == "pending":
                task["status"] = "processing"
                task["start_time"] = datetime.now().isoformat()
                self._save_tasks()
                return task
        return None

    def mark_completed(self, task: Dict[str, object], result: object) -> None:
        """Marks a task as 'completed'."""
        task["status"] = "completed"
        task["completed_time"] = datetime.now().isoformat()
        task["result"] = result
        self._save_tasks()

    def mark_failed(self, task: Dict[str, object], error_message: str) -> None:
        """Marks a task as 'failed'."""
        task["status"] = "failed"
        task["completed_time"] = datetime.now().isoformat()
        task["error"] = error_message
        self._save_tasks()

    def get_stats(self) -> Dict[str, int]:
        """Returns a dictionary with counts of tasks by status."""
        stats = {"pending": 0, "processing": 0, "completed": 0, "failed": 0, "total": len(self.tasks)}
        for task in self.tasks:
            status = task.get("status", "unknown")
            if status in stats:
                stats[status] += 1
            else:
                stats["unknown"] = stats.get("unknown", 0) + 1
        return stats

    def load_tasks_from_file(self, file_path: str) -> List[Dict[str, object]]:
        """Loads tasks from a specified file (e.g., tasks.json) without adding them to the current queue."""
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding JSON from tasks file {file_path}: {e}")
                return []
        logger.warning(f"Tasks file '{file_path}' not found.")
        return []

    def requeue_processing_tasks(self) -> int:
        """Finds tasks that are stuck in 'processing' status and moves them back to 'pending'.

        This is useful for recovering from crashes or unexpected shutdowns.
        Returns the count of re-queued tasks.
        """
        requeued_count = 0
        for task in self.tasks:
            if task.get("status") == "processing":
                task["status"] = "pending"
                task["requeued_time"] = datetime.now().isoformat()  # Optional: add a timestamp for requeue
                requeued_count += 1
                logger.info(f"Re-queued task with description: {task.get('description', 'N/A')}")
        if requeued_count > 0:
            self._save_tasks()
        return requeued_count

    def requeue_failed_tasks(self, criteria: Dict[str, object]) -> int:
        """Re-queues failed tasks that match specific criteria."""
        requeued_count = 0
        for task in self.tasks:
            if task.get("status") == "failed":
                match = all(task.get(k) == v for k, v in criteria.items())
                if match:
                    task["status"] = "pending"
                    task["requeued_time"] = datetime.now().isoformat()
                    task.pop("error", None)  # Remove old error message
                    task.pop("completed_time", None)
                    requeued_count += 1
        if requeued_count > 0:
            self._save_tasks()
        return requeued_count

    def has_task_type(self, task_type: str) -> bool:
        """Checks if a task of a specific type is already in the queue."""
        for task in self.tasks:
            if task.get("type") == task_type and task.get("status") in ["pending", "processing"]:
                return True
        return False

    def clear_completed_tasks(self) -> int:
        """Removes all tasks with 'completed' status from the queue."""
        original_count = len(self.tasks)
        self.tasks = [t for t in self.tasks if t.get("status") != "completed"]
        removed_count = original_count - len(self.tasks)
        if removed_count > 0:
            self._save_tasks()
        return removed_count

    def safe_cleanup(self, max_age_days: int = 7) -> Dict[str, int]:
        """Safely removes old obsolete tasks."""
        from modules.core.task_cleaner import TaskCleaner

        cleaner = TaskCleaner(self)
        return cleaner.clean_safe(max_age_days=max_age_days)

    def preview_cleanup(self, max_age_days: int = 7) -> Dict:
        """Preview what would be cleaned."""
        from modules.core.task_cleaner import TaskCleaner

        cleaner = TaskCleaner(self)
        return cleaner.get_cleanup_preview(max_age_days=max_age_days)
