import matplotlib.pyplot as plt
from collections import defaultdict
from typing import Dict, Tuple, Any

# visualization.py: Functions for generating plots and visualizations for supply chain analysis.
# Includes demand vs. supply, inventory levels, and procurement plan plots for reporting and the app.
# All visualization logic is documented for clarity and maintainability.

def plot_procurement_plan(procurement_plan: Dict[Tuple[str, str, int], float]):
    """
    Plot procurement quantities by product, supplier, and period.
    Step-by-step:
    1. Create a new matplotlib figure with a fixed size for clarity in Streamlit.
    2. Aggregate procurement quantities by (product, supplier) and period.
    3. For each (product, supplier) pair, plot the procurement quantities over periods.
    4. Add axis labels, title, legend, and layout adjustments for readability.
    """
    plt.figure(figsize=(5, 3))
    data = defaultdict(lambda: defaultdict(float))
    # Aggregate procurement quantities by (product, supplier) and period
    for (product, supplier, period), qty in procurement_plan.items():
        data[(product, supplier)][period] += qty
    # Plot each (product, supplier) procurement plan
    for (product, supplier), period_qty in data.items():
        periods = sorted(period_qty.keys())
        quantities = [period_qty[p] for p in periods]
        plt.plot(periods, quantities, marker='o', label=f'{product}-{supplier}')
    plt.xlabel('Period')
    plt.ylabel('Procurement Quantity')
    plt.title('Procurement Plan')
    plt.legend(fontsize='x-small')
    plt.tight_layout()
    # plt.show()  # Not needed for Streamlit

def plot_inventory_levels(inventory: Dict[Tuple[str, int], float]):
    """
    Plot inventory levels by product and period.
    Step-by-step:
    1. Create a new matplotlib figure with a fixed size.
    2. Aggregate inventory levels by product and period.
    3. For each product, plot inventory levels over periods.
    4. Add axis labels, title, legend, and layout adjustments.
    """
    plt.figure(figsize=(5, 3))
    data = defaultdict(lambda: defaultdict(float))
    # Aggregate inventory by product and period
    for (product, period), qty in inventory.items():
        data[product][period] += qty
    # Plot each product's inventory levels
    for product, period_qty in data.items():
        periods = sorted(period_qty.keys())
        quantities = [period_qty[p] for p in periods]
        plt.plot(periods, quantities, marker='o', label=product)
    plt.xlabel('Period')
    plt.ylabel('Inventory Level')
    plt.title('Inventory Levels')
    plt.legend(fontsize='x-small')
    plt.tight_layout()
    # plt.show()  # Not needed for Streamlit

def plot_demand_vs_supply(demand: Any, procurement_plan: Dict[Tuple[str, str, int], float]):
    """
    Plot demand vs. total supply for each product and period.
    Step-by-step:
    1. Create a new matplotlib figure with a fixed size.
    2. Aggregate demand by (product, period).
    3. Aggregate supply (procurement) by (product, period).
    4. For each product, plot both demand and supply over periods for comparison.
    5. Add axis labels, title, legend, and layout adjustments.
    """
    plt.figure(figsize=(5, 3))
    demand_map = defaultdict(float)
    # Aggregate demand by (product, period)
    for d in demand:
        demand_map[(d.product_id, d.period)] += d.expected_quantity
    supply_map = defaultdict(float)
    # Aggregate supply by (product, period)
    for (product, supplier, period), qty in procurement_plan.items():
        supply_map[(product, period)] += qty
    products = sorted(set(p for p, _ in demand_map.keys()))
    periods = sorted(set(t for _, t in demand_map.keys()))
    # Plot demand and supply for each product
    for product in products:
        d_vals = [demand_map[(product, t)] for t in periods]
        s_vals = [supply_map[(product, t)] for t in periods]
        plt.plot(periods, d_vals, label=f'Demand {product}', linestyle='--')
        plt.plot(periods, s_vals, label=f'Supply {product}', marker='o')
    plt.xlabel('Period')
    plt.ylabel('Quantity')
    plt.title('Demand vs. Supply')
    plt.legend(fontsize='x-small')
    plt.tight_layout()
    # plt.show()  # Not needed for Streamlit 