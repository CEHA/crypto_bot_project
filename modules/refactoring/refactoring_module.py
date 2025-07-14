from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


# --- Proposal Definitions ---


class ProposalType(Enum):
    """Enumeration of different types of code refactoring proposals."""

    RENAME_SYMBOL = "rename_symbol"
    ADD_TYPE_HINT = "add_type_hint"
    REPLACE_DEPRECATED = "replace_deprecated"
    EXTRACT_METHOD = "extract_method"
    REORDER_IMPORTS = "reorder_imports"
    INSERT_CODE = "insert_code"
    DELETE_CODE = "delete_code"
    # Add more complex types as needed


@dataclass
class CodeFixProposal:
    """Base class for all code fix proposals.

    Attributes:
        proposal_type (ProposalType): The type of the proposal.
        line_start (int): The starting line number (1-indexed) of the code to be affected.
        line_end (int): The ending line number (1-indexed) of the code to be affected.
        column_start (Optional[int]): The starting column number (0-indexed) of the code to be affected.
                                      Optional, as some fixes might be line-wide.
        column_end (Optional[int]): The ending column number (0-indexed) of the code to be affected.
                                    Optional, as some fixes might be line-wide.
        description (str): A human-readable description of the proposed fix.
        metadata (Dict[str, object]): Additional data specific to the proposal type.
    """

    proposal_type: ProposalType
    line_start: int
    line_end: int
    description: str


@dataclass
class RenameSymbolProposal(CodeFixProposal):
    """A proposal to rename a symbol (variable, function, class).

    Attributes:
        old_name (str): The current name of the symbol.
        new_name (str): The new name for the symbol.
    """

    old_name: str
    new_name: str
    # Common optional fields
    column_start: Optional[int] = None
    column_end: Optional[int] = None
    metadata: Dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Метод __post_init__."""
        self.proposal_type = ProposalType.RENAME_SYMBOL  # type: ignore
        if not self.description:
            self.description = f"Rename '{self.old_name}' to '{self.new_name}'"
        self.metadata["old_name"] = self.old_name  # type: ignore
        self.metadata["new_name"] = self.new_name  # type: ignore


@dataclass
class AddTypeHintProposal(CodeFixProposal):
    """A proposal to add a type hint to a function parameter, return, or variable.

    Attributes:
        target_name (str): The name of the parameter/variable/function to hint.
        hint_type (str): The type hint to add (e.g., "str", "List[int]").
        hint_location (str): Where the hint should be added (e.g., "parameter", "return", "variable_assignment").
        position_in_line (Optional[int]): The specific column where the hint should be inserted if known.
    """

    target_name: str
    hint_type: str
    hint_location: str  # e.g., 'parameter', 'return', 'variable_assignment'
    # Common optional fields
    column_start: Optional[int] = None
    column_end: Optional[int] = None
    metadata: Dict[str, object] = field(default_factory=dict)
    # Specific optional fields
    position_in_line: Optional[int] = None  # For precise insertion

    def __post_init__(self) -> None:
        """Метод __post_init__."""
        self.proposal_type = ProposalType.ADD_TYPE_HINT  # type: ignore
        if not self.description:
            self.description = f"Add type hint '{self.hint_type}' to '{self.target_name}' ({self.hint_location})"
        self.metadata["target_name"] = self.target_name  # type: ignore
        self.metadata["hint_type"] = self.hint_type  # type: ignore
        self.metadata["hint_location"] = self.hint_location  # type: ignore
        if self.position_in_line is not None:
            self.metadata["position_in_line"] = self.position_in_line  # type: ignore


@dataclass
class ReplaceDeprecatedProposal(CodeFixProposal):
    """A proposal to replace a deprecated function call or pattern.

    Attributes:
        old_pattern (str): The regex pattern or exact string of the deprecated code.
        new_replacement (str): The replacement string.
        is_regex (bool): True if `old_pattern` should be treated as a regex.
    """

    old_pattern: str
    new_replacement: str
    # Common optional fields
    column_start: Optional[int] = None
    column_end: Optional[int] = None
    metadata: Dict[str, object] = field(default_factory=dict)
    # Specific optional fields
    is_regex: bool = False

    def __post_init__(self) -> None:
        """Метод __post_init__."""
        self.proposal_type = ProposalType.REPLACE_DEPRECATED  # type: ignore
        if not self.description:
            self.description = f"Replace deprecated '{self.old_pattern}' with '{self.new_replacement}'"
        self.metadata["old_pattern"] = self.old_pattern  # type: ignore
        self.metadata["new_replacement"] = self.new_replacement  # type: ignore
        self.metadata["is_regex"] = self.is_regex  # type: ignore


@dataclass
class ExtractMethodProposal(CodeFixProposal):
    """A proposal to extract a block of code into a new method/function.

    Attributes:
        new_method_name (str): The name for the new method/function.
        parameters (List[str]): List of parameters for the new method (e.g., ["self", "arg1", "arg2"]).
        return_value (Optional[str]): The name of the variable that will be returned, if any.
    """

    new_method_name: str
    parameters: List[str]
    return_value: Optional[str]
    indentation_level: int
    # Common optional fields
    column_start: Optional[int] = None
    column_end: Optional[int] = None
    metadata: Dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Метод __post_init__."""
        self.proposal_type = ProposalType.EXTRACT_METHOD  # type: ignore
        if not self.description:
            self.description = f"Extract method '{self.new_method_name}'"
        self.metadata["new_method_name"] = self.new_method_name  # type: ignore
        self.metadata["parameters"] = self.parameters  # type: ignore
        self.metadata["return_value"] = self.return_value  # type: ignore
        self.metadata["indentation_level"] = self.indentation_level  # type: ignore


@dataclass
class ReorderImportsProposal(CodeFixProposal):
    """A proposal to reorder and clean up imports in a file.

    This proposal typically applies to the entire file, so line/column info might be less precise.
    `line_start` must be 1 for file-wide application.
    """

    # Common optional fields
    column_start: Optional[int] = None
    column_end: Optional[int] = None
    metadata: Dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Метод __post_init__."""
        self.proposal_type = ProposalType.REORDER_IMPORTS  # type: ignore
        if not self.description:
            self.description = "Reorder and clean up imports"
        if self.line_start != 1:
            raise ValueError("ReorderImportsProposal should start at line 1 for file-wide application.")


@dataclass
class InsertCodeProposal(CodeFixProposal):
    """A proposal to insert new code at a specific location.

    Attributes:
        code_to_insert (str): The code string to insert.
        indentation_level (int): The indentation level for the inserted code.
        insert_after_line (bool): If true, insert after line_start, otherwise at line_start.
    """

    code_to_insert: str
    # Common optional fields
    column_start: Optional[int] = None
    column_end: Optional[int] = None
    metadata: Dict[str, object] = field(default_factory=dict)
    # Specific optional fields
    indentation_level: int = 0
    insert_after_line: bool = False  # If true, insert after line_start, otherwise at line_start

    def __post_init__(self) -> None:
        """Метод __post_init__."""
        self.proposal_type = ProposalType.INSERT_CODE  # type: ignore
        if not self.description:
            self.description = f"Insert code at line {self.line_start}"
        self.metadata["code_to_insert"] = self.code_to_insert  # type: ignore
        self.metadata["indentation_level"] = self.indentation_level  # type: ignore
        self.metadata["insert_after_line"] = self.insert_after_line  # type: ignore


@dataclass
class DeleteCodeProposal(CodeFixProposal):
    """A proposal to delete a block of code.

    Attributes:
        # line_start, line_end, column_start, column_end from base class define the range to delete.
        # No additional fields needed.
    """

    # Common optional fields
    column_start: Optional[int] = None
    column_end: Optional[int] = None
    metadata: Dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Метод __post_init__."""
        self.proposal_type = ProposalType.DELETE_CODE  # type: ignore
        if not self.description:
            self.description = f"Delete code from line {self.line_start} to {self.line_end}"
