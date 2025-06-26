from pydantic import BaseModel, Field
from typing import Dict, Optional

class Product(BaseModel):
    """
    Represents a product that can be procured from suppliers.
    MOQ (Minimum Order Quantity) is enforced in both the exact and heuristic solvers.
    The 'discounts' field defines quantity discounts for nonlinear optimization: {'threshold': int, 'discount': float}.
    """
    id: str = Field(..., description="Unique identifier for the product.")
    name: str = Field(..., description="Name of the product.")
    unit_cost_by_supplier: Dict[str, float] = Field(..., description="Unit cost of the product by supplier ID.")
    expiration_periods: int = Field(..., description="Number of periods before the product expires.")
    MOQ: int = Field(..., description="Minimum order quantity for the product.")
    discounts: Optional[Dict[str, float]] = Field(None, description="Discount policy: {'threshold': int, 'discount': float}. If order quantity > threshold, discount applies to units above threshold.") 