import json
from typing import List, Dict, Any
from models.product import Product
from models.supplier import Supplier
from models.demand import Demand
from models.inventory import Inventory
from models.logistics_cost import LogisticsCost
from pydantic import ValidationError


def load_products(path: str) -> List[Product]:
    with open(path, 'r') as f:
        data = json.load(f)
    return [Product(**item) for item in data]

def load_suppliers(path: str) -> List[Supplier]:
    with open(path, 'r') as f:
        data = json.load(f)
    return [Supplier(**item) for item in data]

def load_demand(path: str) -> List[Demand]:
    with open(path, 'r') as f:
        data = json.load(f)
    return [Demand(**item) for item in data]

def load_inventory(path: str) -> List[Inventory]:
    with open(path, 'r') as f:
        data = json.load(f)
    return [Inventory(**item) for item in data]

def load_logistics_cost(path: str) -> List[LogisticsCost]:
    with open(path, 'r') as f:
        data = json.load(f)
    return [LogisticsCost(**item) for item in data]

def load_all_data(paths: Dict[str, str]) -> Dict[str, Any]:
    """
    Loads all data from the provided file paths.
    paths: dict with keys 'products', 'suppliers', 'demand', 'inventory', 'logistics_cost'
    Returns a dict with lists of Pydantic models.
    """
    try:
        return {
            'products': load_products(paths['products']),
            'suppliers': load_suppliers(paths['suppliers']),
            'demand': load_demand(paths['demand']),
            'inventory': load_inventory(paths['inventory']),
            'logistics_cost': load_logistics_cost(paths['logistics_cost'])
        }
    except (ValidationError, KeyError, FileNotFoundError, json.JSONDecodeError) as e:
        raise ValueError(f"Data loading error: {e}") 