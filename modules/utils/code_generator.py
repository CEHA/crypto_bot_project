import ast
from typing import Dict, List, Optional


class CodeGenerator:
    """Генератор коду Python на основі специфікацій."""

    def __init__(self, indent_string: str = "    ") -> None:
        """Ініціалізує CodeGenerator."""
        self.indent_level: int = 0
        self.indent_string: str = indent_string

    def indent(self) -> None:
        """Збільшує рівень відступу."""
        self.indent_level += 1

    def dedent(self) -> None:
        """Зменшує рівень відступу."""
        if self.indent_level > 0:
            self.indent_level -= 1

    def get_indentation(self) -> str:
        """Повертає поточний рядок відступу."""
        return self.indent_string * self.indent_level

    def generate_class(
        self,
        class_name: str,
        attributes: Dict[str, str],
        methods: List[Dict[str, object]],
        base_classes: Optional[List[str]] = None,
        docstring: str = "",
    ) -> str:
        """Генерує код класу."""
        code = f"{self.get_indentation()}class {class_name}"
        if base_classes:
            code += f"({', '.join(base_classes)})"
        code += ":\n"
        self.indent()

        if docstring:
            code += f'{self.get_indentation()}"""{docstring}"""\n'

        if not attributes and not methods:
            code += f"{self.get_indentation()}pass\n"
        else:
            if attributes:
                code += f"{self.get_indentation()}def __init__(self"
                for attr_name, attr_type in attributes.items():
                    code += f", {attr_name}: {attr_type}"
                code += ") -> None:\n"
                self.indent()
                for attr_name, _attr_type in attributes.items():
                    code += f"{self.get_indentation()}self.{attr_name} = {attr_name}\n"
                self.dedent()
                code += "\n"

            for method_spec in methods:
                code += self.generate_method(method_spec)

        self.dedent()
        return code

    def generate_method(self, method_spec: Dict[str, object]) -> str:
        """Генерує код методу."""
        method_name = method_spec["name"]
        parameters = method_spec.get("parameters", {})
        return_type = method_spec.get("return_type", "None")
        body = method_spec.get("body", ["pass"])
        docstring = method_spec.get("docstring", "")

        code = f"\n{self.get_indentation()}def {method_name}(self"
        if parameters:
            params_str = ", ".join(f"{name}: {type_}" for name, type_ in parameters.items())
            code += f", {params_str}"
        code += f") -> {return_type}:\n"
        self.indent()

        if docstring:
            code += f'{self.get_indentation()}"""{docstring}"""\n'

        for line in body:
            code += f"{self.get_indentation()}{line}\n"
        self.dedent()
        return code

    def generate_function(
        self, function_name: str, parameters: Dict[str, str], return_type: str, body: List[str], docstring: str = ""
    ) -> str:
        """Генерує код функції."""
        code = f"{self.get_indentation()}def {function_name}("
        params_str = ", ".join(f"{name}: {type_}" for name, type_ in parameters.items())
        code += f"{params_str}) -> {return_type}:\n"
        self.indent()

        if docstring:
            code += f'{self.get_indentation()}"""{docstring}"""\n'

        for line in body:
            code += f"{self.get_indentation()}{line}\n"
        self.dedent()
        return code

    def is_valid_python(self, code: str) -> bool:
        """Перевіряє, чи є наданий рядок валідним кодом Python."""
        try:
            ast.parse(code)
            return True
        except SyntaxError:  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007
            return False
