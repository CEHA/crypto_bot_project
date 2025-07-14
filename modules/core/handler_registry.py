import logging
from typing import Callable, Dict


logger = logging.getLogger(__name__)

# Global registry for task handlers
_handler_registry: Dict[str, Callable[..., object]] = {}


def register_handler(task_type: str) -> Callable:
    """A decorator to register a function as a handler for a specific task type.

    Args:
        task_type (str): The type of the task (e.g., 'code_generation', 'refactoring').

    Returns:
        Callable: The decorator function.
    """

    def decorator(func: Callable[..., object]) -> Callable[..., object]:
        """Метод decorator."""
        if task_type in _handler_registry:
            logger.warning(f"Handler for task type '{task_type}' is being overridden by function {func.__name__}.")
        _handler_registry[task_type] = func
        logger.debug(f"Task handler for '{task_type}' registered to function {func.__name__}.")
        return func

    return decorator


def get_handler(task_type: str) -> Callable[..., object]:
    """Retrieves a handler for a given task type from the registry.

    Args:
        task_type (str): The type of the task.

    Returns:
        Callable: The registered handler function.

    Raises:
        KeyError: If no handler is registered for the given task type.
    """
    if task_type not in _handler_registry:
        raise KeyError(
            f"No handler registered for task type '{task_type}'. Available handlers: {list(_handler_registry.keys())}"
        )
    return _handler_registry[task_type]


def get_registry() -> Dict[str, Callable[..., object]]:
    """Returns a copy of the entire handler registry."""
    return _handler_registry.copy()
