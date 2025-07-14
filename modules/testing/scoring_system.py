import logging
from typing import Dict, List, Tuple


"""
Модуль системи оцінювання для Meta-Agent.
"""
# Налаштування логування
logger = logging.getLogger(__name__)


class ScoringSystem:
    """Клас для оцінювання якості коду та проекту."""

    def __init__(self, output_dir: str, gemini_interaction=None) -> None:
        """Ініціалізує ScoringSystem.

        Args:
            output_dir (str): Коренева директорія проекту.
            gemini_interaction: Екземпляр GeminiInteraction для взаємодії з Gemini API (опціонально).
        """
        self.output_dir = output_dir
        self.gemini_interaction = gemini_interaction
        logger.info("ScoringSystem ініціалізовано")

    def evaluate_project_progress(
        self,
        project_state: Dict[str, str],
        current_plan: Dict[str, object] = None,
        dependency_report: Dict[str, object] = None,
    ) -> Tuple[float, Dict[str, object]]:
        """Оцінює прогрес проекту на основі різних метрик.

        Включає підрахунок файлів, рядків коду, оцінку виконання плану,
        якості коду та архітектури, а також виявлення проблем.

        Args:
            project_state (Dict[str, str]): Словник, що представляє стан проекту
                                            (шлях до файлу: вміст файлу).
            current_plan (Dict[str, object], optional): Поточний план розвитку проекту.
            dependency_report (Dict[str, object], optional): Звіт про залежності проекту.

        Returns:
            Tuple[float, Dict[str, object]]: Кортеж, що містить загальний бал (від 0 до 1)
                                          та детальний звіт про оцінку.
        """
        logger.info("Оцінка прогресу проекту")

        # Базові метрики # Corrected reference to project_state
        metrics = {
            "files_count": len(project_state),
            "code_lines": 0,
            "comment_lines": 0,
            "empty_lines": 0,
            "py_files_count": 0,
            "py_code_lines": 0,
        }

        # Підраховуємо рядки коду
        for file_path, content in project_state.items():
            if file_path.startswith("SELF/"):
                continue  # Пропускаємо файли агента

            lines = content.split("\n")
            metrics["code_lines"] += len(lines)

            # Підраховуємо коментарі та порожні рядки
            for line in lines:
                line = line.strip()
                if not line:
                    metrics["empty_lines"] += 1
                elif line.startswith("#"):
                    metrics["comment_lines"] += 1

            # Підраховуємо Python-файли
            if file_path.endswith(".py"):
                metrics["py_files_count"] += 1
                metrics["py_code_lines"] += len(lines)

        # Оцінка виконання плану
        plan_score = self._evaluate_plan_completion(current_plan) if current_plan else 0.0  # type: ignore

        # Оцінка якості коду
        code_quality_score = self._evaluate_code_quality(project_state)

        # Оцінка архітектури
        architecture_score = self._evaluate_architecture(dependency_report) if dependency_report else 0.0  # type: ignore

        # Загальна оцінка
        overall_score = (plan_score + code_quality_score + architecture_score) / 3

        # Виявлені проблеми
        problems = self._identify_problems(project_state, current_plan, dependency_report)

        # Формуємо звіт
        report = {
            "metrics": metrics,
            "scores": {
                "plan_completion": plan_score,
                "code_quality": code_quality_score,
                "architecture": architecture_score,
                "overall": overall_score,
            },
            "summary": {"overall_score": overall_score, "problems_detected": problems},
        }

        return overall_score, report

    def _evaluate_plan_completion(self, plan: Dict[str, object]) -> float:
        """Оцінює відсоток виконання плану.

        Args:
            plan (Dict[str, object]): Словник, що представляє план розвитку.

        Returns:
            float: Відсоток виконання плану (від 0.0 до 1.0).
        """
        if not plan or "next_steps" not in plan:
            return 0.0  # type: ignore

        total_steps = len(plan.get("next_steps", [])) + len(plan.get("completed_steps", []))
        if total_steps == 0:
            return 0.0  # type: ignore

        completed_steps = len([step for step in plan.get("next_steps", []) if step.get("status") == "completed"])
        completed_steps += len(plan.get("completed_steps", []))

        return completed_steps / total_steps

    def _evaluate_code_quality(self, project_state: Dict[str, str]) -> float:
        """Оцінює якість коду в проекті.

        Включає підрахунок співвідношення коментарів та, якщо доступно,
        використовує Gemini для більш глибокої оцінки.

        Args:
            project_state (Dict[str, str]): Словник, що представляє стан проекту.

        Returns:
            float: Оцінка якості коду (від 0.0 до 1.0).
        """
        if not project_state:
            return 0.0  # type: ignore

        # Базова оцінка
        score = 0.5  # type: ignore

        # Підраховуємо метрики якості коду
        py_files = {
            path: content
            for path, content in project_state.items()
            if path.endswith(".py") and not path.startswith("SELF/")
        }
        if not py_files:
            return score

        # Підраховуємо коментарі
        comment_ratio = 0.0  # type: ignore
        for content in py_files.values():
            lines = content.split("\n")
            code_lines = len(lines)
            comment_lines = sum(1 for line in lines if line.strip().startswith("#"))
            if code_lines > 0:
                comment_ratio += comment_lines / code_lines

        comment_ratio /= len(py_files)

        # Оцінюємо якість коду на основі метрик
        if comment_ratio > 0.1:
            score += 0.1  # type: ignore

        # Якщо доступний gemini_interaction, використовуємо його для оцінки
        if self.gemini_interaction:
            for _path, content in py_files.items():
                # Обмежуємо розмір коду для аналізу
                if len(content) > 5000:
                    content = content[:5000] + "..."

                prompt_parts = [
                    "Ти - AI-асистент для оцінки якості коду.",
                    "Оціни якість наступного Python-коду за шкалою від 0 до 1:",
                    f"```python\n{content}\n```",
                    "Поверни лише число від 0 до 1, де 0 - дуже погана якість, 1 - відмінна якість.",
                ]

                response = self.gemini_interaction.generate_content(
                    prompt_parts=prompt_parts, generation_config={"temperature": 0.1}
                )

                if response:
                    try:
                        file_score = float(response.strip())
                        score = (score + file_score) / 2
                    except ValueError:  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa  # noqa
                        pass

        return min(max(score, 0.0), 1.0)

    def _evaluate_architecture(self, dependency_report: Dict[str, object]) -> float:
        """Оцінює архітектуру проекту на основі звіту про залежності.

        Зменшує оцінку за наявність циклічних залежностей та
        збільшує за модульність.

        Args:
            dependency_report (Dict[str, object]): Звіт про залежності проекту.

        Returns:
            float: Оцінка архітектури (від 0.0 до 1.0).
        """
        if not dependency_report:
            return 0.5  # type: ignore

        # Базова оцінка
        score = 0.5  # type: ignore

        # Оцінюємо архітектуру на основі залежностей
        dependencies = dependency_report.get("dependencies", {})
        if not dependencies:
            return score

        # Підраховуємо циклічні залежності
        circular_dependencies = 0
        for module, deps in dependencies.items():
            for dep in deps:
                if dep in dependencies and module in dependencies[dep]:
                    circular_dependencies += 1

        # Зменшуємо оцінку за циклічні залежності
        if circular_dependencies > 0:
            score -= 0.1 * min(circular_dependencies, 5)

        # Оцінюємо модульність
        modules_count = len(dependencies)
        if modules_count > 1:
            score += 0.1  # type: ignore

        return min(max(score, 0.0), 1.0)

    def _identify_problems(
        self, project_state: Dict[str, str], current_plan: Dict[str, object], dependency_report: Dict[str, object]
    ) -> List[Dict[str, object]]:
        """Ідентифікує проблеми в проекті на основі його стану, плану та залежностей.

        Args:
            project_state (Dict[str, str]): Словник, що представляє стан проекту.
            current_plan (Dict[str, object]): Поточний план розвитку проекту.
            dependency_report (Dict[str, object]): Звіт про залежності проекту.

        Returns:
            List[Dict[str, object]]: Список виявлених проблем.
        """
        problems: List = []

        # Перевіряємо наявність файлів
        if not project_state:
            problems.append({"type": "empty_project", "message": "Проект не містить файлів"})
            return problems

        # Перевіряємо виконання плану
        if current_plan:
            failed_steps = [step for step in current_plan.get("next_steps", []) if step.get("status") == "failed"]
            for step in failed_steps:
                problems.append(
                    {
                        "type": "failed_step",
                        "message": f"Крок {step.get('step_number')} не виконано: {step.get('task')}",
                        "step": step,
                    }
                )
        py_files = {
            path: content
            for path, content in project_state.items()
            if path.endswith(".py") and not path.startswith("SELF/")
        }
        for path, content in py_files.items():
            # Перевіряємо наявність коментарів
            lines = content.split("\n")
            comment_lines = sum(1 for line in lines if line.strip().startswith("#"))
            if comment_lines == 0 and len(lines) > 10:
                problems.append({"type": "no_comments", "message": f"Файл {path} не містить коментарів", "file": path})

            # Перевіряємо довжину рядків
            long_lines = [i + 1 for i, line in enumerate(lines) if len(line) > 100]
            if long_lines:
                problems.append(
                    {
                        "type": "long_lines",
                        "message": f"Файл {path} містить рядки довжиною більше 100 символів",
                        "file": path,
                        "lines": long_lines[:5],  # Обмежуємо кількість рядків у звіті
                    }
                )

        # Перевіряємо архітектуру
        if dependency_report:
            dependencies = dependency_report.get("dependencies", {})
            for module, deps in dependencies.items():
                for dep in deps:
                    if dep in dependencies and module in dependencies[dep]:
                        problems.append(
                            {
                                "type": "circular_dependency",
                                "message": f"Циклічна залежність між модулями {module} та {dep}",
                                "modules": [module, dep],
                            }
                        )

        return problems
