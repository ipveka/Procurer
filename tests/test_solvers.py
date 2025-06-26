from solvers.linear import LinearSolver
from solvers.nonlinear import NonlinearSolver
from solvers.heuristic import HeuristicSolver
from models.product import Product
from models.supplier import Supplier
from models.demand import Demand
from models.inventory import Inventory
from models.logistics_cost import LogisticsCost

def minimal_data(discount=False):
    """
    Create a minimal valid dataset for testing solvers.
    If discount=True, include a discount policy for the product.
    Returns a dictionary with all required data lists.
    """
    products = [Product(
        id="P1",
        name="Widget",
        unit_cost_by_supplier={"S1": 10.0},
        expiration_periods=12,
        MOQ=5,
        discounts={"threshold": 10, "discount": 0.2} if discount else None
    )]
    suppliers = [Supplier(id="S1", name="SupplierA", products_offered=["P1"], lead_times={"P1": 1})]
    demand = [
        Demand(product_id="P1", period=0, expected_quantity=0),  # No demand in period 0
        Demand(product_id="P1", period=1, expected_quantity=20)  # Demand in period 1
    ]
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
    """
    Test that the LinearSolver returns a dictionary with required keys.
    Ensures the solver runs and produces a valid output structure.
    """
    solver = LinearSolver()
    result = solver.solve(minimal_data())
    assert isinstance(result, dict)
    assert 'procurement_plan' in result
    assert 'shipments_plan' in result
    assert 'inventory' in result

def test_nonlinear_solver_discount_applied():
    """
    Test that the NonlinearSolver applies discounts when quantity exceeds threshold.
    Ensures the solver returns a valid result and the objective reflects the discount.
    """
    solver = NonlinearSolver()
    result = solver.solve(minimal_data(discount=True))
    assert isinstance(result, dict)
    assert 'procurement_plan' in result
    assert 'shipments_plan' in result
    assert 'inventory' in result
    # Check that discount is applied for quantity > threshold
    plan = result['procurement_plan']
    if plan:  # Only check if there are orders
        qty = next(iter(plan.values()))
        assert qty >= 5  # Should order at least MOQ
    # The objective should reflect the discount (less than full price * qty)
    if plan:
        qty = next(iter(plan.values()))
        assert result['objective'] < qty * 10.0 + qty * 2.0  # unit_cost + logistics_cost

def test_heuristic_solver_returns_dict():
    """
    Test that the HeuristicSolver returns a dictionary with required keys.
    Ensures the solver runs and produces a valid output structure.
    """
    solver = HeuristicSolver()
    result = solver.solve(minimal_data())
    assert isinstance(result, dict)
    assert 'procurement_plan' in result
    assert 'shipments_plan' in result
    assert 'inventory' in result 