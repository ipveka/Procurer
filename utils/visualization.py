import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from collections import defaultdict
from typing import Dict, Tuple, Any, List

# visualization.py: Functions for generating plots and visualizations for supply chain analysis.
# Includes demand vs. supply, inventory levels, procurement plan, and shipments plan plots for reporting and the app.
# All visualization logic is documented for clarity and maintainability.

# Standard plot configuration for consistency
PLOT_FIGSIZE = (8, 6)
PLOT_FONTSIZE = 12
LEGEND_FONTSIZE = 10
GRID_ALPHA = 0.7
GRID_LINESTYLE = '--'

def _apply_standard_plot_style(fig, title, xlabel, ylabel):
    """
    Apply standard styling to all plots for consistency.
    """
    ax = plt.gca()
    ax.set_xlabel(xlabel, fontsize=PLOT_FONTSIZE)
    ax.set_ylabel(ylabel, fontsize=PLOT_FONTSIZE)
    ax.set_title(title, fontsize=PLOT_FONTSIZE + 2, fontweight='bold')
    ax.grid(True, linestyle=GRID_LINESTYLE, alpha=GRID_ALPHA)
    ax.set_ylim(bottom=0)  # Ensure y-axis starts at 0
    ax.legend(fontsize=LEGEND_FONTSIZE)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    plt.tight_layout()
    return fig

def plot_procurement_plan(procurement_plan: Dict[Tuple[str, str, int], float]):
    """
    Plot procurement quantities by product, supplier, and period (when orders are placed).
    Step-by-step:
    1. Create a new matplotlib figure with standardized size for consistency.
    2. Aggregate procurement quantities by (product, supplier) and period.
    3. For each (product, supplier) pair, plot the procurement quantities over periods.
    4. Apply standard styling for consistency across all plots.
    5. Ensure y-axis starts at 0 for better visualization.
    """
    plt.figure(figsize=PLOT_FIGSIZE)
    data = defaultdict(lambda: defaultdict(float))
    # Aggregate procurement quantities by (product, supplier) and period
    for (product, supplier, period), qty in procurement_plan.items():
        data[(product, supplier)][period] += qty
    # Plot each (product, supplier) procurement plan
    for (product, supplier), period_qty in data.items():
        periods = sorted(period_qty.keys())
        quantities = [period_qty[p] for p in periods]
        plt.plot(periods, quantities, marker='o', linewidth=2, markersize=6, label=f'{product}-{supplier}')
    
    return _apply_standard_plot_style(
        plt.gcf(),
        'Procurement Plan (Orders Placed)',
        'Period',
        'Procurement Quantity'
    )

def plot_shipments_plan(shipments_plan: Dict[Tuple[str, str, int], float]):
    """
    Plot shipments quantities by product, supplier, and period (when orders arrive).
    Step-by-step:
    1. Create a new matplotlib figure with standardized size for consistency.
    2. Aggregate shipments quantities by (product, supplier) and period.
    3. For each (product, supplier) pair, plot the shipments quantities over periods.
    4. Apply standard styling for consistency across all plots.
    5. Ensure y-axis starts at 0 for better visualization.
    """
    plt.figure(figsize=PLOT_FIGSIZE)
    data = defaultdict(lambda: defaultdict(float))
    # Aggregate shipments quantities by (product, supplier) and period
    for (product, supplier, period), qty in shipments_plan.items():
        data[(product, supplier)][period] += qty
    # Plot each (product, supplier) shipments plan
    for (product, supplier), period_qty in data.items():
        periods = sorted(period_qty.keys())
        quantities = [period_qty[p] for p in periods]
        plt.plot(periods, quantities, marker='s', linewidth=2, markersize=6, label=f'{product}-{supplier}')
    
    return _apply_standard_plot_style(
        plt.gcf(),
        'Shipments Plan (Orders Received)',
        'Period',
        'Shipments Quantity'
    )

def plot_inventory_levels(inventory: Dict[Tuple[str, int], float]):
    """
    Plot inventory levels by product and period.
    Step-by-step:
    1. Create a new matplotlib figure with standardized size for consistency.
    2. Aggregate inventory levels by product and period.
    3. For each product, plot inventory levels over periods.
    4. Apply standard styling for consistency across all plots.
    5. Ensure y-axis starts at 0 for better visualization.
    """
    plt.figure(figsize=PLOT_FIGSIZE)
    data = defaultdict(lambda: defaultdict(float))
    # Aggregate inventory by product and period
    for (product, period), qty in inventory.items():
        data[product][period] += qty
    # Plot each product's inventory levels
    for product, period_qty in data.items():
        periods = sorted(period_qty.keys())
        quantities = [period_qty[p] for p in periods]
        plt.plot(periods, quantities, marker='o', linewidth=2, markersize=6, label=product)
    
    return _apply_standard_plot_style(
        plt.gcf(),
        'Inventory Levels',
        'Period',
        'Inventory Level'
    )

def plot_demand_vs_supply(demand: List[Any], shipments_plan: Dict[Tuple[str, str, int], float]):
    """
    Plot demand vs. total supply (shipments) for each product and period.
    Step-by-step:
    1. Create a new matplotlib figure with standardized size for consistency.
    2. Aggregate demand by (product, period).
    3. Aggregate supply (shipments) by (product, period).
    4. For each product, plot both demand and supply over periods for comparison.
    5. Apply standard styling for consistency across all plots.
    6. Ensure y-axis starts at 0 for better visualization.
    """
    plt.figure(figsize=PLOT_FIGSIZE)
    demand_map = defaultdict(float)
    # Aggregate demand by (product, period)
    for d in demand:
        demand_map[(d.product_id, d.period)] += d.expected_quantity
    supply_map = defaultdict(float)
    # Aggregate supply (shipments) by (product, period)
    for (product, supplier, period), qty in shipments_plan.items():
        supply_map[(product, period)] += qty
    products = sorted(set(p for p, _ in demand_map.keys()))
    periods = sorted(set(t for _, t in demand_map.keys()))
    # Plot demand and supply for each product
    for product in products:
        d_vals = [demand_map[(product, t)] for t in periods]
        s_vals = [supply_map[(product, t)] for t in periods]
        plt.plot(periods, d_vals, marker='o', linewidth=2, markersize=6, linestyle='--', label=f'Demand {product}')
        plt.plot(periods, s_vals, marker='s', linewidth=2, markersize=6, label=f'Supply {product}')
    
    return _apply_standard_plot_style(
        plt.gcf(),
        'Demand vs. Supply (Shipments)',
        'Period',
        'Quantity'
    ) 