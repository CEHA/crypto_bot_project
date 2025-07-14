#!/usr/bin/env python3
"""Clean project from generated and temporary files."""

import shutil
from pathlib import Path


def clean_project() -> None:
    """Clean generated and temporary files."""
    project_root = Path(".")

    # Patterns to clean
    patterns_to_remove = [
        "**/__pycache__",
        "**/*.pyc",
        "**/*.pyo",
        "**/*.pyd",
        ".mypy_cache",
        ".ruff_cache",
        "**/*.backup",
        "**/*_fixed.py",
        "**/*refactoring_suggestions.txt",
        "**/*dead_code_suggestions.txt",
        ".pytest_cache",
        "*.egg-info",
        "build/",
        "dist/",
    ]

    # Files to clean
    files_to_remove = [
        "gemini_cache.json",
        "error_cache.json",
        "automation.log",
        "logs/agent_errors.log",
        "logs/agent.log",
        "logs/bootstrap.log",
        "logs/continuous.log",
    ]

    removed_count = 0

    print("🧹 Cleaning project...")

    # Remove pattern matches
    for pattern in patterns_to_remove:
        for path in project_root.glob(pattern):
            try:
                if path.is_dir():
                    shutil.rmtree(path)
                    print(f"📁 Removed directory: {path}")
                else:
                    path.unlink()
                    print(f"📄 Removed file: {path}")
                removed_count += 1
            except Exception as e:
                print(f"❌ Failed to remove {path}: {e}")

    # Remove specific files
    for file_path in files_to_remove:
        path = Path(file_path)
        if path.exists():
            try:
                path.unlink()
                print(f"📄 Removed file: {path}")
                removed_count += 1
            except Exception as e:
                print(f"❌ Failed to remove {path}: {e}")

    # Remove backup files
    for backup_file in project_root.glob("*.backup.*"):
        try:
            backup_file.unlink()
            print(f"📄 Removed backup: {backup_file}")
            removed_count += 1
        except Exception as e:
            print(f"❌ Failed to remove {backup_file}: {e}")

    # Clean empty log directories
    logs_dir = Path("logs")
    if logs_dir.exists() and not any(logs_dir.iterdir()):
        try:
            logs_dir.rmdir()
            print(f"📁 Removed empty directory: {logs_dir}")
            removed_count += 1
        except Exception as e:
            print(f"❌ Failed to remove {logs_dir}: {e}")

    print(f"✅ Cleaned {removed_count} items")
    print("🎯 Project cleaned successfully!")


if __name__ == "__main__":
    clean_project()
