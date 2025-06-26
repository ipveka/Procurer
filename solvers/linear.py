"""
LinearSolver (MILP) for Procurement Optimization

This solver builds a Mixed Integer Linear Programming (MILP) model to minimize total procurement, logistics, and holding costs over multiple periods, products, and suppliers. It enforces demand satisfaction, inventory balance, warehouse capacity, safety stock, shelf life, and MOQ constraints. The solver uses PuLP and CBC.

This solver does NOT handle nonlinear quantity discounts; for that, see NonlinearSolver.

How it works:
- Decision variables: Quantity of each product to buy from each supplier in each period, and inventory at each period end.
- Objective: Minimize total cost (procurement + logistics + holding).
- Constraints: Demand satisfaction, inventory balance, warehouse capacity, shelf life, safety stock, MOQ.
- MOQ is enforced using a binary variable and big-M approach for each product-supplier-period.
- Output: Procurement plan, inventory plan, and objective value.
"""
from typing import Any, Dict
from .base import BaseSolver
from pulp import LpProblem, LpMinimize, LpVariable, lpSum, LpStatus, value, LpInteger, LpBinary

class LinearSolver(BaseSolver):
    def solve(self, data: Dict[str, Any]) -> Dict[str, Any]:
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

        prob = LpProblem("ProcurementOptimization", LpMinimize)
        p_vars = {(i, j, t): LpVariable(f"p_{i}_{j}_{t}", lowBound=0, cat=LpInteger)
                  for i in product_ids for j in supplier_ids for t in periods}
        inv_vars = {(i, t): LpVariable(f"inv_{i}_{t}", lowBound=0, cat=LpInteger)
                    for i in product_ids for t in periods}
        # Binary variables for MOQ enforcement
        y_vars = {(i, j, t): LpVariable(f"y_{i}_{j}_{t}", cat=LpBinary)
                  for i in product_ids for j in supplier_ids for t in periods}

        procurement_cost = lpSum(
            p_vars[i, j, t] * product_map[i].unit_cost_by_supplier.get(j, 1e6)
            for i in product_ids for j in supplier_ids for t in periods
        )
        logistics_cost_total = lpSum(
            p_vars[i, j, t] * logistics_map.get((j, i), type('L', (), {'cost_per_unit': 1e6})).cost_per_unit
            for i in product_ids for j in supplier_ids for t in periods
            if (j, i) in logistics_map
        )
        holding_cost = lpSum(
            inv_vars[i, t] * inventory_map[i].holding_cost
            for i in product_ids for t in periods
        )
        prob += procurement_cost + logistics_cost_total + holding_cost

        for i in product_ids:
            for t in periods:
                if t == periods[0]:
                    prob += (
                        inventory_map[i].initial_stock
                        + lpSum(p_vars[i, j, t] for j in supplier_ids)
                        - demand_map.get((i, t), 0)
                        == inv_vars[i, t]
                    ), f"InventoryBalance_{i}_{t}"
                else:
                    prob += (
                        inv_vars[i, periods[periods.index(t)-1]]
                        + lpSum(p_vars[i, j, t] for j in supplier_ids)
                        - demand_map.get((i, t), 0)
                        == inv_vars[i, t]
                    ), f"InventoryBalance_{i}_{t}"
                prob += inv_vars[i, t] <= inventory_map[i].warehouse_capacity, f"WarehouseCap_{i}_{t}"
                prob += inv_vars[i, t] >= inventory_map[i].safety_stock, f"SafetyStock_{i}_{t}"
                if product_map[i].expiration_periods is not None and t is not None:
                    try:
                        expiration_limit = int(periods[0]) + int(product_map[i].expiration_periods)
                        t_int = int(t)
                        if t_int > expiration_limit:
                            prob += inv_vars[i, t] == 0, f"Expiration_{i}_{t}"
                    except Exception:
                        pass
            for j in supplier_ids:
                for t in periods:
                    try:
                        moq = int(product_map[i].MOQ)
                        t_int = int(t)
                        if moq is not None and t_int is not None:
                            prob += p_vars[i, j, t] >= moq * y_vars[i, j, t], f"MOQ_min_{i}_{j}_{t}"
                            bigM = 1e6
                            prob += p_vars[i, j, t] <= bigM * y_vars[i, j, t], f"MOQ_bigM_{i}_{j}_{t}"
                    except Exception:
                        pass
        
        # Solve the problem
        prob.solve()
        status = LpStatus[prob.status]
        solution = {
            'status': status,
            'objective': value(prob.objective),
            'procurement_plan': {
                (i, j, t): p_vars[i, j, t].varValue
                for i in product_ids for j in supplier_ids for t in periods
                if p_vars[i, j, t].varValue is not None and p_vars[i, j, t].varValue > 0
            },
            'inventory': {
                (i, t): inv_vars[i, t].varValue
                for i in product_ids for t in periods
                if inv_vars[i, t].varValue is not None and inv_vars[i, t].varValue > 0
            }
        }
        return solution 