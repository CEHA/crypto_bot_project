"""Модуль управління конфігурацією для Meta-Agent."""

import json
import logging
import os
from typing import Dict, Optional


# Налаштування логування
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [ConfigManager] - %(message)s') # Використовуємо глобальну конфігурацію
logger = logging.getLogger(__name__)


class ConfigManager:
    """Клас для управління конфігурацією."""

    def __init__(self, config_file: str = "dev_agent_config.json") -> None:
        """Метод __init__."""
        self.config_file = config_file
        self.config = self._load_config()
        logger.info(f"ConfigManager ініціалізовано з файлу {config_file}")

    def _load_config(self) -> Dict[str, object]:
        """Завантажує конфігурацію з файлу."""
        default_config = {
            "model_parameters": {"temperature": 0.7, "max_output_tokens": 8192},
            "max_retries": 5,
            "initial_delay": 2,
            "max_delay": 10,
            "post_call_delay": 1.5,
            "max_repair_attempts": 3,
        }

        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    loaded_config = json.load(f)
                if isinstance(loaded_config, dict):
                    default_config.update(loaded_config)
                    logger.info(f"Конфігурацію завантажено з {self.config_file}")
            except Exception as e:
                logger.error(f"Помилка завантаження конфігурації: {e}")

        return default_config

    def save_config(self) -> None:
        """Зберігає конфігурацію у файл."""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logger.info(f"Конфігурацію збережено у {self.config_file}")
        except Exception as e:
            logger.error(f"Помилка збереження конфігурації: {e}")

    def get(self, key: str, default: Optional[object] = None) -> object:
        """Отримує значення параметра конфігурації."""
        # Підтримка вкладених ключів через крапку (наприклад, "model_parameters.temperature")
        if "." in key:
            parts = key.split(".")
            value = self.config  # type: ignore
            for part in parts:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    return default
            return value

        return self.config.get(key, default)

    def set(self, key: str, value: object) -> None:
        """Встановлює значення параметра конфігурації."""
        # Підтримка вкладених ключів через крапку
        if "." in key:
            parts = key.split(".")
            config = self.config  # type: ignore
            for part in parts[:-1]:
                if part not in config:
                    config[part] = {}
                config = config[part]
            config[parts[-1]] = value
        else:
            self.config[key] = value

    def update(self, config: Dict[str, object]) -> None:
        """Оновлює конфігурацію."""
        self.config.update(config)

    def get_model_params(self) -> Dict[str, object]:
        """Отримує параметри моделі."""
        return self.config.get("model_parameters", {})
