"""Утилітарні модулі."""

from .code_fixer import fix_file_automatically, fix_project_files
from .config_manager import ConfigManager
from .diff_applier import DiffApplier
from .error_memory import ErrorMemory
from .gemini_client import GeminiClient as GeminiCache, GeminiClient as GeminiInteraction, GeminiClient as GeminiStats
from .git_module import GitModule
from .integration import patch_dev_agent_class as integration_patch
from .json_analyzer import JsonAnalyzer
from .local_tools import patch_dev_agent_class


__all__ = [
    "JsonAnalyzer",
    "GeminiInteraction",
    "GeminiCache",
    "GeminiStats",
    "ConfigManager",
    "ErrorMemory",
    "GitModule",
    "patch_dev_agent_class",
    "integration_patch",
    "DiffApplier",
    "fix_file_automatically",
    "fix_project_files",
]
