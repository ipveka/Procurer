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
from typing import Any, Dict, List, Tuple

class BaseSolver(ABC):
    """
    Base class for all solvers (heuristic, linear, nonlinear). All must implement the solve(data) method.
    The nonlinear solver supports quantity discounts via the 'discounts' field in the product model.
    """
    @abstractmethod
    def solve(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Abstract method to solve the procurement optimization problem.
        Args:
            data: Dictionary containing all required input data.
        Returns:
            Dictionary with solution details (e.g., procurement plan, inventory plan).
        """
        pass

    def _complete_procurement_plan(self, procurement_plan: Dict[Tuple[str, str, int], float], 
                                  product_ids: List[str], supplier_ids: List[str], periods: List[int]) -> Dict[Tuple[str, str, int], float]:
        """
        Generate a complete procurement plan with all combinations (including zeros) ordered by supplier, product, period.
        Args:
            procurement_plan: Dictionary with actual procurement quantities (only non-zero values)
            product_ids: List of product IDs
            supplier_ids: List of supplier IDs  
            periods: List of periods
        Returns:
            Complete procurement plan with all combinations, ordered by supplier, product, period
        """
        complete_plan = {}
        
        # Sort by supplier, product, period as requested
        for supplier in sorted(supplier_ids):
            for product in sorted(product_ids):
                for period in sorted(periods):
                    key = (product, supplier, period)
                    # Use actual value if exists, otherwise 0
                    complete_plan[key] = procurement_plan.get(key, 0.0)
        
        return complete_plan 