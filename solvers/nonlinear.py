from typing import Any, Dict
from .base import BaseSolver
import pyomo.environ as pyo

class NonlinearSolver(BaseSolver):
    """
    NonlinearSolver for Procurement Optimization with Quantity Discounts.
    Uses Pyomo and IPOPT to solve a true nonlinear program (NLP) with piecewise cost functions for quantity discounts.
    This solver is compared to the linear (MILP) and heuristic solvers in the documentation and reports.
    """
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

        m = pyo.ConcreteModel()
        m.P = pyo.Set(initialize=product_ids)
        m.S = pyo.Set(initialize=supplier_ids)
        m.T = pyo.Set(initialize=periods)

        m.procure = pyo.Var(m.P, m.S, m.T, domain=pyo.NonNegativeReals)
        m.inv = pyo.Var(m.P, m.T, domain=pyo.NonNegativeReals)

        def procurement_cost_rule(m):
            total = 0
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
                        # Use Expr_if for nonlinear discount logic
                        total += pyo.Expr_if(qty <= threshold,
                                             qty * unit_cost,
                                             threshold * unit_cost + (qty - threshold) * unit_cost * (1 - discount))
            return total

        def logistics_cost_rule(m):
            total = 0
            for i in m.P:
                for j in m.S:
                    for t in m.T:
                        l = logistics_map.get((j, i), None)
                        if l:
                            total += m.procure[i, j, t] * l.cost_per_unit
            return total

        def holding_cost_rule(m):
            total = 0
            for i in m.P:
                for t in m.T:
                    total += m.inv[i, t] * inventory_map[i].holding_cost
            return total

        m.obj = pyo.Objective(expr=procurement_cost_rule(m) + logistics_cost_rule(m) + holding_cost_rule(m), sense=pyo.minimize)

        # Constraints
        def inventory_balance_rule(m, i, t):
            if t == periods[0]:
                return (inventory_map[i].initial_stock + sum(m.procure[i, j, t] for j in m.S) - demand_map.get((i, t), 0) == m.inv[i, t])
            else:
                prev_t = periods[periods.index(t)-1]
                return (m.inv[i, prev_t] + sum(m.procure[i, j, t] for j in m.S) - demand_map.get((i, t), 0) == m.inv[i, t])
        m.inventory_balance = pyo.Constraint(m.P, m.T, rule=inventory_balance_rule)

        def warehouse_cap_rule(m, i, t):
            return m.inv[i, t] <= inventory_map[i].warehouse_capacity
        m.warehouse_cap = pyo.Constraint(m.P, m.T, rule=warehouse_cap_rule)

        def safety_stock_rule(m, i, t):
            return m.inv[i, t] >= inventory_map[i].safety_stock
        m.safety_stock = pyo.Constraint(m.P, m.T, rule=safety_stock_rule)

        def shelf_life_rule(m, i, t):
            p = product_map[i]
            if t > periods[0] + p.expiration_periods:
                return m.inv[i, t] == 0
            return pyo.Constraint.Skip
        m.shelf_life = pyo.Constraint(m.P, m.T, rule=shelf_life_rule)

        # MOQ constraint: if order > 0, must be at least MOQ (relaxed for NLP)
        def moq_rule(m, i, j, t):
            return pyo.inequality(0, m.procure[i, j, t], None) if product_map[i].MOQ == 0 else pyo.inequality(0, m.procure[i, j, t])
        m.moq = pyo.Constraint(m.P, m.S, m.T, rule=moq_rule)

        solver = pyo.SolverFactory('ipopt')
        result = solver.solve(m, tee=False)

        procurement_plan = {}
        inventory_plan = {}
        for i in product_ids:
            for j in supplier_ids:
                for t in periods:
                    qty = pyo.value(m.procure[i, j, t])
                    if qty and qty > 0:
                        procurement_plan[(i, j, t)] = qty
            for t in periods:
                inv_qty = pyo.value(m.inv[i, t])
                if inv_qty is not None:
                    inventory_plan[(i, t)] = inv_qty
        solution = {
            'status': str(result.solver.status),
            'objective': pyo.value(m.obj),
            'procurement_plan': procurement_plan,
            'inventory': inventory_plan
        }
        return solution 