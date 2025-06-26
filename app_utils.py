import os
import pandas as pd
from typing import Dict, Any, List, Optional
from utils.data_loader import load_all_data
from utils.validation import validate_data
from utils.metrics import calculate_kpis
from utils.visualization import plot_procurement_plan, plot_inventory_levels, plot_demand_vs_supply
from solvers.linear import LinearSolver
from solvers.heuristic import HeuristicSolver
from solvers.nonlinear import NonlinearSolver
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

DATA_DIR = 'data'

# --- Data Loading ---
def get_data_paths(data_dir: str = DATA_DIR) -> Dict[str, str]:
    """
    Construct a dictionary of file paths for all required data files.
    Args:
        data_dir: Directory where data files are stored.
    Returns:
        Dictionary mapping data type to file path.
    """
    return {
        'products': os.path.join(data_dir, 'products.json'),
        'suppliers': os.path.join(data_dir, 'suppliers.json'),
        'demand': os.path.join(data_dir, 'demand.json'),
        'inventory': os.path.join(data_dir, 'inventory.json'),
        'logistics_cost': os.path.join(data_dir, 'logistics_cost.json'),
    }

def load_and_validate_data(data_dir: str = DATA_DIR) -> Dict[str, Any]:
    """
    Load all data from disk and validate it for consistency and completeness.
    Args:
        data_dir: Directory where data files are stored.
    Returns:
        Dictionary with validated data lists for products, suppliers, demand, inventory, logistics_cost.
    """
    paths = get_data_paths(data_dir)
    data = load_all_data(paths)
    validate_data(data)
    return data

# --- Solver Execution ---
def run_solver(solver_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the selected solver on the provided data.
    Args:
        solver_name: Name of the solver ('linear', 'heuristic', 'nonlinear').
        data: Dictionary with validated input data.
    Returns:
        Dictionary with the solver's solution (procurement plan, inventory, etc.).
    """
    if solver_name == 'linear':
        solver = LinearSolver()
    elif solver_name == 'heuristic':
        solver = HeuristicSolver()
    elif solver_name == 'nonlinear':
        solver = NonlinearSolver()
    else:
        raise ValueError(f"Unknown solver: {solver_name}")
    return solver.solve(data)

# --- KPI Calculation ---
def get_kpis(solution: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, float]:
    """
    Calculate KPIs for a given solution and input data.
    Args:
        solution: Output from a solver (procurement plan, inventory, etc.).
        data: Input data used for the solution.
    Returns:
        Dictionary of KPI names and values.
    """
    return calculate_kpis(solution, data)

# --- Visualization Utilities ---
def get_procurement_plot(procurement_plan: Dict, title: str = '', products_to_plot: Optional[List[str]] = None, moqs=None) -> Figure:
    """
    Generate a matplotlib Figure for the procurement plan.
    Args:
        procurement_plan: Dictionary of procurement quantities by (product, supplier, period).
        title: Optional plot title.
        products_to_plot: Optional list of product IDs to include.
        moqs: Optional MOQ data for annotation.
    Returns:
        Matplotlib Figure object.
    """
    plot_procurement_plan(procurement_plan)
    return plt.gcf()

def get_inventory_plot(inventory: Dict, title: str = '', products_to_plot: Optional[List[str]] = None, safety_stocks=None) -> Figure:
    """
    Generate a matplotlib Figure for inventory levels.
    Args:
        inventory: Dictionary of inventory levels by (product, period).
        title: Optional plot title.
        products_to_plot: Optional list of product IDs to include.
        safety_stocks: Optional safety stock data for annotation.
    Returns:
        Matplotlib Figure object.
    """
    plot_inventory_levels(inventory)
    return plt.gcf()

def get_demand_vs_supply_plot(demand: List[Any], procurement_plan: Dict, title: str = '', products_to_plot: Optional[List[str]] = None) -> Figure:
    """
    Generate a matplotlib Figure comparing demand and supply.
    Args:
        demand: List of demand records.
        procurement_plan: Dictionary of procurement quantities by (product, supplier, period).
        title: Optional plot title.
        products_to_plot: Optional list of product IDs to include.
    Returns:
        Matplotlib Figure object.
    """
    plot_demand_vs_supply(demand, procurement_plan)
    return plt.gcf()

# --- Filtering Utilities ---
def filter_products(data: Dict[str, Any], product_ids: List[str]) -> Dict[str, Any]:
    """
    Filter all data to only include the specified product IDs.
    Args:
        data: Full input data dictionary.
        product_ids: List of product IDs to keep.
    Returns:
        Filtered data dictionary.
    """
    filtered = data.copy()
    filtered['products'] = [p for p in data['products'] if p.id in product_ids]
    filtered['demand'] = [d for d in data['demand'] if d.product_id in product_ids]
    filtered['inventory'] = [i for i in data['inventory'] if i.product_id in product_ids]
    filtered['logistics_cost'] = [l for l in data['logistics_cost'] if l.product_id in product_ids]
    return filtered

def filter_periods(data: Dict[str, Any], periods: List[int]) -> Dict[str, Any]:
    """
    Filter all data to only include the specified periods.
    Args:
        data: Full input data dictionary.
        periods: List of periods to keep.
    Returns:
        Filtered data dictionary.
    """
    filtered = data.copy()
    filtered['demand'] = [d for d in data['demand'] if d.period in periods]
    filtered['inventory'] = [i for i in data['inventory'] if hasattr(i, 'period') and i.period in periods]
    return filtered

# --- Utility to get available products, suppliers, periods ---
def get_available_products(data: Dict[str, Any]) -> List[str]:
    """
    Return a list of all product IDs in the data.
    """
    return [p.id for p in data['products']]

def get_available_suppliers(data: Dict[str, Any]) -> List[str]:
    """
    Return a list of all supplier IDs in the data.
    """
    return [s.id for s in data['suppliers']]

def get_available_periods(data: Dict[str, Any]) -> List[int]:
    """
    Return a sorted list of all periods in the demand data.
    """
    return sorted(set(d.period for d in data['demand'])) 