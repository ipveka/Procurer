"""
Main entry point for the Procurer Supply Chain Optimization System.

Usage:
  python main.py cli  # Run CLI
  python main.py api  # Run API
  python main.py scenario  # Run scenario analysis
  python main.py kpi  # Calculate KPIs for a solution
"""
import sys
from utils.data_loader import load_all_data
from utils.validation import validate_data
from utils.metrics import calculate_kpis
from utils.scenario import run_scenario_analysis
from solvers.linear import LinearSolver
from solvers.heuristic import HeuristicSolver
import json

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "api":
        import uvicorn
        uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
    elif len(sys.argv) > 1 and sys.argv[1] == "scenario":
        # Example scenario analysis
        paths = {
            'products': 'data/products.json',
            'suppliers': 'data/suppliers.json',
            'demand': 'data/demand.json',
            'inventory': 'data/inventory.json',
            'logistics_cost': 'data/logistics_cost.json'
        }
        data = load_all_data(paths)
        validate_data(data)
        scenarios = {
            'high_demand': {'demand': [{**d, 'expected_quantity': d.expected_quantity * 1.2} for d in data['demand']]},
            'low_demand': {'demand': [{**d, 'expected_quantity': d.expected_quantity * 0.8} for d in data['demand']]}
        }
        results = run_scenario_analysis(data, scenarios, LinearSolver().solve)
        print(json.dumps(results, indent=2, default=str))
    elif len(sys.argv) > 1 and sys.argv[1] == "kpi":
        # Example KPI calculation
        paths = {
            'products': 'data/products.json',
            'suppliers': 'data/suppliers.json',
            'demand': 'data/demand.json',
            'inventory': 'data/inventory.json',
            'logistics_cost': 'data/logistics_cost.json'
        }
        data = load_all_data(paths)
        validate_data(data)
        solution = LinearSolver().solve(data)
        kpis = calculate_kpis(solution, data)
        print(json.dumps(kpis, indent=2))
    else:
        import cli
        cli.cli() 