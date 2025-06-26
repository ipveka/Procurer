# Procurer: Professional Supply Chain Optimization

Procurer is a modular, professional Python system for multi-period, multi-product, multi-supplier procurement planning. It features:

- Streamlit UI for scenario analysis and reporting
- Linear (MILP), nonlinear (NLP), and heuristic solvers
- Scenario analysis and comprehensive reporting
- Fully documented, extensible, and robust codebase

## Key Features
- **Optimization**: Minimize procurement, logistics, and holding costs while meeting demand and respecting all constraints (capacity, safety stock, MOQ, shelf life, etc.)
- **Multiple Solvers**: Compare exact (MILP), nonlinear (discount-aware), and heuristic (fast, interpretable) approaches
- **Scenario Analysis**: Explore the impact of different policies, demand, and supplier options
- **Professional Reporting**: HTML and in-app reports with clear explanations, KPIs, and visualizations
- **Tested & Documented**: Comprehensive tests and detailed documentation throughout

## Solver Architecture (2024 Refactor)
All solvers now follow a clear, maintainable structure:
- **Lookup Table Preparation**: All data is mapped for fast access in a dedicated helper
- **Variable/Model Creation**: Variables and models are created in a single, well-documented helper
- **Objective & Constraints**: Each is added in a clear, grouped fashion, with helpers and comments
- **Solution Extraction**: Output is parsed and returned in a consistent format

This structure makes it easy to:
- Understand and debug solver logic
- Extend with new constraints, objectives, or solver types
- Maintain and test the codebase

**Inputs and outputs remain unchanged**—all APIs and data formats are stable.

## How to Contribute or Extend
- To add a new solver, subclass `BaseSolver` and follow the helper-based structure (see `solvers/linear.py`, `solvers/nonlinear.py`, `solvers/heuristic.py`)
- To add new constraints or objectives, add a helper or extend the relevant method
- All code should be type-annotated and clearly commented
- Run `pytest` to verify correctness after any change

## Running & Testing
- Install requirements: `pip install -r requirements.txt`
- Run the app: `streamlit run app.py`
- Run tests: `pytest --maxfail=3 --disable-warnings -v`

## License
MIT
