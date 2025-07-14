"""Модуль для запам'ятовування та аналізу помилок."""

import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional


logger = logging.getLogger(__name__)


class ErrorMemory:
    """Система запам'ятовування помилок для покращення виправлень."""

    def __init__(self, memory_file: str = "error_memory.json") -> None:
        """Метод __init__."""
        self.memory_file = memory_file
        self.errors = self._load_memory()

    def _load_memory(self) -> Dict[str, object]:
        """Завантажує історію помилок з файлу."""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Помилка завантаження пам'яті помилок: {e}")
        return {"patterns": {}, "fixes": {}, "stats": {"total": 0, "fixed": 0}}

    def _save_memory(self) -> None:
        """Зберігає історію помилок у файл."""
        try:
            with open(self.memory_file, "w", encoding="utf-8") as f:
                json.dump(self.errors, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Помилка збереження пам'яті помилок: {e}")

    def record_error(
        self, error_type: str, file_path: str, error_msg: str, fix_attempted: bool = False, fix_successful: bool = False
    ) -> None:
        """Записує помилку в пам'ять."""
        error_key = f"{error_type}:{hash(error_msg) % 10000}"

        if error_key not in self.errors["patterns"]:
            self.errors["patterns"][error_key] = {
                "type": error_type,
                "message": error_msg,
                "occurrences": [],
                "fixes": [],
                "success_rate": 0.0,
            }

        # Додаємо нове входження
        self.errors["patterns"][error_key]["occurrences"].append(
            {
                "file": file_path,
                "timestamp": datetime.now().isoformat(),
                "fix_attempted": fix_attempted,
                "fix_successful": fix_successful,
            }
        )

        # Оновлюємо статистику
        self.errors["stats"]["total"] += 1
        if fix_successful:
            self.errors["stats"]["fixed"] += 1

        self._update_success_rate(error_key)
        self._save_memory()

    def record_fix(self, error_type: str, error_msg: str, fix_strategy: str, fix_code: str, success: bool) -> None:
        """Записує успішне виправлення."""
        error_key = f"{error_type}:{hash(error_msg) % 10000}"

        if error_key in self.errors["patterns"]:
            self.errors["patterns"][error_key]["fixes"].append(
                {
                    "strategy": fix_strategy,
                    "code": fix_code,
                    "success": success,
                    "timestamp": datetime.now().isoformat(),
                }
            )
            self._update_success_rate(error_key)
            self._save_memory()

    def _update_success_rate(self, error_key: str) -> None:
        """Оновлює коефіцієнт успішності для типу помилки."""
        pattern = self.errors["patterns"][error_key]
        total_attempts = len([o for o in pattern["occurrences"] if o["fix_attempted"]])
        successful_fixes = len([o for o in pattern["occurrences"] if o["fix_successful"]])

        if total_attempts > 0:
            pattern["success_rate"] = successful_fixes / total_attempts

    def get_similar_fixes(self, error_type: str, error_msg: str) -> List[Dict]:
        """Повертає схожі успішні виправлення."""
        similar_fixes: List = []

        for _pattern_key, pattern in self.errors["patterns"].items():
            if pattern["type"] == error_type and pattern["success_rate"] > 0.5:
                # Перевіряємо схожість повідомлень
                similarity = self._calculate_similarity(error_msg, pattern["message"])
                if similarity > 0.7:
                    successful_fixes = [f for f in pattern["fixes"] if f["success"]]
                    for fix in successful_fixes:
                        similar_fixes.append(
                            {
                                "similarity": similarity,
                                "strategy": fix["strategy"],
                                "code": fix["code"],
                                "success_rate": pattern["success_rate"],
                            }
                        )

        return sorted(similar_fixes, key=lambda x: x["similarity"], reverse=True)

    def _calculate_similarity(self, msg1: str, msg2: str) -> float:
        """Обчислює схожість між повідомленнями помилок."""
        words1 = set(msg1.lower().split())
        words2 = set(msg2.lower().split())

        if not words1 or not words2:
            return 0.0  # type: ignore

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union)

    def get_stats(self) -> Dict[str, object]:
        """Повертає статистику помилок."""
        stats = self.errors["stats"].copy()
        stats["success_rate"] = stats["fixed"] / stats["total"] if stats["total"] > 0 else 0.0  # type: ignore
        stats["patterns_count"] = len(self.errors["patterns"])

        # Топ помилок
        top_errors = sorted(self.errors["patterns"].items(), key=lambda x: len(x[1]["occurrences"]), reverse=True)[:5]

        stats["top_errors"] = [
            {
                "type": pattern["type"],
                "message": pattern["message"][:100],
                "count": len(pattern["occurrences"]),
                "success_rate": pattern["success_rate"],
            }
            for _, pattern in top_errors
        ]

        return stats

    def suggest_fix_strategy(self, error_type: str, error_msg: str) -> Optional[str]:
        """Пропонує стратегію виправлення на основі історії."""
        similar_fixes = self.get_similar_fixes(error_type, error_msg)

        if similar_fixes:
            best_fix = similar_fixes[0]
            return f"Рекомендована стратегія: {best_fix['strategy']} (успішність: {best_fix['success_rate']:.1%})"

        return None
