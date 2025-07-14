import ast
import logging
import re
from typing import Dict, List


# Налаштування логування
logger = logging.getLogger(__name__)


class CodeBlockExtractor:
    """Клас для витягування логічних блоків коду (класів, функцій) з файлів."""

    def __init__(self) -> None:
        """Ініціалізує екстрактор блоків коду."""
        logger.info("CodeBlockExtractor ініціалізовано")

    def extract_blocks_from_file(self, file_path: str) -> Dict[str, object]:
        """Читає файл та витягує з нього блоки коду.

        Args:
            file_path (str): Шлях до файлу для аналізу.

        Returns:
            Dict[str, object]: Словник з результатом, що містить список блоків,
                            або інформацію про помилку.
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            return self.extract_blocks_from_code(content, file_path)
        except Exception as e:
            logger.error(f"Помилка при витягуванні блоків з файлу {file_path}: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}

    def extract_blocks_from_code(self, code: str, file_path: str = "") -> Dict[str, object]:
        """Витягує блоки коду з наданого рядка коду.

        Використовує AST для Python-файлів для точності та регулярні вирази
        як резервний варіант або для інших типів файлів.

        Args:
            code (str): Рядок з кодом для аналізу.
            file_path (str, optional): Шлях до файлу, з якого взято код.
                                       Використовується для визначення стратегії аналізу.

        Returns:
            Dict[str, object]: Словник з результатом, що містить список блоків.
        """
        try:
            # Спроба використати AST для аналізу Python-коду
            if file_path.endswith(".py"):
                return self._extract_blocks_using_ast(code, file_path)
            else:
                # Для інших типів файлів використовуємо регулярні вирази
                return self._extract_blocks_using_regex(code, file_path)
        except SyntaxError:  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa  # noqa
            # Якщо виникла синтаксична помилка, використовуємо регулярні вирази
            logger.warning(f"Синтаксична помилка в файлі {file_path}. Використовуємо регулярні вирази.")
            return self._extract_blocks_using_regex(code, file_path)
        except Exception as e:
            logger.error(f"Помилка при витягуванні блоків з коду: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}

    def _extract_blocks_using_ast(self, code: str, file_path: str) -> Dict[str, object]:
        """Витягує блоки коду (класи та функції) з використанням AST.

        Args:
            code (str): Рядок з Python-кодом.
            file_path (str): Шлях до файлу (для логування).

        Returns:
            Dict[str, object]: Словник з результатом, що містить список
                            витягнутих блоків коду.
        """
        try:
            tree = ast.parse(code)

            blocks: List = []

            # Витягуємо класи
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Знаходимо початок і кінець класу
                    class_start = node.lineno  # type: ignore
                    class_end = self._find_node_end(node, code)

                    # Витягуємо код класу
                    class_code = "\n".join(code.split("\n")[class_start - 1 : class_end])

                    blocks.append(
                        {
                            "type": "class",
                            "name": node.name,
                            "start_line": class_start,
                            "end_line": class_end,
                            "code": class_code,
                        }
                    )

                # Витягуємо функції (не методи класів)
                elif isinstance(node, ast.FunctionDef):
                    # Перевіряємо, чи батьківський вузол не є класом
                    # Це потребує більш складного аналізу дерева або передачі батьківського вузла
                    # Для простоти, припускаємо, що функції верхнього рівня знаходяться безпосередньо в тілі модуля
                    if isinstance(tree, ast.Module) and node in tree.body:
                        # Знаходимо початок і кінець функції
                        func_start = node.lineno  # type: ignore
                        func_end = self._find_node_end(node, code)

                        # Витягуємо код функції
                        func_code = "\n".join(code.split("\n")[func_start - 1 : func_end])

                        blocks.append(
                            {
                                "type": "function",
                                "name": node.name,
                                "start_line": func_start,
                                "end_line": func_end,
                                "code": func_code,
                            }
                        )

            return {"status": "success", "file_path": file_path, "blocks": blocks}
        except Exception as e:
            logger.error(f"Помилка при витягуванні блоків з використанням AST: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}

    def _extract_blocks_using_regex(self, code: str, file_path: str) -> Dict[str, object]:
        """Витягує блоки коду з використанням регулярних виразів.

        Цей метод є менш точним, ніж аналіз AST, і використовується як
        резервний варіант або для не-Python файлів.

        Args:
            code (str): Рядок з кодом.
            file_path (str): Шлях до файлу (для логування).

        Returns:
            Dict[str, object]: Словник з результатом, що містить список блоків.
        """
        blocks: List = []

        # Розбиваємо код на рядки
        lines = code.split("\n")

        # Шаблони для пошуку блоків коду
        patterns = {
            "class": r"^\s*class\s+(\w+)",
            "function": r"^\s*def\s+(\w+)",
            "section": r"^\s*#{3,}\s*(.*?)\s*#{3,}",
        }

        current_block = None

        for i, line in enumerate(lines):
            # Перевіряємо, чи рядок відповідає одному з шаблонів
            for block_type, pattern in patterns.items():
                match = re.match(pattern, line)
                if match:
                    # Якщо знайдено новий блок, зберігаємо попередній
                    if current_block:
                        current_block["code"] = "\n".join(lines[current_block["start_line"] - 1 : i])
                        blocks.append(current_block)

                    # Створюємо новий блок
                    current_block = {
                        "type": block_type,
                        "name": match.group(1),
                        "start_line": i + 1,
                        "end_line": None,  # Буде визначено пізніше
                    }
                    break

        # Додаємо останній блок
        if current_block:
            current_block["code"] = "\n".join(lines[current_block["start_line"] - 1 :])
            current_block["end_line"] = len(lines)  # Встановлюємо end_line для останнього блоку
            blocks.append(current_block)

        return {"status": "success", "file_path": file_path, "blocks": blocks}

    def _find_node_end(self, node: ast.AST, code: str) -> int:
        """Знаходить номер останнього рядка для вузла AST.

        Спочатку намагається використати атрибут `end_lineno` (доступний у Python 3.8+).
        Якщо він відсутній, використовує евристичний метод для визначення кінця блоку,
        аналізуючи відступи.

        Args:
            node (ast.AST): Вузол AST, для якого потрібно знайти кінець.
            code (str): Повний вихідний код файлу.

        Returns:
            int: Номер останнього рядка, що належить до вузла.
        """
        # Отримуємо останній рядок з атрибутів вузла
        if hasattr(node, "end_lineno") and node.end_lineno is not None:
            return node.end_lineno  # type: ignore

        # Якщо атрибут end_lineno відсутній, шукаємо останній рядок вручну
        lines = code.split("\n")
        start_line = node.lineno  # type: ignore

        # Визначаємо відступ першого рядка
        first_line_content = lines[start_line - 1]
        indent = len(first_line_content) - len(first_line_content.lstrip())

        # Шукаємо перший рядок з таким самим або меншим відступом,
        # або кінець файлу, або початок наступного елемента того ж рівня
        for i in range(start_line, len(lines)):
            line_content = lines[i]
            if line_content.strip():  # Ігноруємо порожні рядки
                current_indent = len(line_content) - len(line_content.lstrip())
                if current_indent <= indent:
                    # Перевіряємо, чи це не продовження поточного блоку (наприклад, багаторядковий рядок)
                    # Це спрощена перевірка, може потребувати покращення
                    if i > start_line - 1:  # Якщо це не перший рядок блоку
                        return i  # Повертаємо номер попереднього рядка як кінець блоку
                    # Якщо це перший рядок блоку і відступ менший або рівний,
                    # це може бути кінець блоку, якщо немає вкладених елементів.
                    # Для простоти, припускаємо, що це кінець, якщо немає інших ознак.

        # Якщо не знайдено, повертаємо останній рядок файлу
        return len(lines)
