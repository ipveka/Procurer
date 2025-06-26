from typing import Dict, Any, Callable

def run_scenario_analysis(base_data: Dict[str, Any], scenarios: Dict[str, Any], solver: Callable[[Dict[str, Any]], Dict[str, Any]]) -> Dict[str, Any]:
    """
    Run scenario analysis and sensitivity testing.
    For each scenario, modify base_data as specified and run the solver.
    Returns a dictionary with scenario results.
    """
    results = {}
    for name, changes in scenarios.items():
        scenario_data = {k: v for k, v in base_data.items()}
        for key, value in changes.items():
            scenario_data[key] = value
        results[name] = solver(scenario_data)
    return results 