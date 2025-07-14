import json
import logging
import os
import sys
from typing import TYPE_CHECKING, Dict, List, Optional, Union

from dotenv import load_dotenv

from modules.utils.gemini_client import GeminiClient as GeminiInteraction


try:
    import jsonschema
except ImportError:  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa  # noqa
    jsonschema = None

from modules.core.module_registry import ModuleRegistry
from modules.core.task_dispatcher import TaskDispatcher
from modules.core.task_queue import TaskQueue
from modules.self_improvement.pull_request_monitor import PullRequestMonitor
from modules.utils.config_manager import ConfigManager
from modules.utils.gemini_stats import GeminiStatsCollector
from modules.utils.json_analyzer import JsonAnalyzer


if TYPE_CHECKING:
    import argparse

    from dev_agent import DevAgent

logger = logging.getLogger(__name__)

# Визначаємо корінь проекту відносно поточного файлу
_AGENT_INITIALIZER_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(_AGENT_INITIALIZER_DIR, "..", ".."))


class AgentInitializer:
    """Handles the complex initialization process of the DevAgent."""

    def __init__(self, args: "argparse.Namespace", current_log_file: str) -> None:
        """Initializes the environment and prepares for agent setup.

        This includes loading configuration, checking API keys, and resolving paths.
        """
        load_dotenv()
        self._check_api_keys()

        self.config_manager = self._initialize_config_manager(args)
        self.output_dir = self._resolve_path(args.output, "output_dir", ".")
        self.tasks_file = self._resolve_path(args.tasks, "tasks_file", "tasks.json")
        self.queue_file = os.path.join(self.output_dir, "task_queue.json")
        self.current_log_file = current_log_file
        self.agent: Optional["DevAgent"] = None  # Will hold the agent instance being built

        logger.info(f"Using config file: {self.config_manager.config_file}")
        logger.info(f"Using output directory: {self.output_dir}")
        logger.info(f"Using tasks file: {self.tasks_file}")
        logger.info(f"Using task queue file: {self.queue_file}")

    def _check_api_keys(self) -> None:
        """Checks for the presence of GOOGLE_API_KEY in the environment."""
        api_keys_str = os.getenv("GOOGLE_API_KEY")
        if not api_keys_str:
            logger.error("GOOGLE_API_KEY environment variable not found.")
            sys.exit(1)
        api_keys = [key.strip() for key in api_keys_str.split(",") if key.strip()]
        logger.info(f"Found {len(api_keys)} Gemini API key(s).")

    def _initialize_config_manager(self, args: "argparse.Namespace") -> ConfigManager:
        """Initializes the ConfigManager based on command-line arguments."""
        config_path = args.config  # type: ignore
        if not os.path.isabs(config_path):
            config_path = os.path.join(PROJECT_ROOT, config_path)
        return ConfigManager(config_file=os.path.abspath(config_path))

    def _resolve_path(self, arg_path: str, config_key: str, default: str) -> str:
        """Resolves a path, giving priority to command-line arguments,.

        then the config file, and finally a default value.
        """
        path = arg_path if arg_path != default else self.config_manager.get(config_key, default)
        if not os.path.isabs(path):
            path = os.path.join(PROJECT_ROOT, path)
        return path

    def setup_agent(self) -> "DevAgent":
        """Orchestrates the entire setup process for the agent."""
        from dev_agent import DevAgent

        self.agent = DevAgent(
            config_manager=self.config_manager,
            output_dir=self.output_dir,
            tasks_file=self.tasks_file,
            queue_file=self.queue_file,
            current_log_file=self.current_log_file,
        )

        self.agent.module_setup = self._load_module_setup()
        self._setup_core_services()
        self._setup_task_management()
        self._requeue_stuck_tasks()
        self._setup_module_registry()

        self.agent.config = self.config_manager.config  # type: ignore
        self._apply_config()

        self._initialize_agent_modules()
        self._init_scheduler()

        self.agent.finalize_setup()

        logger.info("DevAgent fully initialized by AgentInitializer.")
        return self.agent  # type: ignore

    def _load_module_setup(self) -> List[Dict[str, object]]:
        """Loads and validates the module initialization configuration from a JSON file."""
        if jsonschema is None:
            logger.warning(
                "The 'jsonschema' library was not found. Skipping validation of module_setup.json. "
                "To enable validation, install it: pip install jsonschema"
            )

        setup_file_path = os.path.join(self.output_dir, "module_setup.json")
        schema_file_path = os.path.join(self.output_dir, "schemas", "module_setup_schema.json")

        try:
            with open(setup_file_path, "r", encoding="utf-8") as f:
                logger.info(f"Loading module configuration from {setup_file_path}")
                config_data: List[Dict[str, object]] = json.load(f)
        except FileNotFoundError:  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa  # noqa
            logger.error(f"Module configuration file not found: {setup_file_path}. Initialization is not possible.")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"JSON decoding error in module configuration file {setup_file_path}: {e}")
            raise

        if jsonschema:
            try:
                with open(schema_file_path, "r", encoding="utf-8") as f:
                    schema = json.load(f)
                jsonschema.validate(instance=config_data, schema=schema)
                logger.info("Module configuration successfully validated against the schema.")
            except FileNotFoundError:  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa  # noqa
                logger.error(f"Schema file not found: {schema_file_path}. Validation is not possible.")
                raise
            except jsonschema.ValidationError as e:
                logger.error(
                    f"Validation error for file {setup_file_path} against schema {schema_file_path}: {e.message}"
                )
                raise

        return config_data

    def _requeue_stuck_tasks(self) -> None:
        """Finds tasks that are 'stuck' in 'processing' status and returns them to the queue."""
        if self.agent and self.agent.task_queue:
            requeued_count = self.agent.task_queue.requeue_processing_tasks()
            if requeued_count > 0:
                logger.info(f"Returned {requeued_count} 'processing' tasks to 'pending' status.")

    def _setup_core_services(self) -> None:
        """Initializes basic services like JsonAnalyzer and GeminiInteraction."""
        logger.debug("Initializing basic services...")
        if self.agent:
            self.agent.gemini_stats_collector = GeminiStatsCollector(output_dir=self.output_dir)
            self.agent.json_analyzer = JsonAnalyzer()
            self.agent.gemini_interaction = GeminiInteraction()

            try:
                from modules.utils.gemini_cache import patch_gemini_interaction

                patch_gemini_interaction(self.agent.gemini_interaction)
                logger.info("GeminiInteraction successfully patched for caching")
            except ImportError:  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa  # noqa
                logger.warning("gemini_cache module not found")

            setup_agent_core = getattr(self.agent, "setup_agent_core", None)
            if setup_agent_core:
                setup_agent_core(self.agent.gemini_interaction, self.agent.json_analyzer)

    def _setup_task_management(self) -> None:
        """Initializes the task management system (TaskQueue and TaskDispatcher)."""
        logger.debug("Initializing task management system...")
        if self.agent:
            self.agent.task_queue = TaskQueue(self.queue_file)
            assert self.agent.task_queue is not None, "TaskQueue should be initialized here"
            self.agent.task_dispatcher = TaskDispatcher(agent=self.agent, task_queue=self.agent.task_queue)

    def _setup_module_registry(self) -> None:
        """Initializes the module registry and registers basic/core modules."""
        logger.debug("Initializing module registry...")
        if (
            self.agent  # type: ignore
            and self.agent.json_analyzer  # type: ignore
            and self.agent.gemini_interaction  # type: ignore
            and self.agent.task_queue  # type: ignore
            and self.agent.task_dispatcher  # type: ignore
        ):
            self.agent.registry = ModuleRegistry()
            if self.agent.registry:
                self.agent.registry.register("json_analyzer", JsonAnalyzer)
                self.agent.registry.register("gemini_interaction", GeminiInteraction)
                self.agent.registry.load_core_modules()
                self.agent.registry.instances["json_analyzer"] = self.agent.json_analyzer  # type: ignore
                self.agent.registry.instances["gemini_interaction"] = self.agent.gemini_interaction  # type: ignore
                self.agent.registry.instances["task_queue"] = self.agent.task_queue  # type: ignore
                self.agent.registry.instances["task_dispatcher"] = self.agent.task_dispatcher  # type: ignore

    def _initialize_agent_modules(self) -> None:
        """Initializes all functional modules based on declarative setup."""
        logger.debug("Initializing agent modules from declarative setup...")
        try:
            from modules.self_improvement.code_fixer import CodeFixer
            from modules.self_improvement.documentation_updater import DocumentationUpdater
            from modules.self_improvement.self_analyzer import SelfAnalyzer
            from modules.self_improvement.self_improver import SelfImprover

            modules_to_register = [
                ("self_analyzer", SelfAnalyzer),
                ("self_improver", SelfImprover),
                ("documentation_updater", DocumentationUpdater),
                ("code_fixer", CodeFixer),
            ]
            if self.agent and self.agent.registry:
                for name, cls in modules_to_register:
                    if name not in self.agent.registry.modules:
                        self.agent.registry.register(name, cls)
        except ImportError as e:
            logger.warning(f"Could not register self-improvement modules: {e}")

        if self.agent and self.agent.module_setup:
            for module_config in self.agent.module_setup:
                module_name = module_config.get("name")
                attr_name = module_config.get("attr")
                deps = {
                    "gemini_interaction": self.agent.gemini_interaction,
                    "output_dir": self.output_dir,
                    "json_analyzer": self.agent.json_analyzer,
                }
                if "deps" in module_config and isinstance(module_config.get("deps"), dict):
                    for param_name, agent_attr in module_config["deps"].items():
                        if hasattr(self.agent, agent_attr):
                            deps[param_name] = getattr(self.agent, agent_attr)
                        else:
                            logger.warning(f"Dependency '{agent_attr}' not found in agent for module '{module_name}'.")
                if module_name == "code_fixer":
                    deps.update(
                        {
                            "github_token": os.getenv("GITHUB_TOKEN"),
                            "repo_owner": os.getenv("GITHUB_REPO_OWNER"),
                            "repo_name": os.getenv("GITHUB_REPO_NAME"),
                        }
                    )
                if self.agent.registry and module_name and attr_name:
                    instance = self.agent.registry.create(module_name, **deps)
                    if instance:
                        setattr(self.agent, attr_name, instance)
                    else:
                        logger.error(f"Could not create module '{module_name}'. It will be unavailable.")

        if self.agent and self.agent.task_queue:
            code_fixer_instance = getattr(self.agent, "code_fixer", None)
            if code_fixer_instance and hasattr(code_fixer_instance, "git_module"):
                self.agent.pull_request_monitor = PullRequestMonitor(
                    git_module=code_fixer_instance.git_module,
                    task_queue=self.agent.task_queue,
                    output_dir=self.output_dir,
                )
                self_improver_instance = getattr(self.agent, "self_improver", None)
                if self_improver_instance:
                    self_improver_instance.pull_request_monitor = self.agent.pull_request_monitor  # type: ignore
                logger.info("PullRequestMonitor initialized and connected.")
            else:
                logger.warning("GitModule or CodeFixer not initialized, PullRequestMonitor will not be available.")
        logger.info("Agent module initialization complete.")

    def _init_scheduler(self) -> None:
        """Initializes the self-improvement scheduler."""
        logger.debug("Initializing self-improvement scheduler...")
        try:
            from modules.self_improvement.improvement_scheduler import ImprovementScheduler

            if self.agent and self.agent.registry:
                self.agent.registry.register("improvement_scheduler", ImprovementScheduler)
                instance = self.agent.registry.create("improvement_scheduler", output_dir=self.output_dir)
                if instance:
                    self.agent.improvement_scheduler = instance
                    self.agent.registry.instances["improvement_scheduler"] = self.agent.improvement_scheduler  # type: ignore
                    logger.info("Self-improvement scheduler successfully initialized.")
                else:
                    logger.error(
                        "self.registry.create('improvement_scheduler', ...) returned None. Scheduler not initialized."
                    )
        except Exception as e:
            logger.error(f"Exception during scheduler initialization: {e}", exc_info=True)

    def _apply_config(self) -> None:
        """Applies parameters from the configuration."""
        logger.debug("Applying configuration parameters...")
        if self.agent and self.agent.gemini_interaction and self.agent.config:
            self.agent.gemini_interaction.max_retries = self.agent.config.get(
                "max_retries",
                self.agent.gemini_interaction.max_retries,  # type: ignore
            )
            self.agent.gemini_interaction.initial_delay = self.agent.config.get(
                "initial_delay",
                self.agent.gemini_interaction.initial_delay,  # type: ignore
            )
            model_params = self.agent.config.get("model_parameters")
            if isinstance(model_params, dict):
                temperature: Optional[Union[int, float]] = model_params.get("temperature")
                max_output_tokens: Optional[int] = model_params.get("max_output_tokens")
                if temperature is not None and isinstance(temperature, (int, float)):
                    self.agent.gemini_interaction.generation_config.temperature = temperature
                if max_output_tokens is not None and isinstance(max_output_tokens, int):
                    self.agent.gemini_interaction.generation_config.max_output_tokens = max_output_tokens
        if self.agent and self.agent.json_analyzer and self.agent.config:
            self.agent.json_analyzer.max_repair_attempts = self.agent.config.get("max_repair_attempts", 3)
        logger.info("Configuration parameters applied.")
