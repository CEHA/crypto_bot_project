from .code_block_extractor import CodeBlockExtractor
from .dependency_analyzer import DependencyAnalyzer
from .project_analyzer import ProjectAnalyzer


# Спочатку імпортуємо більш базові модулі, щоб уникнути циклічних залежностей

# Потім імпортуємо модулі вищого рівня, які можуть залежати від базових


"""
Модулі для аналізу коду та проекту.
"""
__all__ = ["ProjectAnalyzer", "DependencyAnalyzer", "CodeBlockExtractor"]
