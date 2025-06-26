from pydantic import BaseModel, Field
from typing import List, Dict

class Supplier(BaseModel):
    """
    Represents a supplier that offers products.
    """
    id: str = Field(..., description="Unique identifier for the supplier.")
    name: str = Field(..., description="Name of the supplier.")
    products_offered: List[str] = Field(..., description="List of product IDs offered by the supplier.")
    minimum_order_value: float = Field(..., description="Minimum order value required by the supplier.")
    lead_times: Dict[str, int] = Field(..., description="Lead times by product ID (in periods).") 