from solvers.linear import LinearSolver
from solvers.nonlinear import NonlinearSolver
from solvers.heuristic import HeuristicSolver
from models.product import Product
from models.supplier import Supplier
from models.demand import Demand
from models.inventory import Inventory
from models.logistics_cost import LogisticsCost

def minimal_data(discount=False):
    products = [Product(
        id="P1",
        name="Widget",
        unit_cost_by_supplier={"S1": 10.0},
        expiration_periods=12,
        MOQ=5,
        discounts={"threshold": 10, "discount": 0.2} if discount else None
    )]
    suppliers = [Supplier(id="S1", name="SupplierA", products_offered=["P1"], minimum_order_value=10.0, lead_times={"P1": 1})]
    demand = [Demand(product_id="P1", period=1, expected_quantity=20)]
    inventory = [Inventory(product_id="P1", initial_stock=0, holding_cost=0.5, warehouse_capacity=100, safety_stock=0)]
    logistics_cost = [LogisticsCost(supplier_id="S1", product_id="P1", cost_per_unit=2.0, fixed_cost=1.0)]
    return {
        'products': products,
        'suppliers': suppliers,
        'demand': demand,
        'inventory': inventory,
        'logistics_cost': logistics_cost
    }

def test_linear_solver_returns_dict():
    solver = LinearSolver()
    result = solver.solve(minimal_data())
    assert isinstance(result, dict)
    assert 'procurement_plan' in result
    assert 'inventory' in result

def test_nonlinear_solver_discount_applied():
    solver = NonlinearSolver()
    result = solver.solve(minimal_data(discount=True))
    assert isinstance(result, dict)
    assert 'procurement_plan' in result
    assert 'inventory' in result
    # Check that discount is applied for quantity > threshold
    plan = result['procurement_plan']
    qty = next(iter(plan.values()))
    assert qty > 10  # Should order more than threshold
    # The objective should reflect the discount (less than full price * qty)
    assert result['objective'] < qty * 10.0 + qty * 2.0  # unit_cost + logistics_cost

def test_heuristic_solver_returns_dict():
    solver = HeuristicSolver()
    result = solver.solve(minimal_data())
    assert isinstance(result, dict) 