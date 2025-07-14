import logging
import time
from typing import TYPE_CHECKING, Dict, List, Optional

from modules.core.strategic_planner import StrategicPlanner


if TYPE_CHECKING:
    import argparse

    from dev_agent import DevAgent
    from modules.core.task_queue import TaskQueue


logger = logging.getLogger(__name__)


class AgentRunner:
    """Handles the execution loops (run, daemon) for the DevAgent."""

    def __init__(self, agent: "DevAgent") -> None:
        """Метод __init__."""
        self.agent = agent

    def run(self) -> None:
        """Runs the task execution process until the queue is empty."""
        logger.info("Starting DevAgent...")
        self.agent._create_documentation_dirs()  # This can be part of the agent's initialization logic

        if self.agent.task_queue:
            stats = self.agent.task_queue.get_stats()
            if stats["pending"] == 0 and stats["processing"] == 0:
                logger.info("No tasks in the queue. Loading from file.")
                self.agent.load_tasks()

        while True:
            processed_tasks_in_cycle: List[Dict[str, object]] = []
            while True:
                if self.agent.task_queue:
                    task = self.agent.task_queue.get_next_task()
                    if not task:
                        break

                    if task.get("type") == "self_improvement":
                        if self.agent.task_dispatcher:
                            self.agent.task_dispatcher.process_task(task)
                    else:
                        if self.agent.workflow_manager:
                            self.agent.workflow_manager.handle_feature_task(task)

                    if self.agent.task_queue:
                        updated_task = self.agent.task_queue.get_task_by_id(task["id"])
                        processed_tasks_in_cycle.append(updated_task if updated_task else task)

            processed_count = len(processed_tasks_in_cycle)
            if processed_count == 0:
                logger.info("Task queue is empty. Finishing work.")
                break
            logger.info(f"Processed {processed_count} tasks in the current cycle. Checking for new tasks...")
            if self.agent.self_improver:
                self.agent.self_improver.evaluate_and_create_followup_tasks(processed_tasks_in_cycle, self.agent)

        if self.agent.task_queue:
            stats = self.agent.task_queue.get_stats()
            logger.info(f"Total tasks processed: {stats['completed'] + stats['failed']}")
            logger.info(f"Successfully completed: {stats['completed']}")
            logger.info(f"Completed with errors: {stats['failed']}")

    def run_daemon(self, check_interval: int = 10) -> None:
        """Runs the agent in daemon mode for continuous task processing."""
        logger.info(f"Starting DevAgent in daemon mode with a check interval of {check_interval} seconds")
        self.agent._create_documentation_dirs()  # This can be part of the agent's initialization logic

        try:
            while True:
                logger.debug("Starting daemon cycle...")
                self._check_logs_for_errors_and_create_tasks()
                self.check_scheduled_tasks()

                if self.agent.pull_request_monitor:
                    pr_monitor_result = self.agent.pull_request_monitor.check_and_close_merged_prs()
                    if pr_monitor_result.get("closed_prs_count", 0) > 0:
                        logger.info(f"Closed {pr_monitor_result['closed_prs_count']} merged Pull Requests.")

                processed_tasks_in_cycle: List[Dict[str, object]] = []
                while True:
                    if self.agent.task_queue:
                        task = self.agent.task_queue.get_next_task()
                        if not task:
                            break

                        if task.get("type") == "self_improvement":
                            if self.agent.task_dispatcher:
                                self.agent.task_dispatcher.process_task(task)
                        else:
                            if self.agent.workflow_manager:
                                self.agent.workflow_manager.handle_feature_task(task)

                        if self.agent.task_queue:
                            updated_task = self.agent.task_queue.get_task_by_id(task["id"])
                            processed_tasks_in_cycle.append(updated_task if updated_task else task)

                processed_count = len(processed_tasks_in_cycle)
                if processed_count > 0:
                    logger.info(f"Processed {processed_count} tasks from the main queue.")
                    if self.agent.self_improver:
                        self.agent.self_improver.evaluate_and_create_followup_tasks(
                            processed_tasks_in_cycle,
                            self.agent,  # type: ignore
                        )
                else:
                    logger.debug(f"No active tasks. Waiting for {check_interval} seconds.")

                time.sleep(check_interval)
        except KeyboardInterrupt:  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa  # noqa
            logger.info("Received interrupt signal. Shutting down the daemon...")
        except Exception as e:
            logger.error(f"Critical error in daemon mode: {e}", exc_info=True)

    def check_scheduled_tasks(self) -> Optional[Dict[str, object]]:
        """Checks for scheduled tasks."""
        if not self.agent.improvement_scheduler:
            logger.warning("The self-improvement scheduler is not initialized")
            return None

        task = self.agent.improvement_scheduler.get_next_task()
        if not task:
            return None

        if "options" in task and self.agent.config:
            task["options"]["auto_fix"] = self.agent.config.get("auto_fix", True)

        if not self.agent.task_queue:
            logger.warning("Task queue not initialized. Cannot process scheduled task.")
            return None

        self.agent.task_queue.add_task(task)
        if self.agent.task_dispatcher:
            self.agent.task_dispatcher.process_next_task()

        task_id = task.get("id")
        for t in self.agent.task_queue.get_all_tasks():
            if t.get("id") == task_id and t.get("status") in ["completed", "failed"]:
                return {
                    "status": t.get("status"),
                    "result": t.get("result") if t.get("status") == "completed" else t.get("error"),
                }
        return None

    def analyze_logs_and_exit(self) -> None:
        """Runs a one-time scan of logs for errors, creates tasks to fix them, and then exits."""
        logger.info("Starting in log analysis mode...")
        try:
            self.agent._check_logs_for_errors_and_create_tasks()
            logger.info("Log analysis complete. Tasks to fix errors (if any) have been added to the queue.")
        except Exception as e:
            logger.error(f"Error during log analysis: {e}", exc_info=True)

    def _check_logs_for_errors_and_create_tasks(self) -> None:
        """Scans logs for errors and creates tasks to fix them."""
        # This method is complex and tightly coupled with the agent's state (output_dir, task_queue, gemini_interaction).
        # It remains on the DevAgent class for now but could be a candidate for further refactoring.
        self.agent._check_logs_for_errors_and_create_tasks()

    def run_one_task(self) -> None:
        """Runs a single task from the queue."""
        if self.agent.task_queue:
            task = self.agent.task_queue.get_next_task()
            if task:
                if task.get("type") == "self_improvement":
                    if self.agent.task_dispatcher:
                        self.agent.task_dispatcher.process_task(task)
                else:
                    if self.agent.workflow_manager:
                        self.agent.workflow_manager.handle_feature_task(task)


class ApplicationRunner:
    """Encapsulates the logic for running the agent in different modes."""

    def __init__(self, agent: "DevAgent", args: "argparse.Namespace") -> None:
        """Метод __init__."""
        self.agent = agent
        self.args = args

    def run(self) -> None:
        """Runs the application based on the selected mode."""
        if self.args.mode == "autonomous":
            self._run_autonomous_mode()
        else:
            self._run_agent_mode()

    def _run_agent_mode(self) -> None:
        """Runs the agent in standard, auto, or daemon modes."""
        if self.args.mode == "auto":
            if self.agent.workflow_manager:
                self.agent.workflow_manager.self_improve()
        elif self.args.mode == "daemon":
            if self.agent.runner:
                self.agent.runner.run_daemon(check_interval=self.args.interval)
        elif self.args.mode == "agent":
            if self.agent.runner:
                self.agent.runner.run()
        elif self.args.mode == "self-improve-direct":
            if self.agent.workflow_manager:
                self.agent.workflow_manager.self_improve(direct=True)
        elif self.args.mode == "analyze-logs":
            if self.agent.runner:
                self.agent.runner.analyze_logs_and_exit()

    def _run_autonomous_mode(self) -> None:
        """Runs the agent in a fully autonomous mode, generating its own tasks."""
        logger.info("Starting agent in autonomous mode.")
        project_path = self.agent.config_manager.get("output_dir", ".")
        strategic_planner = StrategicPlanner(project_path=project_path)

        while True:
            try:
                if self.agent.task_queue is not None and self.is_task_queue_empty(self.agent.task_queue):
                    logger.info("Task queue is empty. Engaging strategic planner...")
                    new_tasks = strategic_planner.run_self_improvement_cycle()

                    if new_tasks:
                        if self.agent.task_queue:
                            self.agent.task_queue.add_tasks(new_tasks)
                            logger.info(f"Strategic planner added {len(new_tasks)} new tasks.")
                    else:
                        logger.info("Strategic planner generated no new tasks. Shutting down.")
                        break

                if self.agent.task_queue is not None and not self.is_task_queue_empty(self.agent.task_queue):
                    logger.info("Processing next task from the queue...")
                    # Assuming run_one_task is a method on AgentRunner
                    if hasattr(self.agent.runner, "run_one_task") and self.agent.runner:
                        self.agent.runner.run_one_task()
                    else:
                        # Fallback to standard run if run_one_task is not available
                        logger.warning("'run_one_task' method not found on runner. Running standard cycle.")
                        if self.agent.runner:
                            self.agent.runner.run()

            except Exception as e:
                logger.error(f"An error occurred in the autonomous loop: {e}", exc_info=True)
                logger.info("Attempting to continue after a 60-second delay...")
                time.sleep(60)

    def is_task_queue_empty(self, task_queue: "TaskQueue") -> bool:
        """Checks if the task queue is empty.

        Args:
            task_queue (TaskQueue): The task queue to check.

        Returns:
            bool: True if the task queue is empty, False otherwise.
        """
        stats = task_queue.get_stats()
        return stats["pending"] == 0 and stats["processing"] == 0
