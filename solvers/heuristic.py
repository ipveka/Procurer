from typing import Any, Dict, List, Tuple
from .base import BaseSolver

class HeuristicSolver(BaseSolver):
    """
    Heuristic solver for procurement optimization.
    Projects inventory forward using demand forecast and orders MOQ from cheapest supplier when projected inventory falls below safety stock.
    Fast, interpretable, and follows a simple rule-based approach.
    """
    def solve(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Heuristic procurement planning based on inventory projection with lead times.
        For each period, project inventory to period+1 considering shipments that will arrive.
        If projected inventory falls below safety stock, order MOQ from cheapest supplier.
        Args:
            data: Dictionary with lists of Pydantic models for products, suppliers, demand, inventory, logistics_cost.
        Returns:
            Dictionary with procurement and inventory plan.
        """
        # Step 1: Prepare data and lookup tables
        (
            products, suppliers, demand, inventory, logistics_cost,
            product_map, supplier_map, inventory_map, periods, demand_map, lead_time_map
        ) = self._prepare_lookups(data)

        procurement_plan = {}
        shipments_plan = {}
        inventory_plan = {}
        # Initialize inventory for each product
        inv = {i.product_id: i.initial_stock for i in inventory}
        # Track pending shipments (orders placed but not yet arrived)
        pending_shipments = {i.product_id: {} for i in inventory}
        
        for t in periods:
            for p in products:
                # Add shipments that arrive in this period
                if t in pending_shipments[p.id]:
                    inv[p.id] += pending_shipments[p.id][t]
                    del pending_shipments[p.id][t]
                
                # Calculate projected inventory at period+1 considering pending shipments
                projected_inventory = self._project_inventory_with_lead_times(p.id, t, inv[p.id], demand_map, periods, pending_shipments[p.id])
                safety_stock = inventory_map[p.id].safety_stock
                
                # If projected inventory falls below safety stock, order MOQ from cheapest supplier
                if projected_inventory < safety_stock:
                    s_id, order_qty = self._order_moq_from_cheapest(p, suppliers)
                    if s_id is not None:
                        procurement_plan[(p.id, s_id, t)] = order_qty
                        
                        # Calculate when this order will arrive and add to pending shipments
                        lead_time = lead_time_map.get((s_id, p.id), 0)
                        arrival_period = t + lead_time
                        if arrival_period in periods:
                            pending_shipments[p.id][arrival_period] = pending_shipments[p.id].get(arrival_period, 0) + order_qty
                            shipments_plan[(p.id, s_id, arrival_period)] = shipments_plan.get((p.id, s_id, arrival_period), 0) + order_qty
                
                # Apply demand for current period
                demand_qty = demand_map.get((p.id, t), 0)
                inv[p.id] = max(0, inv[p.id] - demand_qty)
                
                # Record inventory at end of period
                inventory_plan[(p.id, t)] = inv[p.id]
        
        solution = {
            'status': 'heuristic',
            'procurement_plan': self._complete_procurement_plan(procurement_plan, [p.id for p in products], [s.id for s in suppliers], periods),
            'shipments_plan': {k: v for k, v in shipments_plan.items() if v > 0},
            'inventory': dict(inventory_plan)
        }
        return solution

    def _prepare_lookups(self, data: Dict[str, Any]) -> Tuple:
        """Build lookup tables for fast access."""
        products = data['products']
        suppliers = data['suppliers']
        demand = data['demand']
        inventory = data['inventory']
        logistics_cost = data['logistics_cost']
        product_map = {p.id: p for p in products}
        supplier_map = {s.id: s for s in suppliers}
        inventory_map = {i.product_id: i for i in inventory}
        periods = sorted(set(d.period for d in demand))
        demand_map = {(d.product_id, d.period): d.expected_quantity for d in demand}
        # Lead time lookup: (supplier_id, product_id) -> lead_time
        lead_time_map = {(s.id, p.id): s.lead_times.get(p.id, 0) for s in suppliers for p in products}
        return products, suppliers, demand, inventory, logistics_cost, product_map, supplier_map, inventory_map, periods, demand_map, lead_time_map

    def _project_inventory_with_lead_times(self, product_id: str, current_period: int, current_inventory: float, demand_map: Dict, periods: List[int], pending_shipments: Dict) -> float:
        """Project inventory to period+1 using demand forecast and pending shipments."""
        # Find the next period
        current_idx = periods.index(current_period)
        if current_idx + 1 >= len(periods):
            # If this is the last period, return current inventory
            return current_inventory
        
        next_period = periods[current_idx + 1]
        next_demand = demand_map.get((product_id, next_period), 0)
        
        # Add shipments that will arrive before next period
        shipments_arriving = sum(qty for arrival_period, qty in pending_shipments.items() 
                               if arrival_period <= next_period)
        
        # Projected inventory = current inventory + shipments arriving - next period demand
        projected = current_inventory + shipments_arriving - next_demand
        return max(0, projected)  # Inventory cannot be negative

    def _order_moq_from_cheapest(self, p, suppliers) -> Tuple[Any, Any]:
        """Order MOQ from the cheapest available supplier."""
        offers = [(s.id, p.unit_cost_by_supplier.get(s.id, float('inf')))
                  for s in suppliers if p.id in s.products_offered]
        offers = sorted(offers, key=lambda x: x[1])  # Sort by cost (cheapest first)
        
        for s_id, unit_cost in offers:
            if unit_cost == float('inf'):
                continue
            # Order MOQ from this supplier
            return s_id, p.MOQ
        
        return None, None
