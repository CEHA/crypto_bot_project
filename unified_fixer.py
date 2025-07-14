#!/usr/bin/env python3
"""Unified automated code fixer."""

from modules.utils.code_fixer import fix_project_files


def main() -> None:
    """Main fixer."""
    print("🔧 Running unified automated fixes...")
    fix_project_files()
    print("✅ Project fixes completed")


if __name__ == "__main__":
    main()
