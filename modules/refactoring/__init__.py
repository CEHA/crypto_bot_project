from .code_generation_module import CodeGenerationModule
from .refactoring_executor import RefactoringExecutor
from .refactoring_module import CodeFixProposal, ProposalType  # Expose relevant dataclasses/enums


"""
Модулі для рефакторингу коду.
"""
__all__ = ["CodeGenerationModule", "RefactoringExecutor", "CodeFixProposal", "ProposalType"]
