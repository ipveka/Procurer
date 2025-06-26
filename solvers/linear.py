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
from typing import Any, Dict, List, Tuple
from .base import BaseSolver
from pulp import LpProblem, LpMinimize, LpVariable, lpSum, LpStatus, value, LpInteger, LpBinary

class LinearSolver(BaseSolver):
    def solve(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Solve the procurement optimization problem using MILP.
        Args:
            data: Dictionary with lists of Pydantic models for products, suppliers, demand, inventory, logistics_cost.
        Returns:
            Dictionary with solution details (status, objective, procurement_plan, inventory).
        """
        # Step 1: Prepare data and lookup tables
        (
            product_ids, supplier_ids, periods,
            product_map, supplier_map, demand_map, inventory_map, logistics_map
        ) = self._prepare_lookups(data)

        # Step 2: Create MILP variables
        prob, p_vars, inv_vars, y_vars = self._create_variables(product_ids, supplier_ids, periods)

        # Step 3: Add objective function
        self._add_objective(prob, p_vars, inv_vars, product_ids, supplier_ids, periods, product_map, inventory_map, logistics_map)

        # Step 4: Add constraints
        self._add_constraints(
            prob, p_vars, inv_vars, y_vars,
            product_ids, supplier_ids, periods,
            product_map, inventory_map, demand_map, logistics_map
        )

        # Step 5: Solve the problem
        prob.solve()
        status = LpStatus[prob.status]

        # Step 6: Extract and return solution
        return self._extract_solution(status, prob, p_vars, inv_vars, product_ids, supplier_ids, periods)

    def _prepare_lookups(self, data: Dict[str, Any]) -> Tuple[List[str], List[str], List[int], Dict, Dict, Dict, Dict, Dict]:
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
        return product_ids, supplier_ids, periods, product_map, supplier_map, demand_map, inventory_map, logistics_map

    def _create_variables(self, product_ids, supplier_ids, periods):
        """Create MILP variables for procurement, inventory, and MOQ enforcement."""
        prob = LpProblem("ProcurementOptimization", LpMinimize)
        p_vars = {(i, j, t): LpVariable(f"p_{i}_{j}_{t}", lowBound=0, cat=LpInteger)
                  for i in product_ids for j in supplier_ids for t in periods}
        inv_vars = {(i, t): LpVariable(f"inv_{i}_{t}", lowBound=0, cat=LpInteger)
                    for i in product_ids for t in periods}
        y_vars = {(i, j, t): LpVariable(f"y_{i}_{j}_{t}", cat=LpBinary)
                  for i in product_ids for j in supplier_ids for t in periods}
        return prob, p_vars, inv_vars, y_vars

    def _add_objective(self, prob, p_vars, inv_vars, product_ids, supplier_ids, periods, product_map, inventory_map, logistics_map):
        """Add the objective function to the MILP problem."""
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

    def _add_constraints(self, prob, p_vars, inv_vars, y_vars,
                         product_ids, supplier_ids, periods,
                         product_map, inventory_map, demand_map, logistics_map):
        """Add all constraints to the MILP problem."""
        for i in product_ids:
            for t in periods:
                # Inventory balance constraint
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
                # Warehouse capacity constraint
                prob += inv_vars[i, t] <= inventory_map[i].warehouse_capacity, f"WarehouseCap_{i}_{t}"
                # Safety stock constraint
                prob += inv_vars[i, t] >= inventory_map[i].safety_stock, f"SafetyStock_{i}_{t}"
                # Shelf life constraint (if applicable)
                if product_map[i].expiration_periods is not None and t is not None:
                    expiration_limit = int(periods[0]) + int(product_map[i].expiration_periods)
                    t_int = int(t)
                    if t_int > expiration_limit:
                        prob += inv_vars[i, t] == 0, f"Expiration_{i}_{t}"
            for j in supplier_ids:
                for t in periods:
                    moq = int(product_map[i].MOQ)
                    t_int = int(t)
                    # MOQ lower bound: if order is placed, must be at least MOQ
                    prob += p_vars[i, j, t] >= moq * y_vars[i, j, t], f"MOQ_min_{i}_{j}_{t}"
                    # Big-M upper bound: if no order, quantity is zero
                    bigM = 1e6
                    prob += p_vars[i, j, t] <= bigM * y_vars[i, j, t], f"MOQ_bigM_{i}_{j}_{t}"

    def _extract_solution(self, status, prob, p_vars, inv_vars, product_ids, supplier_ids, periods):
        """Extract the solution from the solved MILP problem."""
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