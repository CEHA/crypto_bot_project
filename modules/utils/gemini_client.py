"""Unified Gemini client combining all Gemini-related functionality."""

import asyncio
import json
import logging
import os
import time
from typing import Dict, List, Optional

import google.generativeai as genai
from google.generativeai.types import HarmBlockThreshold, HarmCategory


logger = logging.getLogger(__name__)


class GeminiClient:
    """Unified Gemini client with caching, stats, and async support."""

    MODELS = {
        "gemini-2.5-flash-preview-05-20": {"input": 1048576, "output": 65535},
        "gemini-2.0-flash": {"input": 1048576, "output": 8192},
        "gemini-2.0-flash-lite": {"input": 1048576, "output": 8192},
        "gemini-1.5-flash": {"input": 1048576, "output": 8192},
        "gemini-1.5-flash-8b": {"input": 1048576, "output": 8192},
    }

    def __init__(self, api_keys: Optional[List[str]] = None, models: Optional[List[str]] = None) -> None:
        """Метод __init__."""
        self.api_keys = api_keys or self._load_api_keys()
        self.models = models or list(self.MODELS.keys())
        self.current_key_index = 0
        self.current_model_index = 0
        self.cache: Dict = {}
        self.stats = {"requests": 0, "cache_hits": 0, "errors": 0}
        self.max_retries = 3
        self.initial_delay = 1
        self.max_delay = 60

        max_attempts = len(self.api_keys) * len(self.models)
        logger.info(f"GeminiClient: {len(self.api_keys)} API keys, {len(self.models)} models")
        logger.info(f"Default model: {self.models[0]}")
        logger.info(f"Max attempts: {max_attempts} ({len(self.api_keys)}×{len(self.models)})")

        self._configure_client()

    def _load_api_keys(self) -> List[str]:
        """Load API keys from environment."""
        keys_str = os.getenv("GOOGLE_API_KEY", "")
        return [key.strip() for key in keys_str.split(",") if key.strip()]

    def _configure_client(self) -> None:
        """Configure Gemini client with current API key and model."""
        if not self.api_keys:
            raise ValueError("No Gemini API keys provided")

        genai.configure(api_key=self.api_keys[self.current_key_index])

        # Configure safety settings
        safety_settings = self._get_safety_settings()
        current_model = self.models[self.current_model_index]
        self.model = genai.GenerativeModel(model_name=current_model, safety_settings=safety_settings)

    def _get_safety_settings(self) -> Dict:
        """Get safety settings from environment or use defaults."""
        settings_str = os.getenv("GEMINI_SAFETY_SETTINGS", "")
        if not settings_str:
            return {
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }

        settings = {}
        for setting in settings_str.split(";"):
            if ":" in setting:
                category, threshold = setting.split(":", 1)
                settings[getattr(HarmCategory, category)] = getattr(HarmBlockThreshold, threshold)

        return settings

    def _get_cache_key(self, prompt: str, config: Dict) -> str:
        """Generate cache key for request."""
        return f"{hash(prompt)}_{hash(json.dumps(config, sort_keys=True))}"

    def _rotate_api_key(self) -> bool:
        """Rotate to next API key."""
        if len(self.api_keys) <= 1:
            return False

        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        self._configure_client()
        logger.info(f"Rotated to API key {self.current_key_index + 1}")
        return True

    def _rotate_model(self) -> bool:
        """Rotate to next model."""
        if len(self.models) <= 1:
            return False

        self.current_model_index = (self.current_model_index + 1) % len(self.models)
        self._configure_client()
        logger.info(f"Rotated to model {self.models[self.current_model_index]}")
        return True

    def generate_content(
        self, prompt_parts: List[str], generation_config: Optional[Dict] = None, use_cache: bool = True
    ) -> Optional[str]:
        """Generate content with caching and error handling."""
        prompt = "\n".join(prompt_parts)
        config = generation_config or {}

        # Check cache
        if use_cache:
            cache_key = self._get_cache_key(prompt, config)
            if cache_key in self.cache:
                self.stats["cache_hits"] += 1
                return self.cache[cache_key]

        self.stats["requests"] += 1

        # Try with current API key and model combinations
        max_attempts = len(self.api_keys) * len(self.models)
        for _attempt in range(max_attempts):
            try:
                response = self.model.generate_content(prompt, generation_config=config)

                if response.text:
                    if use_cache:
                        self.cache[cache_key] = response.text
                    return response.text

            except Exception as e:
                logger.warning(
                    f"API key {self.current_key_index + 1}, model {self.models[self.current_model_index]} failed: {e}"
                )
                self.stats["errors"] += 1

                # Try rotating model first, then API key
                if not self._rotate_model() and not self._rotate_api_key():
                    break

                time.sleep(1)  # Brief delay before retry

        logger.error("All API keys failed")
        return None

    async def generate_content_async(
        self, prompt_parts: List[str], generation_config: Optional[Dict] = None, use_cache: bool = True
    ) -> Optional[str]:
        """Async version of generate_content."""
        # Run sync version in thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.generate_content, prompt_parts, generation_config, use_cache)

    def get_stats(self) -> Dict:
        """Get usage statistics."""
        return {
            **self.stats,
            "cache_size": len(self.cache),
            "current_key": self.current_key_index + 1,
            "total_keys": len(self.api_keys),
            "current_model": self.models[self.current_model_index],
            "total_models": len(self.models),
        }

    def clear_cache(self) -> None:
        """Clear the cache."""
        self.cache.clear()
        logger.info("Cache cleared")


# Backward compatibility aliases
GeminiInteraction = GeminiClient
AsyncGeminiInteraction = GeminiClient
GeminiCache = GeminiClient
GeminiStats = GeminiClient
