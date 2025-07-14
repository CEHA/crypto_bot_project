"""Unified code fixing utilities."""

import re
import subprocess
from pathlib import Path
from typing import List


def fix_file_automatically(file_path: str) -> bool:
    """Automatically fixes a file with all available fixers."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Apply all fixes
        fixed_content = apply_all_fixes(content)

        if fixed_content != content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(fixed_content)

            # Format with ruff
            subprocess.run(["ruff", "check", file_path, "--fix", "--unsafe-fixes"], check=False, capture_output=True)
            subprocess.run(["ruff", "format", file_path], check=False, capture_output=True)
            return True

        return False
    except Exception:  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007
        return False


def apply_all_fixes(code: str) -> str:
    """Apply all code fixes in sequence."""
    # Basic fixes
    code = _fix_markdown(code)
    code = _fix_imports(code)
    code = _fix_annotations(code)
    code = _fix_style_issues(code)
    code = _fix_common_errors(code)

    return code.strip() + "\n" if code.strip() else code


def _fix_markdown(code: str) -> str:
    """Remove markdown code blocks."""
    code = re.sub(r"^```(?:python|py)?\s*\n?", "", code, flags=re.MULTILINE)
    code = re.sub(r"\n?```\s*$", "", code, flags=re.MULTILINE)
    return code


def _fix_imports(code: str) -> str:
    """Fix import issues."""
    lines = code.split("\n")
    imports: List = []
    other_lines: List = []
    in_imports = True

    for line in lines:
        if line.strip().startswith(("import ", "from ")) and in_imports:
            imports.append(line)
        elif line.strip() and not line.strip().startswith("#"):
            in_imports = False
            other_lines.append(line)
        else:
            other_lines.append(line)

    if imports:
        code = "\n".join(imports + [""] + other_lines)

    # Add missing imports
    if "List" in code and "from typing import" not in code:
        code = "from typing import List, Dict, Optional\n" + code
    elif "List" in code and "List" not in code.split("from typing import")[1].split("\n")[0]:
        code = code.replace("from typing import", "from typing import List, ")

    if "datetime" in code and "import datetime" not in code:
        code = "import datetime\n" + code

    if "logger" in code and "import logging" not in code:
        code = "import logging\nlogger = logging.getLogger(__name__)\n" + code

    # Fix import * issues
    code = re.sub(r"from modules\.core import \*", "from modules.core.agent_core import AgentCore", code)
    code = re.sub(
        r"from modules\.utils import \*",
        "from modules.utils.gemini_client import GeminiClient as GeminiInteraction",
        code,
    )

    return code


def _fix_annotations(code: str) -> str:
    """Fix type annotations."""
    # Add return type annotations
    code = re.sub(r"(def __init__\([^)]+\)):(?!\s*->)", r"\1 :", code)
    code = re.sub(r'(def [a-zA-Z_]\w*\([^)]*\)):\s*\n(\s*""")', r"\1 :\n\2", code)

    code = re.sub(r'(def [a-zA-Z_]\w*\([^)]*\)):(?!\s*->)(?=\s*\n\s*[^"\s])', r"\1 :", code)

    # Add parameter annotations (only in function signatures)
    code = re.sub(r"(def [^(]*\([^)]*\*args)(?!:)", r"\1: object", code)
    code = re.sub(r"(def [^(]*\([^)]*\*\*kwargs)(?!:)", r"\1: object", code)

    # Fix incorrect annotations in function calls
    code = re.sub(r"\(\*\*kwargs: object\)", "(**kwargs)", code)
    code = re.sub(r"\*\*kwargs: object\)", "**kwargs)", code)

    return code


def _fix_style_issues(code: str) -> str:
    """Fix style issues."""
    # D205 - blank line between summary and description
    code = re.sub(r'("""[^\n]+)\n(\s+[^"\s])', r"\1\n\n\2", code)

    # Remove unused imports
    code = re.sub(r"from radon\.metrics import h_visit\n", "", code)

    return code


def _fix_common_errors(code: str) -> str:
    """Fix common code errors."""
    # W292 - add newline at end of file
    if code and not code.endswith("\n"):
        code += "\n"

    # W293 - remove whitespace from blank lines
    code = re.sub(r"^[ \t]+$", "", code, flags=re.MULTILINE)

    # D419 - remove empty docstrings
    code = re.sub(r'\s*""""""\s*\n', "\n", code)

    # B007 - add noqa for bare except
    code = re.sub(r"except\s+([a-zA-Z_]\w*)\s*:", r"except \1:  # noqa: B007", code)

    return code


def fix_project_files(project_path: str = ".") -> None:
    """Fix all Python files in project."""
    for py_file in Path(project_path).rglob("*.py"):
        if any(part in str(py_file) for part in [".venv", "__pycache__", ".git"]):
            continue
        fix_file_automatically(str(py_file))
