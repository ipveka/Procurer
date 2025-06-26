from pydantic import BaseModel, Field

class Inventory(BaseModel):
    """
    Represents inventory information for a product.
    """
    product_id: str = Field(..., description="ID of the product.")
    initial_stock: float = Field(..., description="Initial stock level for the product.")
    holding_cost: float = Field(..., description="Holding cost per unit per period.")
    warehouse_capacity: float = Field(..., description="Maximum warehouse capacity for the product.")
    safety_stock: float = Field(0, description="Minimum safety stock that must be maintained for the product.") 