# Procurer: Professional Supply Chain Optimization

Procurer is a modular, professional Python system for multi-period, multi-product, multi-supplier procurement planning with realistic lead time modeling. It features:

- Streamlit UI for scenario analysis and reporting
- Linear (MILP), nonlinear (NLP), and heuristic solvers
- Realistic lead time modeling (procurement vs shipments)
- 2x2 visualization layout for comprehensive analysis
- Scenario analysis and comprehensive reporting
- Fully documented, extensible, and robust codebase

## Key Features
- **Optimization**: Minimize procurement, logistics, and holding costs while meeting demand and respecting all constraints (capacity, safety stock, MOQ, shelf life, lead times, etc.)
- **Multiple Solvers**: Compare exact (MILP), nonlinear (discount-aware), and heuristic (fast, interpretable) approaches
- **Realistic Lead Times**: Distinguish between when orders are placed (procurement) and when they arrive (shipments)
- **2x2 Visualization**: Comprehensive view showing procurement plans, shipments, inventory levels, and demand vs supply
- **Scenario Analysis**: Explore the impact of different policies, demand, and supplier options
- **Professional Reporting**: HTML and in-app reports with clear explanations, KPIs, and visualizations
- **Tested & Documented**: Comprehensive tests and detailed documentation throughout

## Key Supply Chain Concepts
- **Procurement Plan**: When orders are placed to suppliers (considering lead times)
- **Shipments Plan**: When orders actually arrive at the warehouse (procurement + lead time)
- **Inventory Levels**: Stock levels throughout the planning horizon
- **Demand vs Supply**: Comparison of customer demand vs. available supply

## Solver Methodologies
- **Linear (MILP)**: Finds the optimal plan by minimizing total cost (procurement, logistics, holding) while respecting all constraints. Models realistic lead times and distinguishes between procurement (order placement) and shipments (order arrival).
- **Nonlinear (NLP)**: Similar to linear solver, but models quantity discounts: if you buy more than a threshold, you get a lower price for the extra units. Also models lead times and distinguishes procurement from shipments.
- **Heuristic**: Works period by period, projecting inventory forward and ordering when safety stock is threatened. Orders from the cheapest available supplier when projected inventory falls below safety stock. Fast and simple, but may not find the absolute best solution. Models lead times and distinguishes procurement from shipments.

## Constraints & Assumptions
- **Hard Constraints**: All constraints in the model are hard constraints (must be satisfied): demand fulfillment, inventory balance, warehouse capacity, safety stock, shelf life, and MOQ.
- **Soft Constraints**: In some advanced scenarios, soft constraints (penalties for violations) can be used for flexibility or robustness, e.g., allowing small backorders or exceeding capacity with a cost penalty.
- **Lead Times**: Realistic modeling of time between order placement and order arrival
- **Safety Stock**: Minimum inventory required at all times as a buffer against uncertainty
- **MOQ**: Minimum order quantities that must be met for each supplier

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

## Visualization & Analysis
The system provides a comprehensive 2x2 visualization layout:
1. **Procurement Plan**: When orders are placed (considering lead times)
2. **Shipments Plan**: When orders arrive at the warehouse
3. **Inventory Levels**: Stock levels throughout the planning horizon
4. **Demand vs Supply**: Comparison of customer demand vs. available supply

All plots are optimized for clarity with y-axis starting at 0 when appropriate, grid lines, and clear legends.

## How to Contribute or Extend
- To add a new solver, subclass `BaseSolver` and follow the helper-based structure (see `solvers/linear.py`, `solvers/nonlinear.py`, `solvers/heuristic.py`)
- To add new constraints or objectives, add a helper or extend the relevant method
- All code should be type-annotated and clearly commented
- Run `pytest` to verify correctness after any change

## Running & Testing
- Install requirements: `pip install -r requirements.txt`
- Run the app: `streamlit run app.py`
- Run the E2E example: `python examples/e2e_example.py`
- Run tests: `pytest --maxfail=3 --disable-warnings -v`

## License
MIT
