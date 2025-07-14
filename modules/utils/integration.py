"""Модуль інтеграції з зовнішніми системами."""

import logging
from typing import Type


# Налаштування логування
logger = logging.getLogger(__name__)


def patch_dev_agent_class() -> object:
    """Повертає функцію для патчу класу DevAgent.

    Використовується для інтеграції з зовнішніми системами.
    """

    def patch(dev_agent_class: Type) -> Type:
        """Патчить клас DevAgent для інтеграції з зовнішніми системами.

        Args:
            dev_agent_class: Клас DevAgent для патчу

        Returns:
            Патчений клас DevAgent
        """
        logger.info(f"Інтегруємо клас {dev_agent_class.__name__} з зовнішніми системами")

        # Зберігаємо оригінальний метод __init__
        original_init = dev_agent_class.__init__  # type: ignore

        # Створюємо новий метод __init__ з додатковою функціональністю
        def patched_init(self, *args: object, **kwargs) -> None:
            """Метод patched_init."""
            # Викликаємо оригінальний метод
            original_init(self, *args, **kwargs)

            # Додаткова функціональність після ініціалізації
            try:
                # Імпортуємо зовнішні системи
                from modules.utils.git_module import GitModule

                # Ініціалізуємо зовнішні системи
                self.git_module = GitModule()
                logger.info("Зовнішні системи успішно ініціалізовано")
            except ImportError as e:
                logger.warning(f"Не вдалося імпортувати зовнішні системи: {e}")

        # Замінюємо оригінальний метод на патчений
        dev_agent_class.__init__ = patched_init

        return dev_agent_class

    return patch
