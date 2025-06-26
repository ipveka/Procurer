from typing import Any, Dict
from .base import BaseSolver

class HeuristicSolver(BaseSolver):
    """
    Heuristic solver (greedy + local search) for procurement optimization.
    Fast, but not always optimal. Good for large or time-constrained problems.
    """
    def solve(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Greedy heuristic:
        1. For each period, for each product, fulfill demand from inventory first.
        2. If more is needed, buy from the cheapest supplier, respecting MOQ and supplier minimum order value.
        3. Update inventory after each period.
        4. Repeat for all periods and products.
        Args:
            data: Dictionary with lists of Pydantic models for products, suppliers, demand, inventory, logistics_cost.
        Returns:
            Dictionary with procurement and inventory plan.
        """
        products = data['products']
        suppliers = data['suppliers']
        demand = data['demand']
        inventory = data['inventory']
        logistics_cost = data['logistics_cost']

        product_map = {p.id: p for p in products}
        supplier_map = {s.id: s for s in suppliers}
        inventory_map = {i.product_id: i for i in inventory}
        logistics_map = {(l.supplier_id, l.product_id): l for l in logistics_cost}
        periods = sorted(set(d.period for d in demand))
        demand_map = {(d.product_id, d.period): d.expected_quantity for d in demand}

        procurement_plan = {}
        inventory_plan = {}
        inv = {i.product_id: i.initial_stock for i in inventory}
        for t in periods:
            for p in products:
                demand_qty = demand_map.get((p.id, t), 0)
                # Use inventory first
                used_from_inv = min(inv[p.id], demand_qty)
                inv[p.id] -= used_from_inv
                remaining = demand_qty - used_from_inv
                # Greedy: buy from cheapest supplier(s)
                if remaining > 0:
                    offers = [(s.id, p.unit_cost_by_supplier.get(s.id, float('inf')))
                              for s in suppliers if p.id in s.products_offered]
                    offers = sorted(offers, key=lambda x: x[1])
                    for s_id, unit_cost in offers:
                        if unit_cost == float('inf'):
                            continue
                        if remaining < p.MOQ:
                            continue  # Do not order if below MOQ
                        order_qty = max(remaining, p.MOQ)
                        min_order_value = supplier_map[s_id].minimum_order_value
                        if order_qty * unit_cost < min_order_value:
                            order_qty = int(-(-min_order_value // unit_cost))  # ceil
                        procurement_plan[(p.id, s_id, t)] = order_qty
                        inv[p.id] += order_qty - remaining
                        remaining = 0
                        break
                # Enforce safety stock: if inventory below safety_stock, buy more (even if no demand)
                safety_stock = inventory_map[p.id].safety_stock
                if inv[p.id] < safety_stock:
                    deficit = safety_stock - inv[p.id]
                    offers = [(s.id, p.unit_cost_by_supplier.get(s.id, float('inf')))
                              for s in suppliers if p.id in s.products_offered]
                    offers = sorted(offers, key=lambda x: x[1])
                    for s_id, unit_cost in offers:
                        if unit_cost == float('inf'):
                            continue
                        if deficit < p.MOQ:
                            continue  # Do not order if below MOQ
                        order_qty = max(deficit, p.MOQ)
                        min_order_value = supplier_map[s_id].minimum_order_value
                        if order_qty * unit_cost < min_order_value:
                            order_qty = int(-(-min_order_value // unit_cost))
                        procurement_plan[(p.id, s_id, t)] = procurement_plan.get((p.id, s_id, t), 0) + order_qty
                        inv[p.id] += order_qty
                        break
                inventory_plan[(p.id, t)] = inv[p.id]
        solution = {
            'status': 'heuristic',
            'procurement_plan': {k: v for k, v in procurement_plan.items() if v > 0},
            'inventory': dict(inventory_plan)
        }
        return solution 