import logging
from typing import Optional


try:
    import patch

    PATCH_LIB_AVAILABLE = True
except ImportError:  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa  # noqa
    patch = None
# Налаштування логування
logger = logging.getLogger(__name__)

if not PATCH_LIB_AVAILABLE:
    logger.warning(
        "Бібліотека 'patch' не встановлена. "
        "Автоматичне застосування diff-ів буде недоступним. "
        "Будь ласка, встановіть її: pip install patch"
    )


class DiffApplier:
    """Клас для застосування diff-ів до текстового контенту."""

    @staticmethod
    def apply_diff(original_content: str, diff_text: str) -> Optional[str]:
        """Застосовує diff у форматі unified до оригінального контенту за допомогою бібліотеки 'patch'.

        Args:
            original_content: Оригінальний рядковий контент.
            diff_text: Рядок diff у форматі unified.

        Returns:
            Змінений рядок, якщо застосування успішне, інакше None.
        """
        if not PATCH_LIB_AVAILABLE:
            logger.error("Спроба застосувати diff, але бібліотека 'patch' не доступна.")
            return None

        if not diff_text.strip():
            logger.info("Отримано порожній diff текст. Повертаємо оригінальний контент.")
            return original_content

        try:
            patch_set = patch.fromstring(diff_text.encode("utf-8"))
            patched_bytes = patch_set.apply(original_content.encode("utf-8"))

            if patched_bytes is False:
                logger.error("Не вдалося застосувати diff. patch.apply() повернув False.")
                return None

            logger.info("Diff успішно застосовано.")
            return patched_bytes.decode("utf-8")
        except Exception as e:
            logger.error(f"Виняток під час застосування diff: {e}", exc_info=True)
            return None
