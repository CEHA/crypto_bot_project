import heapq
import time
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(order=True)
class Task:
    """Represents a self-improvement task with an assigned priority.

    Tasks are comparable based on their priority, then insertion time,
    and finally a unique task ID to ensure a stable and deterministic order
    within the priority queue. Lower priority values indicate higher importance.

    Attributes:
        priority: A float indicating the task's importance. Lower values mean higher priority.
        insertion_time: A timestamp recording when the task was created. Used for FIFO tie-breaking.
        task_id: A unique integer ID for the task, ensuring stable ordering for identical priorities/timestamps.
        description: A string describing the self-improvement task.
    """

    priority: float
    insertion_time: float
    task_id: int
    description: str = field(compare=False)

    def __str__(self) -> str:
        """Returns a human-readable string representation of the Task."""
        return f"Task(desc='{self.description}', priority={self.priority:.2f}, id={self.task_id})"


class SelfImprovementPlanner:
    """A planner specialized in managing and prioritizing self-improvement tasks.

    This agent uses evaluated priorities to form its task queue, ensuring that
    the most critical or impactful self-improvement tasks are addressed first.
    It simulates the process of identifying, prioritizing, and managing a backlog
    of tasks aimed at enhancing its own capabilities or knowledge.
    """

    _task_counter: int = 0  # Class-level counter for unique task IDs

    def __init__(self) -> None:
        """Initializes the SelfImprovementPlanner with an empty priority queue for tasks.

        The priority queue stores Task objects, ordered automatically by
        the Task's `__lt__` method (priority, then insertion time, then task ID).
        """
        self._task_queue: List[Task] = []

    def _evaluate_task_priority(self, task_description: str) -> float:
        """Evaluates and assigns a priority score to a given task description.

        This method encapsulates the logic for determining a task's importance.
        Lower numerical values indicate higher priority (e.g., 1.0 is critical, 5.0 is low).

        Args:
            task_description: The description of the self-improvement task.

        Returns:
            A float representing the evaluated priority score.
        """
        priority_score = 5.0  # type: ignore  # Default low priority

        description_lower = task_description.lower()

        if "critical" in description_lower or "bug" in description_lower:
            priority_score = 1.0  # type: ignore  # Highest priority
        elif "security" in description_lower or "performance" in description_lower:
            priority_score = 1.5  # type: ignore
        elif "refactor" in description_lower or "optimize" in description_lower:
            priority_score = 2.0  # type: ignore
        elif "learn" in description_lower or "explore" in description_lower:
            priority_score = 3.0  # type: ignore
        elif "document" in description_lower or "test" in description_lower:
            priority_score = 4.0  # type: ignore

        return priority_score

    def add_self_improvement_task(self, task_description: str) -> None:
        """Adds a new self-improvement task to the agent's queue after evaluating its priority.

        Args:
            task_description: A string describing the task to be added.
        """
        priority = self._evaluate_task_priority(task_description)
        SelfImprovementPlanner._task_counter += 1
        new_task = Task(
            priority=priority,
            insertion_time=time.time(),
            task_id=SelfImprovementPlanner._task_counter,
            description=task_description,
        )
        heapq.heappush(self._task_queue, new_task)

    def get_next_task(self) -> Optional[Task]:
        """Retrieves and removes the highest-priority self-improvement task from the queue.

        Returns:
            The Task object with the highest priority, or None if the queue is empty.
        """
        if not self._task_queue:
            return None
        return heapq.heappop(self._task_queue)

    def _generate_potential_tasks(self) -> List[str]:
        """Simulates identifying potential self-improvement areas.

        Returns:
            A list of strings, each representing a potential self-improvement task.
        """
        return [
            "Refactor legacy authentication module for better security.",
            "Learn new Python asyncio patterns for concurrent programming.",
            "Fix critical bug in payment processing system.",
            "Optimize database queries for reporting dashboard performance.",
            "Document API endpoints for external developers.",
            "Explore FastAPI for building new microservices.",
            "Write unit tests for the data parsing utility.",
            "Address minor UI glitch in user profile page.",
            "Improve error handling across microservices.",
            "Research best practices for cloud deployment security.",
        ]

    def form_self_improvement_queue(self) -> None:
        """Forms the self-improvement task queue by generating potential tasks.

        and evaluating their priorities.
        """
        potential_tasks = self._generate_potential_tasks()
        for task_desc in potential_tasks:
            self.add_self_improvement_task(task_desc)

    def get_queue_size(self) -> int:
        """Returns the current number of tasks in the self-improvement queue."""
        return len(self._task_queue)

    def view_top_tasks(self, num_tasks: int = 5) -> List[Task]:
        """Returns a list of the top N highest-priority tasks without removing them from the queue."""
        # Create a temporary copy to peek without modifying the original heap
        temp_heap = list(self._task_queue)
        top_tasks: List = []
        for _ in range(min(num_tasks, len(temp_heap))):
            top_tasks.append(heapq.heappop(temp_heap))
        return top_tasks
