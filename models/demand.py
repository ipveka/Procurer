from pydantic import BaseModel, Field

class Demand(BaseModel):
    """
    Represents the expected demand for a product in a given period.
    """
    product_id: str = Field(..., description="ID of the product.")
    period: int = Field(..., description="Time period (integer index).")
    expected_quantity: float = Field(..., description="Expected demand quantity for the period.") 