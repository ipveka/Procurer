import matplotlib.pyplot as plt
from collections import defaultdict
from typing import Dict, Tuple, Any

def plot_procurement_plan(procurement_plan: Dict[Tuple[str, str, int], float]):
    """
    Plot procurement quantities by product, supplier, and period.
    """
    data = defaultdict(lambda: defaultdict(float))
    for (product, supplier, period), qty in procurement_plan.items():
        data[(product, supplier)][period] += qty
    for (product, supplier), period_qty in data.items():
        periods = sorted(period_qty.keys())
        quantities = [period_qty[p] for p in periods]
        plt.plot(periods, quantities, marker='o', label=f'{product}-{supplier}')
    plt.xlabel('Period')
    plt.ylabel('Procurement Quantity')
    plt.title('Procurement Plan')
    plt.legend()
    plt.tight_layout()
    plt.show()

def plot_inventory_levels(inventory: Dict[Tuple[str, int], float]):
    """
    Plot inventory levels by product and period.
    """
    data = defaultdict(lambda: defaultdict(float))
    for (product, period), qty in inventory.items():
        data[product][period] += qty
    for product, period_qty in data.items():
        periods = sorted(period_qty.keys())
        quantities = [period_qty[p] for p in periods]
        plt.plot(periods, quantities, marker='o', label=product)
    plt.xlabel('Period')
    plt.ylabel('Inventory Level')
    plt.title('Inventory Levels')
    plt.legend()
    plt.tight_layout()
    plt.show()

def plot_demand_vs_supply(demand: Any, procurement_plan: Dict[Tuple[str, str, int], float]):
    """
    Plot demand vs. total supply for each product and period.
    """
    from collections import defaultdict
    demand_map = defaultdict(float)
    for d in demand:
        demand_map[(d.product_id, d.period)] += d.expected_quantity
    supply_map = defaultdict(float)
    for (product, supplier, period), qty in procurement_plan.items():
        supply_map[(product, period)] += qty
    products = sorted(set(p for p, _ in demand_map.keys()))
    periods = sorted(set(t for _, t in demand_map.keys()))
    for product in products:
        d_vals = [demand_map[(product, t)] for t in periods]
        s_vals = [supply_map[(product, t)] for t in periods]
        plt.plot(periods, d_vals, label=f'Demand {product}', linestyle='--')
        plt.plot(periods, s_vals, label=f'Supply {product}', marker='o')
    plt.xlabel('Period')
    plt.ylabel('Quantity')
    plt.title('Demand vs. Supply')
    plt.legend()
    plt.tight_layout()
    plt.show() 