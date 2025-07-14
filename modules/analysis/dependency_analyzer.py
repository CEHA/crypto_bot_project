import ast
import logging
import os
from typing import TYPE_CHECKING, Dict, List, Optional, Set

from modules.core.agent_core import AgentCore, TaskHandler


if TYPE_CHECKING:
    from dev_agent import DevAgent
# Налаштування логування
logger = logging.getLogger(__name__)


class DependencyAnalyzer(AgentCore, TaskHandler):
    """Модуль для аналізу залежностей між файлами проекту."""

    def __init__(self, gemini_interaction, json_analyzer, output_dir) -> None:
        """Ініціалізує аналізатор залежностей.

        Args:
            gemini_interaction: Екземпляр для взаємодії з Gemini API.
            json_analyzer: Екземпляр для аналізу JSON.
            output_dir (str): Коренева директорія проекту.
        """
        super().__init__(gemini_interaction, json_analyzer)
        self.output_dir = output_dir
        # Переконуємося, що output_dir є абсолютним шляхом
        if not os.path.isabs(self.output_dir):
            self.output_dir = os.path.abspath(self.output_dir)
        logger.info("DependencyAnalyzer ініціалізовано")

    def handle_task(self, task: Dict[str, object], agent: Optional["DevAgent"] = None) -> Dict[str, object]:
        """Обробляє завдання аналізу залежностей.

        Диспетчеризує завдання до відповідних методів на основі `analysis_type`.

        Args:
            task (Dict[str, object]): Словник, що містить деталі завдання.
            agent (Optional["DevAgent"]): Екземпляр агента. Defaults to None.

        Returns:
            Dict[str, object]: Результат аналізу.
        """
        analysis_type = task.get("analysis_type")
        target_files = task.get("target_files", [])
        options = task.get("options", {})

        logger.info(f"Виконання аналізу залежностей типу '{analysis_type}' для {len(target_files)} файлів")

        if analysis_type == "module_dependencies":
            result = self.analyze_module_dependencies(target_files, options)
            return result
        elif analysis_type == "import_graph":
            result = self.generate_import_graph(target_files, options)
            return result
        elif analysis_type == "circular_dependencies":
            result = self.find_circular_dependencies(target_files, options)
            return result
        else:
            return {"status": "error", "message": f"Тип аналізу залежностей '{analysis_type}' не підтримується"}

    def analyze_module_dependencies(self, target_files: List[str], options: Dict[str, object]) -> Dict[str, object]:
        """Аналізує залежності між вказаними файлами (модулями).

        Args:
            target_files (List[str]): Список відносних шляхів до файлів для аналізу.
            options (Dict[str, object]): Додаткові опції (наразі не використовуються).

        Returns:
            Dict[str, object]: Словник, що містить граф залежностей та статус виконання.
        """
        logger.info(f"Аналіз залежностей між модулями для {len(target_files)} файлів")

        # Збираємо інформацію про імпорти
        imports_map: Dict = {}
        for file_path_rel in target_files:  # Використовуємо відносний шлях для ключа
            full_path = os.path.join(self.output_dir, file_path_rel)
            if not os.path.exists(full_path):
                logger.warning(f"Файл '{full_path}' не знайдено, пропускаємо.")
                continue

            try:
                imports = self._extract_imports(full_path)
                imports_map[file_path_rel] = imports  # Ключ - відносний шлях
            except Exception as e:
                logger.error(f"Помилка при аналізі імпортів у файлі '{full_path}': {e}", exc_info=True)

        # Будуємо граф залежностей
        dependency_graph: Dict = {}
        for file_path_rel, imports in imports_map.items():
            dependency_graph[file_path_rel] = []
            for imp_info in imports:  # Тепер imports - це список словників
                imported_module_name = imp_info["module"]
                # Перевіряємо, чи імпортований модуль є в списку файлів
                # Потрібно нормалізувати шляхи для порівняння
                for target_rel in target_files:
                    # Спрощене порівняння, може потребувати покращення для складних випадків
                    # (наприклад, відносні імпорти, псевдоніми пакетів)
                    target_module_name_parts = target_rel.replace(".py", "").split(os.path.sep)

                    # Спроба зіставити імпорт з шляхом до файлу
                    # Це дуже спрощена логіка і може не працювати для всіх випадків
                    if (
                        imported_module_name == ".".join(target_module_name_parts)
                        or any(part == imported_module_name for part in target_module_name_parts)
                        or target_rel.endswith(f"{imported_module_name.replace('.', os.path.sep)}.py")
                        or target_rel.endswith(f"{imported_module_name.replace('.', os.path.sep)}/__init__.py")
                    ):
                        if target_rel not in dependency_graph[file_path_rel]:
                            dependency_graph[file_path_rel].append(target_rel)
                        break  # Знайшли відповідність, переходимо до наступного імпорту

        return {"status": "success", "dependency_graph": dependency_graph, "files_analyzed": len(imports_map)}

    def generate_import_graph(self, target_files: List[str], options: Dict[str, object]) -> Dict[str, object]:
        """Генерує граф імпортів у форматі, придатному для візуалізації.

        Args:
            target_files (List[str]): Список відносних шляхів до файлів.
            options (Dict[str, object]): Додаткові опції.

        Returns:
            Dict[str, object]: Словник, що містить вузли (nodes) та ребра (edges)
                            графу, а також статус виконання.
        """
        logger.info(f"Генерація графу імпортів для {len(target_files)} файлів")

        # Збираємо інформацію про імпорти
        imports_map: Dict = {}
        for file_path_rel in target_files:
            full_path = os.path.join(self.output_dir, file_path_rel)
            if not os.path.exists(full_path):
                logger.warning(f"Файл '{full_path}' не знайдено, пропускаємо.")
                continue

            try:
                imports = self._extract_imports(full_path)
                imports_map[file_path_rel] = imports
            except Exception as e:
                logger.error(f"Помилка при аналізі імпортів у файлі '{full_path}': {e}", exc_info=True)

        # Формуємо граф імпортів у форматі для візуалізації
        nodes: List = []
        edges: List = []

        for file_path_rel in imports_map:
            nodes.append(
                {
                    "id": file_path_rel,  # Використовуємо відносний шлях як ID
                    "label": os.path.basename(file_path_rel),
                }
            )

        for source_rel, imports in imports_map.items():
            for imp_info in imports:
                imported_module_name = imp_info["module"]
                for target_rel in imports_map:  # Перебираємо ключі, які є відносними шляхами
                    target_module_name_parts = target_rel.replace(".py", "").split(os.path.sep)
                    if (
                        imported_module_name == ".".join(target_module_name_parts)
                        or any(part == imported_module_name for part in target_module_name_parts)
                        or target_rel.endswith(f"{imported_module_name.replace('.', os.path.sep)}.py")
                        or target_rel.endswith(f"{imported_module_name.replace('.', os.path.sep)}/__init__.py")
                    ):
                        edges.append({"source": source_rel, "target": target_rel})
                        break

        return {"status": "success", "graph": {"nodes": nodes, "edges": edges}, "files_analyzed": len(imports_map)}

    def find_circular_dependencies(self, target_files: List[str], options: Dict[str, object]) -> Dict[str, object]:
        """Знаходить циклічні залежності між вказаними файлами.

        Використовує пошук в глибину (DFS) на графі залежностей для виявлення циклів.

        Args:
            target_files (List[str]): Список відносних шляхів до файлів.
            options (Dict[str, object]): Додаткові опції.

        Returns:
            Dict[str, object]: Словник, що містить список виявлених циклів
                            та статус виконання.
        """
        logger.info(f"Пошук циклічних залежностей для {len(target_files)} файлів")

        analysis_result = self.analyze_module_dependencies(target_files, options)
        dependency_graph = analysis_result.get("dependency_graph", {})

        # Знаходимо циклічні залежності
        circular_dependencies: List = []
        # Створюємо копію ключів для безпечної ітерації, якщо граф може змінюватися
        nodes_to_visit = list(dependency_graph.keys())

        for node in nodes_to_visit:
            # Перевіряємо, чи вузол все ще існує в графі (на випадок динамічних змін, хоча тут це малоймовірно)
            if node not in dependency_graph:
                continue
            visited_in_dfs = set()
            path: List = []
            self._dfs(node, node, dependency_graph, visited_in_dfs, path, circular_dependencies)

        # Видаляємо дублікати циклів (якщо вони є різними перестановками одного циклу)
        # Це може бути складним, тому поки що залишаємо як є
        unique_cycles: List = []
        seen_cycles_sets = set()
        for cycle in circular_dependencies:
            # Сортуємо для канонічного представлення, потім перетворюємо на кортеж для додавання в set
            canonical_cycle = tuple(sorted(cycle))
            if canonical_cycle not in seen_cycles_sets:
                unique_cycles.append(cycle)
                seen_cycles_sets.add(canonical_cycle)

        return {
            "status": "success",
            "circular_dependencies": unique_cycles,
            "files_analyzed": analysis_result.get("files_analyzed", 0),
        }

    def _extract_imports(self, file_path: str) -> List[Dict[str, object]]:
        """Витягує інформацію про імпорти з файлу за допомогою аналізу AST.

        Args:
            file_path (str): Абсолютний шлях до файлу.

        Returns:
            List[Dict[str, object]]: Список словників, де кожен описує один імпорт.
        """
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        imports_info: List = []

        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports_info.append(
                            {"module": alias.name, "alias": alias.asname, "line": node.lineno, "type": "import"}
                        )
                elif isinstance(node, ast.ImportFrom):
                    module_name = node.module or ""  # Може бути None для from . import ...
                    level = node.level  # type: ignore  # Рівень відносного імпорту

                    # Формуємо повне ім'я модуля для відносних імпортів
                    if level > 0:
                        # Потрібно визначити шлях до поточного файлу відносно кореня пакету
                        # Це може бути складним без додаткової інформації про структуру проекту
                        # Для простоти, поки що використовуємо '...' для відносних частин
                        relative_prefix = "." * level
                        module_name = f"{relative_prefix}{module_name}" if module_name else relative_prefix.rstrip(".")

                    for alias in node.names:
                        imports_info.append(
                            {
                                "module": f"{module_name}.{alias.name}"
                                if module_name and alias.name != "*"
                                else alias.name,
                                "alias": alias.asname,
                                "from_module": module_name,
                                "name": alias.name,
                                "level": level,
                                "line": node.lineno,
                                "type": "from_import",
                            }
                        )
        except SyntaxError as e:
            logger.error(f"Синтаксична помилка при парсингу імпортів у файлі '{file_path}': {e}", exc_info=True)
        # Можна додати резервну логіку з регулярними виразами, якщо потрібно

        return imports_info

    def _dfs(
        self,
        start_node: str,  # Змінено назву для ясності
        current_node: str,  # Змінено назву для ясності
        graph: Dict[str, List[str]],
        visited_in_current_path: Set[str],  # Змінено назву для ясності
        path: List[str],
        cycles: List[List[str]],
    ) -> None:
        """Рекурсивна функція пошуку в глибину (DFS) для виявлення циклів у графі.

        Args:
            start_node (str): Вузол, з якого почався обхід.
            current_node (str): Поточний вузол обходу.
            graph (Dict[str, List[str]]): Граф залежностей.
            visited_in_current_path (Set[str]): Множина вузлів, відвіданих у поточному шляху.
            path (List[str]): Поточний шлях обходу.
            cycles (List[List[str]]): Список, куди додаються знайдені цикли.
        """
        visited_in_current_path.add(current_node)
        path.append(current_node)

        for neighbor in graph.get(current_node, []):
            if neighbor == start_node:
                # Знайдено цикл, додаємо копію шляху
                cycles.append(list(path) + [start_node])
            elif neighbor not in visited_in_current_path:
                self._dfs(start_node, neighbor, graph, visited_in_current_path, path, cycles)
            # Якщо neighbor вже є в visited_in_current_path, але не є start_node,
            # це означає, що ми знайшли цикл, який не обов'язково включає start_node,
            # але він буде знайдений, коли DFS почнеться з одного з вузлів цього циклу.

        path.pop()
        visited_in_current_path.remove(current_node)
