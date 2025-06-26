"""
BaseSolver is an abstract base class (interface) for all procurement optimization solvers.

Purpose:
- Defines a standard interface (the `solve` method) that all solvers (exact, heuristic, etc.) must implement.
- Ensures consistency and interchangeability between different solver implementations.
- Not strictly required for a small project, but highly recommended for professional, extensible, and testable codebases.
- Allows you to add new solver types (e.g., metaheuristics, ML-based) without changing the rest of the codebase.

You do not need to instantiate BaseSolver directly. It is only used as a parent class for other solvers.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseSolver(ABC):
    """
    Base class for all solvers (heuristic, linear, nonlinear). All must implement the solve(data) method.
    The nonlinear solver supports quantity discounts via the 'discounts' field in the product model.
    """
    @abstractmethod
    def solve(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Solve the procurement optimization problem.
        Args:
            data: Dictionary containing all required input data.
        Returns:
            Dictionary with solution details.
        """
        pass

class NonlinearSolver(BaseSolver):
    """
    NonlinearSolver for Procurement Optimization with Quantity Discounts.
    This solver handles nonlinear procurement costs due to quantity discounts (e.g., buy > threshold units, get discount on extra units).
    """
    def solve(self, data: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError("NonlinearSolver must be implemented in solvers/nonlinear.py") 