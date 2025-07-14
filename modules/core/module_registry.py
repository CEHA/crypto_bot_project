"""Модуль реєстрації та управління модулями системи."""

import importlib
import logging
from typing import Callable, Dict, Optional, Type


# Налаштування логування
logger = logging.getLogger(__name__)


class ModuleRegistry:
    """Клас для реєстрації та управління модулями системи."""

    _instance = None

    def __new__(cls) -> None:
        """Реалізація патерну Singleton."""
        if cls._instance is None:
            cls._instance = super(ModuleRegistry, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance  # type: ignore

    def __init__(self) -> None:
        """Ініціалізує реєстр модулів."""
        if self._initialized:
            return

        self.modules: Dict[str, Type] = {}
        self.instances: Dict[str, object] = {}
        self._initialized = True
        logger.info("ModuleRegistry ініціалізовано")

    def register(self, name: str, module_class: Type) -> bool:
        """Реєструє модуль у системі.

        Args:
            name: Назва модуля
            module_class: Клас модуля

        Returns:
            True, якщо модуль успішно зареєстровано, False - інакше
        """
        if name in self.modules:
            logger.warning(f"Модуль '{name}' вже зареєстровано")
            return False

        self.modules[name] = module_class
        logger.info(f"Модуль '{name}' зареєстровано")
        return True

    def get(self, name: str) -> Optional[Type]:
        """Повертає клас модуля за назвою.

        Args:
            name: Назва модуля

        Returns:
            Клас модуля або None, якщо модуль не знайдено
        """
        if name not in self.modules:
            logger.warning(f"Модуль '{name}' не знайдено")
            return None

        return self.modules[name]

    def load(self, name: str, module_path: str, class_name: str) -> bool:
        """Завантажує модуль з вказаного шляху та реєструє його.

        Args:
            name: Назва модуля
            module_path: Шлях до модуля
            class_name: Назва класу модуля

        Returns:
            True, якщо модуль успішно завантажено та зареєстровано, False - інакше
        """
        # Перевіряємо, чи модуль вже зареєстровано
        if name in self.modules:
            logger.info(f"Модуль '{name}' вже зареєстровано")
            return True

        try:
            module = importlib.import_module(module_path)
            module_class = getattr(module, class_name)
            return self.register(name, module_class)
        except ImportError:  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007
            logger.error(f"Не вдалося імпортувати модуль '{module_path}'", exc_info=True)
            return False
        except AttributeError:  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007
            logger.error(f"Не вдалося знайти клас '{class_name}' у модулі '{module_path}'", exc_info=True)
            return False

    def create(self, name: str, *args: object, **kwargs) -> Optional[object]:
        """Створює екземпляр модуля за назвою.

        Args:
            name: Назва модуля
            *args: Позиційні аргументи для конструктора модуля
            **kwargs: Іменовані аргументи для конструктора модуля

        Returns:
            Екземпляр модуля або None, якщо модуль не знайдено
        """
        module_class = self.get(name)
        if not module_class:
            return None

        try:
            instance = module_class(*args, **kwargs)
            # Зберігаємо екземпляр, якщо він успішно створений
            self.instances[name] = instance
            logger.info(f"Створено екземпляр модуля '{name}'")
            return instance
        except Exception as e:
            logger.error(f"Помилка при створенні екземпляра модуля '{name}': {e}", exc_info=True)
            return None

    def get_instance(self, name: str) -> Optional[object]:
        """Повертає екземпляр модуля за назвою.

        Args:
            name: Назва модуля

        Returns:
            Екземпляр модуля або None, якщо модуль не знайдено
        """
        if name not in self.instances:
            logger.warning(f"Екземпляр модуля '{name}' не знайдено")
            return None

        return self.instances[name]

    def load_core_modules(self) -> bool:
        """Завантажує основні модулі системи.

        Returns:
            True, якщо всі модулі успішно завантажено, False - інакше
        """
        modules_to_load = [
            ("task_queue", "modules.core.task_queue", "TaskQueue"),
            ("task_dispatcher", "modules.core.task_dispatcher", "TaskDispatcher"),
            ("code_generation", "modules.refactoring.code_generation_module", "CodeGenerationModule"),
            ("refactoring_executor", "modules.refactoring.refactoring_executor", "RefactoringExecutor"),
            ("project_analyzer", "modules.analysis.project_analyzer", "ProjectAnalyzer"),
            ("dependency_analyzer", "modules.analysis.dependency_analyzer", "DependencyAnalyzer"),
            ("test_integration", "modules.testing.test_integration", "TestIntegrationModule"),
            ("planning", "modules.planning.planning_module", "PlanningModule"),
            ("code_reviewer", "modules.review.code_reviewer", "CodeReviewer"),
            # Додайте сюди інші основні модулі, якщо потрібно
        ]

        success = True
        for module_name, module_path, class_name in modules_to_load:
            if not self.load(module_name, module_path, class_name):
                success = False

        return success

    def register_decorator(self, name: str) -> Callable:
        """Повертає декоратор для реєстрації класу як модуля.

        Args:
            name: Назва модуля

        Returns:
            Декоратор для реєстрації класу
        """

        def decorator(cls) -> Type:
            """Метод decorator."""
            self.register(name, cls)
            return cls

        return decorator
