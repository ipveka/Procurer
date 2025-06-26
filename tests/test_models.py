from models.product import Product
from models.supplier import Supplier
from models.demand import Demand
from models.inventory import Inventory
from models.logistics_cost import LogisticsCost


def test_product():
    """
    Test creation and field access for the Product model.
    Ensures that the Product model can be instantiated and fields are correct.
    """
    p = Product(id="P1", name="Widget", unit_cost_by_supplier={"S1": 10.0}, expiration_periods=12, MOQ=5, discounts=None)
    assert p.id == "P1"

def test_supplier():
    """
    Test creation and field access for the Supplier model.
    Ensures that the Supplier model can be instantiated and fields are correct.
    """
    s = Supplier(id="S1", name="SupplierA", products_offered=["P1"], lead_times={"P1": 2})
    assert s.id == "S1"
    assert s.name == "SupplierA"
    assert s.products_offered == ["P1"]
    assert s.lead_times == {"P1": 2}

def test_demand():
    """
    Test creation and field access for the Demand model.
    Ensures that the Demand model can be instantiated and fields are correct.
    """
    d = Demand(product_id="P1", period=1, expected_quantity=50)
    assert d.period == 1

def test_inventory():
    """
    Test creation and field access for the Inventory model.
    Ensures that the Inventory model can be instantiated and fields are correct.
    """
    i = Inventory(product_id="P1", initial_stock=100, holding_cost=0.5, warehouse_capacity=1000, safety_stock=0)
    assert i.initial_stock == 100

def test_logistics_cost():
    """
    Test creation and field access for the LogisticsCost model.
    Ensures that the LogisticsCost model can be instantiated and fields are correct.
    """
    l = LogisticsCost(supplier_id="S1", product_id="P1", cost_per_unit=2.0, fixed_cost=50.0)
    assert l.fixed_cost == 50.0

def test_visualization_runs():
    """
    Test that the visualization functions run without error on minimal data.
    This ensures that the plotting utilities do not crash and can handle basic input.
    """
    import matplotlib
    matplotlib.use('Agg')
    from utils.visualization import plot_procurement_plan, plot_inventory_levels, plot_demand_vs_supply
    procurement_plan = {('P1', 'S1', 1): 10.0, ('P1', 'S1', 2): 20.0}
    inventory = {('P1', 1): 5.0, ('P1', 2): 10.0}
    demand = [Demand(product_id='P1', period=1, expected_quantity=10), Demand(product_id='P1', period=2, expected_quantity=20)]
    plot_procurement_plan(procurement_plan)
    plot_inventory_levels(inventory)
    plot_demand_vs_supply(demand, procurement_plan) 