from typing import Dict, Any

# metrics.py: Functions for calculating KPIs and performance metrics for supply chain solutions.
# Includes logic for procurement cost, service level, inventory turnover, and obsolescence.
# All calculations are documented for clarity and maintainability.

def calculate_kpis(solution: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, float]:
    """
    Calculate KPIs and performance metrics from the solution and input data.
    KPIs:
    - total_procurement_cost: Sum of all procurement quantities × unit cost (across all products, suppliers, periods)
    - service_level: Total supplied / total demand (should be 1.0 if all demand is met)
    - inventory_turnover: Total demand / average inventory (higher = more efficient use of stock)
    - obsolescence: Inventory left after 4+ periods (risk of waste; should be low)
    Step-by-step:
    1. Aggregate procurement cost and total supplied from the procurement plan.
    2. Calculate total demand from the demand data.
    3. Compute service level as total supplied / total demand.
    4. Compute average inventory and inventory turnover.
    5. Compute obsolescence as inventory left after 4+ periods.
    Returns a dictionary of KPI names and values.
    """
    procurement_plan = solution.get('procurement_plan', {})
    inventory = solution.get('inventory', {})
    demand = data.get('demand', [])
    products = {p.id: p for p in data.get('products', [])}
    total_procurement_cost = 0.0
    total_demand = sum(d.expected_quantity for d in demand)
    total_supplied = 0.0
    # Step 1: Calculate total procurement cost and total supplied
    for (i, j, t), qty in procurement_plan.items():
        unit_cost = products[i].unit_cost_by_supplier.get(j, 0)
        total_procurement_cost += qty * unit_cost
        total_supplied += qty
    # Step 2: Calculate service level
    service_level = total_supplied / total_demand if total_demand > 0 else 1.0
    # Step 3: Inventory turnover: total demand / average inventory
    avg_inventory = sum(inventory.values()) / max(len(inventory), 1)
    inventory_turnover = total_demand / avg_inventory if avg_inventory > 0 else 0.0
    # Step 4: Obsolescence: inventory that is not sold and keeps accumulating (not sold in demand)
    obsolescence = 0.0
    periods = sorted(set(d.period for d in demand))
    for i in products:
        # Total demand for this product
        total_demand_i = sum(d.expected_quantity for d in demand if d.product_id == i)
        # Inventory left at the end of the last period
        last_period = periods[-1]
        end_inventory = inventory.get((i, last_period), 0)
        # Obsolescence is inventory left that was never sold (not consumed by demand)
        excess = end_inventory - max(0, total_demand_i)
        if excess > 0:
            obsolescence += excess
    return {
        'total_procurement_cost': total_procurement_cost,
        'service_level': service_level,
        'inventory_turnover': inventory_turnover,
        'obsolescence': obsolescence
    } 