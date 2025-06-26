from pydantic import BaseModel, Field
from typing import List, Dict

class Supplier(BaseModel):
    """
    Represents a supplier that offers products.
    Fields:
    - id: Unique identifier for the supplier.
    - name: Name of the supplier.
    - products_offered: List of product IDs that the supplier can provide.
    - lead_times: Dictionary mapping product IDs to lead times (in periods).
    """
    id: str
    name: str
    products_offered: List[str]
    lead_times: Dict[str, int]  # product_id -> lead time in periods 