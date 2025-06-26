from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from solvers.linear import LinearSolver
from solvers.heuristic import HeuristicSolver
from utils.validation import validate_data
from utils.data_loader import load_all_data
from utils.logging import get_logger
from typing import Any, Dict, Optional
import json

app = FastAPI(title="Procurer API", description="Supply Chain Optimization System API")
logger = get_logger("API")

class OptimizationResponse(BaseModel):
    solution: Dict[str, Any]

@app.post("/solve/linear", response_model=OptimizationResponse)
async def solve_linear(
    products: UploadFile = File(...),
    suppliers: UploadFile = File(...),
    demand: UploadFile = File(...),
    inventory: UploadFile = File(...),
    logistics_cost: UploadFile = File(...)
):
    try:
        paths = {}
        for name, file in zip(['products', 'suppliers', 'demand', 'inventory', 'logistics_cost'], [products, suppliers, demand, inventory, logistics_cost]):
            content = await file.read()
            paths[name] = json.loads(content)
        # Convert dicts to Pydantic models
        data = {
            'products': [p for p in map(lambda x: x if hasattr(x, 'id') else x, paths['products'])],
            'suppliers': [s for s in map(lambda x: x if hasattr(x, 'id') else x, paths['suppliers'])],
            'demand': [d for d in map(lambda x: x if hasattr(x, 'product_id') else x, paths['demand'])],
            'inventory': [i for i in map(lambda x: x if hasattr(x, 'product_id') else x, paths['inventory'])],
            'logistics_cost': [l for l in map(lambda x: x if hasattr(x, 'supplier_id') else x, paths['logistics_cost'])],
        }
        validate_data(data)
        solver = LinearSolver()
        solution = solver.solve(data)
        return OptimizationResponse(solution=solution)
    except Exception as e:
        logger.error(f"Linear solver error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/solve/heuristic", response_model=OptimizationResponse)
async def solve_heuristic(
    products: UploadFile = File(...),
    suppliers: UploadFile = File(...),
    demand: UploadFile = File(...),
    inventory: UploadFile = File(...),
    logistics_cost: UploadFile = File(...)
):
    try:
        paths = {}
        for name, file in zip(['products', 'suppliers', 'demand', 'inventory', 'logistics_cost'], [products, suppliers, demand, inventory, logistics_cost]):
            content = await file.read()
            paths[name] = json.loads(content)
        data = {
            'products': [p for p in map(lambda x: x if hasattr(x, 'id') else x, paths['products'])],
            'suppliers': [s for s in map(lambda x: x if hasattr(x, 'id') else x, paths['suppliers'])],
            'demand': [d for d in map(lambda x: x if hasattr(x, 'product_id') else x, paths['demand'])],
            'inventory': [i for i in map(lambda x: x if hasattr(x, 'product_id') else x, paths['inventory'])],
            'logistics_cost': [l for l in map(lambda x: x if hasattr(x, 'supplier_id') else x, paths['logistics_cost'])],
        }
        validate_data(data)
        solver = HeuristicSolver()
        solution = solver.solve(data)
        return OptimizationResponse(solution=solution)
    except Exception as e:
        logger.error(f"Heuristic solver error: {e}")
        raise HTTPException(status_code=400, detail=str(e)) 