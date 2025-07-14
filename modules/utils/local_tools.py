"""Локальні інструменти для розширення функціональності системи."""

import importlib
import logging
from typing import Type


# Налаштування логування
logger = logging.getLogger(__name__)


def patch_dev_agent_class() -> object:
    """Повертає функцію для патчу класу DevAgent.

    Використовується для додавання додаткової функціональності до DevAgent.
    """

    def patch(dev_agent_class: Type) -> Type:
        """Патчить клас DevAgent додатковою функціональністю.

        Args:
            dev_agent_class: Клас DevAgent для патчу

        Returns:
            Патчений клас DevAgent
        """
        logger.info(f"Патчимо клас {dev_agent_class.__name__}")

        # Зберігаємо оригінальний метод run
        original_run = dev_agent_class.run  # type: ignore

        # Створюємо новий метод run з додатковою функціональністю
        def patched_run(self, *args: object, **kwargs) -> None:
            """Метод patched_run."""
            logger.info("Запуск патченого методу run")

            # Додаткова функціональність перед запуском
            try:
                # Імпортуємо додаткові модулі
                importlib.import_module("modules.utils.error_memory")
                importlib.import_module("modules.utils.error_fixer")
                logger.info("Додаткові модулі успішно імпортовано")
            except ImportError as e:
                logger.warning(f"Не вдалося імпортувати додаткові модулі: {e}")

            # Викликаємо оригінальний метод
            result = original_run(self, *args, **kwargs)  # type: ignore

            # Додаткова функціональність після запуску
            logger.info("Патчений метод run завершено")

            return result

        # Замінюємо оригінальний метод на патчений
        dev_agent_class.run = patched_run

        return dev_agent_class

    return patch
