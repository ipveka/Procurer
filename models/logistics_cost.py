from pydantic import BaseModel, Field

class LogisticsCost(BaseModel):
    """
    Represents logistics cost information for a supplier-product pair.
    """
    supplier_id: str = Field(..., description="ID of the supplier.")
    product_id: str = Field(..., description="ID of the product.")
    cost_per_unit: float = Field(..., description="Logistics cost per unit.")
    fixed_cost: float = Field(..., description="Fixed logistics cost per shipment.") 