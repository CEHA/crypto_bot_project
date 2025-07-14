import logging
from typing import TYPE_CHECKING, Dict, List, Optional

from modules.core.agent_core import AgentCore, TaskHandler


if TYPE_CHECKING:
    from dev_agent import DevAgent

logger = logging.getLogger(__name__)


class SelfAnalyzer(AgentCore, TaskHandler):
    """Analyzes the agent's own codebase to find and prioritize improvement opportunities."""

    def __init__(self, gemini_interaction, json_analyzer, output_dir: str) -> None:
        """Метод __init__."""
        super().__init__(gemini_interaction, json_analyzer)
        self.output_dir = output_dir
        logger.info("SelfAnalyzer initialized.")

    def handle_task(self, task: Dict[str, object], agent: Optional["DevAgent"] = None) -> Dict[str, object]:
        """Handles analysis tasks to find improvement opportunities."""
        analysis_type = task.get("analysis_type")
        if analysis_type == "codebase_review":
            return self.analyze_codebase(task.get("options", {}))
        elif analysis_type == "full_project_analysis":
            return self.analyze_codebase(task.get("options", {}))
        else:
            return {"status": "error", "message": f"Unsupported analysis type for SelfAnalyzer: {analysis_type}"}

    def _calculate_priority_score(self, severity: str, effort: str) -> int:
        """Calculates a priority score for an improvement opportunity.

        The score is based on a simple formula where higher severity and lower effort
        result in a higher priority score.

        Args:
            severity (str): The estimated severity of the issue ('low', 'medium', 'high').
            effort (str): The estimated effort to fix the issue ('low', 'medium', 'high').

        Returns:
            int: The calculated priority score.
        """
        severity_map = {"low": 1, "medium": 3, "high": 5}
        # Inverted effort scale: low effort leads to a higher score component.
        effort_map = {"low": 5, "medium": 3, "high": 1}

        severity_score = severity_map.get(severity.lower(), 3)  # Default to medium
        effort_score = effort_map.get(effort.lower(), 3)

        # A simple product gives a good priority spread.
        return severity_score * effort_score

    def analyze_codebase(self, options: Dict[str, object]) -> Dict[str, object]:
        """Performs a full analysis of the codebase to identify improvement opportunities.

        This is a simplified example. A real implementation would scan files and use Gemini.
        """
        logger.info("Starting codebase analysis to find improvement opportunities...")

        # Analyze existing codebase for real improvement opportunities
        opportunities = self._scan_codebase_for_improvements()

        # Focus on meta-programming agent improvements, not crypto trading
        filtered_opportunities = [
            opp
            for opp in opportunities
            if not any(
                keyword in opp.get("description", "").lower()
                for keyword in ["trading", "crypto", "binance", "exchange"]
            )
        ]

        opportunities_with_scores: List = []
        for opp in filtered_opportunities:
            # Calculate and assign the priority score to each opportunity.
            opp["priority_score"] = self._calculate_priority_score(
                opp.get("severity", "medium"), opp.get("effort", "medium")
            )
            opportunities_with_scores.append(opp)
            logger.info(f"Found opportunity: '{opp['description']}' with priority score: {opp['priority_score']}")

        return {"status": "success", "improvement_opportunities": opportunities_with_scores}

    def _scan_codebase_for_improvements(self) -> List[Dict[str, object]]:
        """Scan existing codebase for real improvement opportunities."""
        from pathlib import Path

        opportunities = []

        # Scan Python files for common improvement patterns
        for py_file in Path(self.output_dir).rglob("*.py"):
            if any(part in str(py_file) for part in [".venv", "__pycache__", ".git"]):
                continue

            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # Look for meta-programming agent improvements
                if "TODO" in content or "FIXME" in content:
                    opportunities.append(
                        {
                            "type": "code_quality",
                            "file": str(py_file),
                            "description": f"Address TODO/FIXME comments in {py_file.name}",
                            "severity": "medium",
                            "effort": "low",
                        }
                    )

                if len(content.splitlines()) > 500:
                    opportunities.append(
                        {
                            "type": "refactoring",
                            "file": str(py_file),
                            "description": f"Large file {py_file.name} may need refactoring",
                            "severity": "medium",
                            "effort": "high",
                        }
                    )

                if "class" in content and '"""' not in content:
                    opportunities.append(
                        {
                            "type": "documentation",
                            "file": str(py_file),
                            "description": f"Missing docstrings in {py_file.name}",
                            "severity": "low",
                            "effort": "low",
                        }
                    )

            except Exception as e:
                logger.warning(f"Could not analyze {py_file}: {e}")

        return opportunities
