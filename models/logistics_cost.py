from pydantic import BaseModel, Field

class LogisticsCost(BaseModel):
    """
    Represents logistics cost information for a supplier-product pair.
    Fields:
    - supplier_id: ID of the supplier.
    - product_id: ID of the product.
    - cost_per_unit: Logistics cost per unit.
    - fixed_cost: Fixed logistics cost per shipment.
    """
    supplier_id: str = Field(..., description="ID of the supplier.")
    product_id: str = Field(..., description="ID of the product.")
    cost_per_unit: float = Field(..., description="Logistics cost per unit.")
    fixed_cost: float = Field(..., description="Fixed logistics cost per shipment.") 