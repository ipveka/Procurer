from typing import Dict, Any

def calculate_kpis(solution: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, float]:
    """
    Calculate KPIs and performance metrics from the solution and input data.
    Returns a dictionary of KPI names and values.
    """
    procurement_plan = solution.get('procurement_plan', {})
    inventory = solution.get('inventory', {})
    demand = data.get('demand', [])
    products = {p.id: p for p in data.get('products', [])}
    total_procurement_cost = 0.0
    total_demand = sum(d.expected_quantity for d in demand)
    total_supplied = 0.0
    for (i, j, t), qty in procurement_plan.items():
        unit_cost = products[i].unit_cost_by_supplier.get(j, 0)
        total_procurement_cost += qty * unit_cost
        total_supplied += qty
    service_level = total_supplied / total_demand if total_demand > 0 else 1.0
    # Inventory turnover: total demand / average inventory
    avg_inventory = sum(inventory.values()) / max(len(inventory), 1)
    inventory_turnover = total_demand / avg_inventory if avg_inventory > 0 else 0.0
    # Obsolescence: units in stock (not sold) for over 4 periods
    obsolescence = 0.0
    periods = sorted(set(d.period for d in demand))
    for i in products:
        for t in periods:
            if t > min(periods) + 4:
                obsolescence += inventory.get((i, t), 0)
    return {
        'total_procurement_cost': total_procurement_cost,
        'service_level': service_level,
        'inventory_turnover': inventory_turnover,
        'obsolescence': obsolescence
    } 