from typing import Any, Dict

# validation.py: Functions for validating input data for supply chain optimization.
# Ensures all data is consistent, complete, and suitable for use by solvers and the app.
# All validation logic is documented for clarity and maintainability.

def validate_data(data: Dict[str, Any]) -> bool:
    """
    Validate input data for the procurement optimization problem.
    Step-by-step:
    1. Check that all product_ids in demand and inventory exist in products.
    2. Check that all supplier_ids in logistics_cost exist in suppliers.
    3. Raise ValueError if any reference is invalid.
    Returns True if data is valid, else raises ValueError.
    """
    # Step 1: Validate product_ids in demand and inventory
    product_ids = {p.id for p in data['products']}
    for d in data['demand']:
        if d.product_id not in product_ids:
            raise ValueError(f"Demand references unknown product_id: {d.product_id}")
    for i in data['inventory']:
        if i.product_id not in product_ids:
            raise ValueError(f"Inventory references unknown product_id: {i.product_id}")
    # Step 2: Validate supplier_ids in logistics_cost
    supplier_ids = {s.id for s in data['suppliers']}
    for l in data['logistics_cost']:
        if l.supplier_id not in supplier_ids:
            raise ValueError(f"LogisticsCost references unknown supplier_id: {l.supplier_id}")
        if l.product_id not in product_ids:
            raise ValueError(f"LogisticsCost references unknown product_id: {l.product_id}")
    return True 