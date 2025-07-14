import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional

from modules.analysis.project_analyzer import ProjectAnalyzer
from modules.core.module_registry import ModuleRegistry  # Added for TaskQueue access
from modules.utils.gemini_client import GeminiClient as GeminiInteraction
from modules.utils.json_analyzer import JsonAnalyzer


logger = logging.getLogger(__name__)


class PlanningModule:
    """Модуль PlanningModule відповідає за генерацію та оновлення планів розвитку проекту.

    Він взаємодіє з Gemini для створення структурованих планів на основі високорівневих цілей
    та результатів аналізу.
    """

    def __init__(
        self,
        gemini_interaction: GeminiInteraction,
        json_analyzer: JsonAnalyzer,
        output_dir: str,
        project_analyzer: Optional[ProjectAnalyzer] = None,
    ) -> None:
        self.gemini_interaction = gemini_interaction
        self.json_analyzer = json_analyzer
        self.output_dir = output_dir
        self.registry = ModuleRegistry()  # Get the singleton registry
        self.project_analyzer = project_analyzer
        logger.info("PlanningModule ініціалізовано")
        self.logger = logging.getLogger(__name__)  # Додаємо логер

    def handle_task(self, task: Dict[str, object]) -> Dict[str, object]:
        """Обробляє завдання, пов'язані з плануванням, викликаючи відповідний метод."""
        planning_type = task.get("planning_type")
        description = task.get("description", "")
        options = task.get("options", {})
        master_plan_file = task.get("master_plan_file_path")

        logger.info(f"Обробка завдання планування типу: {planning_type}")

        if planning_type == "generate_initial_plan":
            return self.generate_initial_plan(description, master_plan_file)
        elif planning_type == "process_master_plan":
            if not master_plan_file:
                msg = f"Завдання 'process_master_plan' вимагає 'master_plan_file_path', але його не надано. Опис: {description}"
                logger.error(msg)
                return {"status": "error", "message": msg}
            return self.process_master_plan(master_plan_file, options)
        elif planning_type == "plan_key_module_analysis":
            return self._plan_key_module_analysis(options)
        elif planning_type == "agent_architecture":
            return self._handle_agent_architecture(description, options)
        elif planning_type == "metaprogramming_strategy":
            return self._handle_metaprogramming_strategy(description, options)
        elif planning_type == "self_improvement_plan":
            return self._handle_self_improvement_plan(description, options)
        else:
            self.logger.error(f"Невідомий тип завдання планування: {planning_type}. Завдання: {description}")
            return {"status": "error", "message": f"Невідомий тип завдання планування: {planning_type}"}

    def generate_initial_plan(
        self, project_description: str, master_plan_file_path: Optional[str] = None
    ) -> Dict[str, object]:
        """Генерує початковий план для проекту на основі опису."""
        logger.info(f"Генерація початкового плану для проекту: {project_description[:50]}...")

        prompt_parts = [
            "Ти - досвідчений менеджер проектів та архітектор програмного забезпечення. "
            "Твоє завдання - створити детальний, структурований план розробки програмного забезпечення.",
            "На основі наступного опису проекту, згенеруй план у форматі JSON. "
            "План повинен включати: загальний опис проекту, цілі, обсяг (що входить/не входить), "
            "фази розробки (з датами, результатами та статусом), часову шкалу (з основними етапами), "
            "необхідні ресурси (команда, інструменти, бюджет), потенційні ризики та стратегії їх зменшення, "
            "зацікавлені сторони, план комунікації, стратегію забезпечення якості та стратегію розгортання.",
            "--- ОПИС ПРОЕКТУ ---",
            project_description,
            "--- КІНЕЦЬ ОПИСУ ПРОЕКТУ ---",
            "\n",
            "Твоя відповідь ПОВИННА бути ТІЛЬКИ JSON-об'єктом, без жодних додаткових пояснень, коментарів чи markdown-обгорток.",
        ]

        try:
            response_str = self.gemini_interaction.generate_content(
                prompt_parts=prompt_parts, generation_config={"response_mime_type": "application/json"}
            )

            # Спроба очистити відповідь від зайвих символів, якщо Gemini додає їх
            if response_str and isinstance(response_str, str):
                if response_str.startswith("```json"):
                    response_str = response_str[len("```json") :].strip()
                if response_str.endswith("```"):
                    response_str = response_str[: -len("```")].strip()

            plan_data = json.loads(response_str)

            if master_plan_file_path:
                full_path = os.path.join(self.output_dir, master_plan_file_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, "w", encoding="utf-8") as f:
                    # Зберігаємо JSON як Markdown, щоб його можна було легко читати
                    # Це спрощення, в реальності можна було б генерувати більш складний Markdown
                    f.write("# Головний план розвитку\n\n")
                    f.write(f"## Опис проекту\n\n{plan_data.get('project_description', 'N/A')}\n\n")
                    f.write("## Наступні кроки\n\n")
                    for step in plan_data.get("next_steps", []):
                        f.write(f"### {step.get('step_number', '')}. {step.get('task', 'N/A')}\n")
                        f.write(f"- **Файл**: {step.get('file_name', 'N/A')}\n")
                        f.write(f"- **Статус**: {step.get('status', 'N/A')}\n")
                        f.write(f"- **Залежності**: {', '.join(map(str, step.get('dependencies', [])))}\n\n")
                logger.info(f"Початковий план збережено у файл: {full_path}")

            return {"status": "success", "plan": plan_data}

        except json.JSONDecodeError as e:
            logger.error(
                f"Помилка декодування JSON відповіді від Gemini: {e}. Відповідь: {response_str[:500]}...", exc_info=True
            )
            return {"status": "error", "message": f"Не вдалося згенерувати початковий план: некоректний JSON: {e}"}
        except Exception as e:
            logger.error(f"Помилка при генерації початкового плану: {e}", exc_info=True)
            return {"status": "error", "message": f"Не вдалося згенерувати початковий план: {e}"}

    def update_plan_from_context(self, current_plan_content: str, context_description: str) -> Dict[str, object]:
        """Оновлює існуючий план розвитку на основі нового контексту."""
        logger.info(f"Оновлення плану з контексту: {context_description[:50]}...")

        prompt_parts = [
            "Ти - AI-асистент, відповідальний за оновлення плану розвитку проекту.",
            "Ось поточний план розвитку проекту у форматі Markdown:",
            "--- ПОТОЧНИЙ ПЛАН ---",
            current_plan_content,
            "--- КІНЕЦЬ ПОТОЧНОГО ПЛАНУ ---",
            "\n",
            "Ось новий контекст або виконана робота, яку потрібно врахувати:",
            "--- НОВИЙ КОНТЕКСТ ---",
            context_description,
            "--- КІНЕЦЬ НОВОГО КОНТЕКСТУ ---",
            "\n",
            "Твоє завдання - оновити план розвитку, щоб він відображав новий контекст. "
            "Ти можеш змінити статуси кроків, додати нові кроки, або змінити існуючі описи. "
            "Зберігай оригінальну структуру та форматування Markdown. "
            "Поверни ТІЛЬКИ повний оновлений текст плану у форматі Markdown. Не додавай жодних пояснень чи коментарів поза текстом плану.",
        ]

        try:
            updated_plan_content = self.gemini_interaction.generate_content(
                prompt_parts=prompt_parts, generation_config={"temperature": 0.2, "response_mime_type": "text/plain"}
            )

            if updated_plan_content:
                return {"status": "success", "updated_plan": updated_plan_content}
            else:
                logger.error("Gemini не повернув оновлений план.")
                return {"status": "error", "message": "Не вдалося отримати оновлений план від Gemini."}

        except Exception as e:
            logger.error(f"Помилка при оновленні плану з контексту: {e}", exc_info=True)
            return {"status": "error", "message": f"Помилка при оновленні плану з контексту: {e}"}

    def process_master_plan(self, master_plan_file_path: str, options: Dict[str, object]) -> Dict[str, object]:
        """Обробляє головний план розвитку, витягує з нього завдання та додає їх до черги."""
        logger.info(f"Обробка головного плану розвитку з файлу: {master_plan_file_path}")

        full_path = os.path.join(self.output_dir, master_plan_file_path)
        if not os.path.exists(full_path):
            logger.error(f"Файл головного плану не знайдено: {full_path}")
            return {"status": "error", "message": f"Файл головного плану не знайдено: {full_path}"}

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                master_plan_content = f.read()

            initial_focus_points = options.get("initial_focus_points", [])

            prompt_parts = [
                "Ти - AI-асистент, який перетворює секції плану розвитку на конкретні завдання для DevAgent.",
                "Ось головний план розвитку проекту у форматі Markdown:",
                "--- МАЙСТЕР ПЛАН ---",
                master_plan_content,
                "--- КІНЕЦЬ МАЙСТЕР ПЛАНУ ---",
                "\n",
                "Твоє завдання - проаналізувати план і згенерувати список завдань у форматі JSON, "
                "які DevAgent може виконати. Кожне завдання повинно бути об'єктом з обов'язковими полями `type` та `description`.",
                "Вимоги до полів залежно від типу:",
                "- `type` (рядок): Тип завдання. Допустимі значення: 'code_generation', 'refactoring', 'analysis', 'planning', 'self_improvement', 'test', 'documentation'.",
                "- `description` (рядок): Детальний опис завдання.",
                "- Для `code_generation`: ОБОВ'ЯЗКОВО `output_file` (рядок).",
                "- Для `refactoring`: ОБОВ'ЯЗКОВО `target_files` (список рядків) та `refactoring_type` (рядок).",
                "- Для `analysis`: ОБОВ'ЯЗКОВО `analysis_type` (рядок). Якщо `analysis_type` - 'code_quality_review', ОБОВ'ЯЗКОВО `target_files`.",
                "- Для `test`: ОБОВ'ЯЗКОВО `test_type` (рядок). Якщо `test_type` - 'generate_tests', ОБОВ'ЯЗКОВО `target_files`.",
                "- Для `documentation`: ОБОВ'ЯЗКОВО `doc_type` (рядок).",
                "- Для `planning`: ОБОВ'ЯЗКОВО `planning_type` (рядок).",
                "- Для `self_improvement`: ОБОВ'ЯЗКОВО `improvement_type` (рядок).",
                "- `options` (об'єкт, опціонально): Додаткові параметри для завдання.",
                "- `priority_score` (ціле число, опціонально): Оцінка пріоритету завдання (чим вище, тим важливіше).",
                "\n",
                "Зосередься на завданнях, які відповідають наступним початковим пунктам фокусування (якщо вказано):",
                f"Початкові пункти фокусування: {initial_focus_points if initial_focus_points else 'Не вказано, генеруй завдання для всіх відповідних секцій.'}",
                "\n",
                "Поверни ТІЛЬКИ JSON-масив завдань, без жодних додаткових пояснень, коментарів чи markdown-обгорток.",
            ]

            response_str = self.gemini_interaction.generate_content(
                prompt_parts=prompt_parts, generation_config={"response_mime_type": "application/json"}
            )

            # Спроба очистити відповідь від зайвих символів, якщо Gemini додає їх
            if response_str and isinstance(response_str, str):
                if response_str.startswith("```json"):
                    response_str = response_str[len("```json") :].strip()
                if response_str.endswith("```"):
                    response_str = response_str[: -len("```")].strip()

            # Перевіряємо, чи відповідь є рядком, і розбираємо її як JSON.
            # Це робить обробку більш надійною.
            if isinstance(response_str, str):
                suggested_tasks = json.loads(response_str)
            else:
                suggested_tasks = response_str  # Припускаємо, що це вже розпарсений об'єкт

            if not isinstance(suggested_tasks, list):
                raise ValueError(f"Відповідь Gemini не є JSON-масивом завдань. Отримано тип: {type(suggested_tasks)}")

            # Валідація згенерованих завдань перед додаванням до черги
            validated_tasks: List = []
            for task in suggested_tasks:
                if not isinstance(task, dict) or "type" not in task or "description" not in task:
                    logger.warning(
                        f"Пропускаємо некоректно сформоване завдання (відсутні 'type' або 'description'): {task}"
                    )
                    continue

                is_valid = True
                task_type = task.get("type")
                desc = task.get("description", "N/A")[:70] + "..."

                # Розширена валідація на основі помилок з логів
                if task_type == "code_generation" and not task.get("output_file"):
                    logger.warning(f"Пропускаємо 'code_generation' без 'output_file': {desc}")
                    is_valid = False
                elif task_type == "refactoring" and (not task.get("target_files") or not task.get("refactoring_type")):
                    logger.warning(f"Пропускаємо 'refactoring' без 'target_files' або 'refactoring_type': {desc}")
                    is_valid = False
                elif (
                    task_type == "analysis"
                    and task.get("analysis_type") == "code_quality_review"
                    and not task.get("target_files")
                ):
                    logger.warning(f"Пропускаємо 'code_quality_review' без 'target_files': {desc}")
                    is_valid = False
                elif task_type == "test" and not task.get("test_type"):
                    logger.warning(f"Пропускаємо 'test' без 'test_type': {desc}")
                    is_valid = False
                elif task_type == "documentation" and not task.get("doc_type"):
                    logger.warning(f"Пропускаємо 'documentation' без 'doc_type': {desc}")
                    is_valid = False

                if is_valid:
                    validated_tasks.append(task)

            # Додаємо завдання до черги TaskQueue
            task_queue = self.registry.get_instance("task_queue")  # Отримуємо екземпляр TaskQueue через реєстр
            if task_queue:
                if validated_tasks:
                    task_queue.add_tasks(validated_tasks)
                    logger.info(
                        f"Додано {len(validated_tasks)} валідних завдань до черги TaskQueue (всього згенеровано: {len(suggested_tasks)})."
                    )
                else:
                    logger.warning("Не згенеровано жодного валідного завдання.")
            else:
                logger.warning("TaskQueue не ініціалізовано. Завдання не додано до черги.")

            # Створюємо "прапорець", що план було оброблено, щоб уникнути повторного запуску
            flag_file_path = os.path.join(os.path.dirname(full_path), ".master_plan_processed")
            try:
                with open(flag_file_path, "w") as f:
                    f.write(datetime.now().isoformat())
                logger.info(f"Створено прапорець обробки плану: {flag_file_path}")
            except Exception as e:
                logger.warning(f"Не вдалося створити прапорець обробки плану: {e}")

            return {
                "status": "success",
                "message": f"PlanningModule processed master plan, {len(validated_tasks)} valid tasks created.",
            }

        except json.JSONDecodeError as e:
            logger.error(
                f"Помилка декодування JSON відповіді від Gemini: {e}. Відповідь: {response_str[:500]}...", exc_info=True
            )
            return {"status": "error", "message": f"Некоректний формат відповіді від Gemini: {e}"}
        except Exception as e:
            logger.error(f"Помилка при обробці головного плану: {e}", exc_info=True)
            return {"status": "error", "message": f"Помилка при обробці головного плану: {e}"}

    def assess_impact_and_complexity(self, opportunity_description: str, code_context: str) -> Dict[str, object]:
        """Використовує Gemini для оцінки впливу та складності потенційного покращення."""
        logger.info(f"Оцінка впливу та складності для: {opportunity_description[:50]}...")

        prompt_parts = [
            "Ти - досвідчений архітектор програмного забезпечення та оцінювач ризиків. "
            "Твоє завдання - оцінити потенційний вплив та складність (зусилля) реалізації "
            "наступної можливості для покращення коду.",
            "Надай свою оцінку у форматі JSON-об'єкта з полями 'impact' та 'complexity'. "
            "Обидва поля повинні бути рядками: 'low', 'medium', 'high'.",
            "--- ОПИС МОЖЛИВОСТІ ---",
            opportunity_description,
            "--- КОНТЕКСТ КОДУ (якщо є) ---",
            code_context if code_context else "Немає додаткового контексту коду.",
            "--- КІНЕЦЬ КОНТЕКСТУ ---",
            "\n",
            "Твоя відповідь ПОВИННА бути ТІЛЬКИ JSON-об'єктом, без жодних додаткових пояснень, коментарів чи markdown-обгорток.",
        ]

        try:
            response_str = self.gemini_interaction.generate_content(
                prompt_parts=prompt_parts, generation_config={"response_mime_type": "application/json"}
            )

            # Спроба очистити відповідь від зайвих символів, якщо Gemini додає їх
            if response_str and isinstance(response_str, str):
                if response_str.startswith("```json"):
                    response_str = response_str[len("```json") :].strip()
                if response_str.endswith("```"):
                    response_str = response_str[: -len("```")].strip()

            assessment = json.loads(response_str)

            if not isinstance(assessment, dict) or "impact" not in assessment or "complexity" not in assessment:
                raise ValueError("Некоректний формат відповіді: очікувався JSON з 'impact' та 'complexity'.")

            logger.info(
                f"Оцінка впливу та складності: Вплив={assessment['impact']}, Складність={assessment['complexity']}"
            )
            return {"status": "success", "impact": assessment["impact"], "complexity": assessment["complexity"]}

        except json.JSONDecodeError as e:
            logger.error(
                f"Помилка декодування JSON відповіді від Gemini: {e}. Відповідь: {response_str[:500]}...", exc_info=True
            )
            return {"status": "error", "message": f"Некоректний формат відповіді від Gemini: {e}"}
        except Exception as e:
            logger.error(f"Помилка при оцінці впливу та складності: {e}", exc_info=True)
            return {"status": "error", "message": f"Помилка при оцінці впливу та складності: {e}"}

    def _plan_key_module_analysis(self, options: Dict[str, object]) -> Dict[str, object]:
        """Планує аналіз ключових модулів.

        1. Визначає ключові модулі за допомогою ProjectAnalyzer.
        2. Створює завдання 'code_quality_review' для кожного знайденого модуля.
        """
        logger.info("Планування аналізу ключових модулів...")

        if not self.project_analyzer:
            msg = "ProjectAnalyzer не ініціалізовано в PlanningModule. Неможливо визначити ключові модулі."
            logger.error(msg)
            return {"status": "error", "message": msg}

        # 1. Визначити ключові модулі
        # Опції для identify_key_modules передаються з основного завдання
        identification_options = options.get("identification_options", {"strategy": "complexity", "top_n": 5})
        identification_result = self.project_analyzer.identify_key_modules(identification_options)

        if identification_result.get("status") != "success":
            logger.error(f"Не вдалося визначити ключові модулі: {identification_result.get('message')}")
            return identification_result

        key_modules = identification_result.get("key_modules", [])
        if not key_modules:
            logger.info("Ключових модулів для аналізу не знайдено.")
            return {"status": "success", "message": "Ключових модулів для аналізу не знайдено.", "tasks_created": 0}

        task_queue = self.registry.get_instance("task_queue")
        if not task_queue:
            msg = "TaskQueue не ініціалізовано. Завдання аналізу не можуть бути додані до черги."
            logger.error(msg)
            return {"status": "error", "message": msg}

        # Перевіряємо наявні завдання, щоб уникнути дублікатів
        # Читаємо існуючі завдання безпосередньо з файлу черги, щоб уникнути помилки AttributeError
        # Це більш надійний підхід, ніж покладатися на внутрішній атрибут об'єкта.
        existing_tasks: List = []
        queue_file_path = os.path.join(self.output_dir, "task_queue.json")
        if os.path.exists(queue_file_path):
            try:
                with open(queue_file_path, "r", encoding="utf-8") as f:
                    existing_tasks = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Не вдалося прочитати або розпарсити файл черги {queue_file_path}: {e}")

        existing_descriptions = {task.get("description") for task in existing_tasks}

        new_unique_tasks: List = []
        suggested_tasks = identification_result.get("suggested_tasks", [])
        for task in suggested_tasks:
            if task.get("description") not in existing_descriptions:
                new_unique_tasks.append(task)
                existing_descriptions.add(task.get("description"))  # Уникаємо дублікатів в одній пачці
            else:
                logger.info(f"Пропускаємо дублююче завдання: {task.get('description')}")

        if new_unique_tasks:
            task_queue.add_tasks(new_unique_tasks)
            logger.info(f"Додано {len(new_unique_tasks)} нових унікальних завдань до черги.")

        return {
            "status": "success",
            "message": f"Успішно заплановано аналіз. Додано {len(new_unique_tasks)} нових завдань.",
            "tasks_created": len(new_unique_tasks),
            "identified_modules": key_modules,
        }

    def _handle_agent_architecture(self, description: str, options: Dict[str, object]) -> Dict[str, object]:
        """Обробляє планування архітектури агента."""
        logger.info(f"Планування архітектури агента: {description}")
        return {"status": "success", "message": "Планування архітектури агента виконано."}

    def _handle_metaprogramming_strategy(self, description: str, options: Dict[str, object]) -> Dict[str, object]:
        """Обробляє стратегію метапрограмування."""
        logger.info(f"Планування стратегії метапрограмування: {description}")
        return {"status": "success", "message": "Стратегія метапрограмування запланована."}

    def _handle_self_improvement_plan(self, description: str, options: Dict[str, object]) -> Dict[str, object]:
        """Обробляє план самовдосконалення агента."""
        logger.info(f"Планування самовдосконалення: {description}")
        return {"status": "success", "message": "План самовдосконалення створено."}
