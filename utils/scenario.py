from typing import Dict, Any, Callable

def run_scenario_analysis(base_data: Dict[str, Any], scenarios: Dict[str, Any], solver: Callable[[Dict[str, Any]], Dict[str, Any]]) -> Dict[str, Any]:
    """
    Run scenario analysis and sensitivity testing.
    For each scenario:
      1. Copy the base data.
      2. Apply scenario-specific changes to the data.
      3. Run the solver on the modified data.
      4. Collect and return results for each scenario.
    Returns a dictionary with scenario results.
    """
    results = {}
    for name, changes in scenarios.items():
        # Copy base data for this scenario
        scenario_data = {k: v for k, v in base_data.items()}
        # Apply scenario-specific changes
        for key, value in changes.items():
            scenario_data[key] = value
        # Run the solver and store the result
        results[name] = solver(scenario_data)
    return results 