from models.product import Product
from models.supplier import Supplier
from models.demand import Demand
from models.inventory import Inventory
from models.logistics_cost import LogisticsCost


def test_product():
    p = Product(id="P1", name="Widget", unit_cost_by_supplier={"S1": 10.0}, expiration_periods=12, MOQ=5)
    assert p.id == "P1"

def test_supplier():
    s = Supplier(id="S1", name="SupplierA", products_offered=["P1"], minimum_order_value=100.0, lead_times={"P1": 2})
    assert s.id == "S1"

def test_demand():
    d = Demand(product_id="P1", period=1, expected_quantity=50)
    assert d.period == 1

def test_inventory():
    i = Inventory(product_id="P1", initial_stock=100, holding_cost=0.5, warehouse_capacity=1000, safety_stock=0)
    assert i.initial_stock == 100

def test_logistics_cost():
    l = LogisticsCost(supplier_id="S1", product_id="P1", cost_per_unit=2.0, fixed_cost=50.0)
    assert l.fixed_cost == 50.0

def test_visualization_runs():
    import matplotlib
    matplotlib.use('Agg')
    from utils.visualization import plot_procurement_plan, plot_inventory_levels, plot_demand_vs_supply
    procurement_plan = {('P1', 'S1', 1): 10.0, ('P1', 'S1', 2): 20.0}
    inventory = {('P1', 1): 5.0, ('P1', 2): 10.0}
    demand = [Demand(product_id='P1', period=1, expected_quantity=10), Demand(product_id='P1', period=2, expected_quantity=20)]
    plot_procurement_plan(procurement_plan)
    plot_inventory_levels(inventory)
    plot_demand_vs_supply(demand, procurement_plan) 