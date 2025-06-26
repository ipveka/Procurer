from typing import Any, Dict, List, Tuple
from .base import BaseSolver
import pyomo.environ as pyo

class NonlinearSolver(BaseSolver):
    """
    NonlinearSolver for Procurement Optimization with Quantity Discounts.
    Uses Pyomo and IPOPT to solve a true nonlinear program (NLP) with piecewise cost functions for quantity discounts.
    This solver is compared to the linear (MILP) and heuristic solvers in the documentation and reports.
    """
    def solve(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Solve the procurement optimization problem using nonlinear programming (NLP) with quantity discounts.
        Args:
            data: Dictionary with lists of Pydantic models for products, suppliers, demand, inventory, logistics_cost.
        Returns:
            Dictionary with solution details (status, objective, procurement_plan, inventory).
        """
        # Step 1: Prepare data and lookup tables
        (
            product_ids, supplier_ids, periods,
            product_map, supplier_map, demand_map, inventory_map, logistics_map, lead_time_map
        ) = self._prepare_lookups(data)

        # Step 2: Build Pyomo model
        m = self._build_model(product_ids, supplier_ids, periods, product_map, inventory_map, logistics_map, demand_map, lead_time_map)

        # Step 3: Solve the model
        solver = pyo.SolverFactory('ipopt')
        result = solver.solve(m, tee=False)

        # Step 4: Extract and return solution
        return self._extract_solution(m, result, product_ids, supplier_ids, periods, lead_time_map)

    def _prepare_lookups(self, data: Dict[str, Any]) -> Tuple[List[str], List[str], List[int], Dict, Dict, Dict, Dict, Dict, Dict]:
        """Build lookup tables for fast access."""
        products = data['products']
        suppliers = data['suppliers']
        demand = data['demand']
        inventory = data['inventory']
        logistics_cost = data['logistics_cost']
        product_ids = [p.id for p in products]
        supplier_ids = [s.id for s in suppliers]
        periods = sorted(set(d.period for d in demand))
        product_map = {p.id: p for p in products}
        supplier_map = {s.id: s for s in suppliers}
        demand_map = {(d.product_id, d.period): d.expected_quantity for d in demand}
        inventory_map = {i.product_id: i for i in inventory}
        logistics_map = {(l.supplier_id, l.product_id): l for l in logistics_cost}
        # Lead time lookup: (supplier_id, product_id) -> lead_time
        lead_time_map = {(s.id, p.id): s.lead_times.get(p.id, 0) for s in suppliers for p in products}
        return product_ids, supplier_ids, periods, product_map, supplier_map, demand_map, inventory_map, logistics_map, lead_time_map

    def _build_model(self, product_ids, supplier_ids, periods, product_map, inventory_map, logistics_map, demand_map, lead_time_map):
        """Build the Pyomo model, variables, objective, and constraints."""
        m = pyo.ConcreteModel()  # type: ignore[attr-defined]
        m.P = pyo.Set(initialize=product_ids)  # type: ignore[attr-defined]
        m.S = pyo.Set(initialize=supplier_ids)  # type: ignore[attr-defined]
        m.T = pyo.Set(initialize=periods)  # type: ignore[attr-defined]
        m.procure = pyo.Var(m.P, m.S, m.T, domain=pyo.NonNegativeReals)  # type: ignore[attr-defined]
        m.inv = pyo.Var(m.P, m.T, domain=pyo.NonNegativeReals)  # type: ignore[attr-defined]

        # Objective function with nonlinear discount logic
        def procurement_cost_rule(m):
            total = 0.0
            for i in m.P:
                p = product_map[i]
                for j in m.S:
                    for t in m.T:
                        qty = m.procure[i, j, t]
                        unit_cost = p.unit_cost_by_supplier.get(j, 1e6)
                        discount = 0.0
                        threshold = 0
                        if p.discounts:
                            threshold = int(p.discounts.get('threshold', 0))
                            discount = float(p.discounts.get('discount', 0.0))
                        expr = pyo.Expr_if(qty <= threshold,
                                           qty * unit_cost,
                                           threshold * unit_cost + (qty - threshold) * unit_cost * (1 - discount))
                        if expr is not None:
                            total = total + expr
            return total

        def logistics_cost_rule(m):
            total = 0.0
            for i in m.P:
                for j in m.S:
                    for t in m.T:
                        l = logistics_map.get((j, i), None)
                        if l:
                            total = total + m.procure[i, j, t] * l.cost_per_unit
            return total

        def holding_cost_rule(m):
            total = 0.0
            for i in m.P:
                for t in m.T:
                    total = total + m.inv[i, t] * inventory_map[i].holding_cost
            return total

        m.obj = pyo.Objective(expr=procurement_cost_rule(m) + logistics_cost_rule(m) + holding_cost_rule(m), sense=pyo.minimize)  # type: ignore[attr-defined]

        # Constraints
        def inventory_balance_rule(m, i, t):
            if t == periods[0]:
                # For first period, only consider shipments that arrive in time (lead_time = 0)
                shipments = sum(m.procure[i, j, t] for j in m.S if lead_time_map.get((j, i), 0) == 0)
                return (inventory_map[i].initial_stock + shipments - demand_map.get((i, t), 0) == m.inv[i, t])
            else:
                # For subsequent periods, consider shipments from orders placed earlier
                prev_t = periods[periods.index(t)-1]
                shipments = sum(
                    m.procure[i, j, order_period] 
                    for j in m.S 
                    for order_period in periods 
                    if order_period + lead_time_map.get((j, i), 0) == t
                )
                return (m.inv[i, prev_t] + shipments - demand_map.get((i, t), 0) == m.inv[i, t])
        m.inventory_balance = pyo.Constraint(m.P, m.T, rule=inventory_balance_rule)  # type: ignore[attr-defined]

        def warehouse_cap_rule(m, i, t):
            return m.inv[i, t] <= inventory_map[i].warehouse_capacity
        m.warehouse_cap = pyo.Constraint(m.P, m.T, rule=warehouse_cap_rule)  # type: ignore[attr-defined]

        def safety_stock_rule(m, i, t):
            return m.inv[i, t] >= inventory_map[i].safety_stock
        m.safety_stock = pyo.Constraint(m.P, m.T, rule=safety_stock_rule)  # type: ignore[attr-defined]

        def shelf_life_rule(m, i, t):
            p = product_map[i]
            if t > periods[0] + p.expiration_periods:
                return m.inv[i, t] == 0
            return pyo.Constraint.Skip
        m.shelf_life = pyo.Constraint(m.P, m.T, rule=shelf_life_rule)  # type: ignore[attr-defined]

        def moq_rule(m, i, j, t):
            return pyo.inequality(0, m.procure[i, j, t], None) if product_map[i].MOQ == 0 else pyo.inequality(0, m.procure[i, j, t])
        m.moq = pyo.Constraint(m.P, m.S, m.T, rule=moq_rule)  # type: ignore[attr-defined]

        return m

    def _extract_solution(self, m, result, product_ids, supplier_ids, periods, lead_time_map):
        """Extract the solution from the solved Pyomo model."""
        procurement_plan = {}
        shipments_plan = {}
        inventory_plan = {}
        
        # Extract procurement plan (when orders are placed)
        for i in product_ids:
            for j in supplier_ids:
                for t in periods:
                    qty = pyo.value(m.procure[i, j, t])
                    if qty and qty > 0:
                        procurement_plan[(i, j, t)] = qty
                        
                        # Calculate when this order will arrive (shipment)
                        lead_time = lead_time_map.get((j, i), 0)
                        arrival_period = t + lead_time
                        if arrival_period in periods:
                            shipments_plan[(i, j, arrival_period)] = shipments_plan.get((i, j, arrival_period), 0) + qty
        
        # Extract inventory plan
        for i in product_ids:
            for t in periods:
                inv_qty = pyo.value(m.inv[i, t])
                if inv_qty is not None:
                    inventory_plan[(i, t)] = inv_qty
        
        # Generate complete procurement plan with all combinations
        complete_procurement_plan = self._complete_procurement_plan(procurement_plan, product_ids, supplier_ids, periods)
        
        solution = {
            'status': str(result.solver.status),
            'objective': pyo.value(m.obj),
            'procurement_plan': complete_procurement_plan,
            'shipments_plan': shipments_plan,
            'inventory': inventory_plan
        }
        return solution 