# Procurer: Professional Python Supply Chain Optimization System

Procurer is a comprehensive, modular, and extensible Python system for multi-period, multi-product, multi-supplier procurement optimization. It supports both exact (MILP) and heuristic approaches, scenario analysis, risk assessment, and more.

## Features
- Multi-period, multi-product, multi-supplier procurement optimization
- Linear (MILP) and heuristic solvers
- Scenario analysis, rolling horizon, risk assessment
- CLI and optional FastAPI web API
- Modular, object-oriented design with type hints
- Pydantic data models and robust validation
- Visualization utilities for results

## Mathematical Formulation & Solver Details

### Model Variables
- **Indices:**
  - $i$: Product
  - $j$: Supplier
  - $t$: Period
- **Decision Variables:**
  - $p_{i,j,t}$: Quantity of product $i$ procured from supplier $j$ in period $t$
  - $inv_{i,t}$: Inventory of product $i$ at the end of period $t$

### Linear Solver (MILP)
**Objective:**
Minimize total cost (procurement, logistics, holding):

$$
\min \sum_{i,j,t} p_{i,j,t} \cdot c_{i,j} + \sum_{i,j,t} p_{i,j,t} \cdot l_{j,i} + \sum_{i,t} inv_{i,t} \cdot h_i
$$
Where:
- $c_{i,j}$: Unit cost of product $i$ from supplier $j$
- $l_{j,i}$: Logistics cost per unit
- $h_i$: Holding cost per unit per period

**Constraints:**
- **Inventory balance:**
  - $inv_{i,t} = inv_{i,t-1} + \sum_j p_{i,j,t} - d_{i,t}$
- **Warehouse capacity:**
  - $inv_{i,t} \leq$ warehouse capacity
- **Safety stock:**
  - $inv_{i,t} \geq$ safety stock
- **Shelf life:**
  - $inv_{i,t} = 0$ if $t$ exceeds expiration
- **MOQ:**
  - If $p_{i,j,t} > 0$, then $p_{i,j,t} \geq$ MOQ

### Nonlinear Solver (NLP with Quantity Discounts)
**Objective:**
Minimize total cost, where procurement cost is piecewise nonlinear due to discounts:

$$
\min \sum_{i,j,t} \text{PiecewiseCost}(p_{i,j,t}) + \sum_{i,j,t} p_{i,j,t} \cdot l_{j,i} + \sum_{i,t} inv_{i,t} \cdot h_i
$$
Where:
- $\text{PiecewiseCost}(p_{i,j,t}) = \begin{cases}
  p_{i,j,t} \cdot c_{i,j} & \text{if } p_{i,j,t} \leq \text{threshold} \\
  \text{threshold} \cdot c_{i,j} + (p_{i,j,t} - \text{threshold}) \cdot c_{i,j} \cdot (1-\text{discount}) & \text{if } p_{i,j,t} > \text{threshold}
\end{cases}$

**Constraints:** Same as linear solver.

### Heuristic Solver
- Fulfills demand and safety stock period by period, from the cheapest supplier, using the same constraints as above, but does not guarantee global optimality.
- Applies discounts in a greedy fashion if order quantity exceeds threshold.

### Discount Handling
- **Discounts** are defined per product as `{ "threshold": int, "discount": float }`.
- If order quantity for a product in a period from a supplier exceeds the threshold, the discount applies to units above the threshold.

## Project Structure
```
Procurer/
  models/         # Pydantic data models
  solvers/        # Optimization and heuristic solvers
  utils/          # Utilities (logging, validation, metrics, visualization, etc.)
  data/           # Example datasets
  tests/          # Unit and integration tests
  cli.py          # CLI entry point
  api.py          # FastAPI web API
  main.py         # Main orchestration script
  requirements.txt
  README.md
```

## Requirements and Installation

### Python Dependencies
All required Python packages are listed in `requirements.txt`. Install them with:

```bash
pip install -r requirements.txt
```

Key dependencies:
- `pydantic` (data validation)
- `pulp` (MILP solver for linear optimization)
- `ortools` (alternative MILP solver)
- `pyomo` (nonlinear optimization modeling)
- `ipopt` (nonlinear solver backend for Pyomo)
- `fastapi`, `uvicorn` (API)
- `matplotlib` (visualization)
- `click` (CLI)
- `pytest` (testing)

### System Dependencies
For nonlinear optimization, you must have the IPOPT solver installed and available in your system PATH.

#### macOS (with Homebrew):
```bash
brew install ipopt
```

#### Ubuntu/Debian:
```bash
sudo apt-get install coinor-ipopt
```

#### Other OS:
See the [official IPOPT installation instructions](https://coin-or.github.io/Ipopt/INSTALL.html).

### Verifying Installation
After installing, verify in Python:
```python
import pyomo.environ
```
And check that `ipopt` is available:
```bash
ipopt -v
```

### Troubleshooting
- If you see `ModuleNotFoundError: No module named 'pyomo'`, ensure you have run `pip install -r requirements.txt`.
- If you see errors about IPOPT not found, ensure it is installed and available in your system PATH.
- For nonlinear solver functionality, both `pyomo` and `ipopt` must be installed.

## How the Solvers Work

### BaseSolver (solvers/base.py)
- **Purpose:** Defines a standard interface for all solvers via the `solve(data)` method.
- **Why:** Ensures all solvers are interchangeable and code is extensible. Not strictly required, but highly recommended for professional codebases.
- **Usage:** Do not instantiate directly. Inherit for new solver types.

### LinearSolver (solvers/linear.py)
- **Approach:** Uses Mixed Integer Linear Programming (MILP) via PuLP.
- **Logic:**
  - Decision variables: How much of each product to buy from each supplier in each period.
  - Objective: Minimize total cost (procurement + logistics + holding).
  - Constraints: Demand satisfaction, inventory balance, warehouse capacity, product shelf life, MOQ, etc.
  - Returns a detailed procurement and inventory plan.
- **Best for:** Small/medium problems where optimality is required.

### HeuristicSolver (solvers/heuristic.py)
- **Approach:** Greedy algorithm with local logic.
- **Logic:**
  - For each period, fulfill demand from the cheapest available supplier, respecting MOQ and supplier constraints.
  - Uses inventory first, then orders as needed.
  - Fast, but not always optimal.
- **Best for:** Large or time-constrained problems, or as a quick baseline.

## Visualization
- Use the provided `utils/visualization.py` functions to plot procurement plans, inventory levels, and demand satisfaction.
- Example usage:
  ```python
  from utils.visualization import plot_procurement_plan, plot_inventory_levels
  plot_procurement_plan(solution['procurement_plan'])
  plot_inventory_levels(solution['inventory'])
  ```
- Visualizations help you understand the process, bottlenecks, and results.

## How to Run the Process
- **Main Executor:** Run `main.py` for all main workflows.
  - CLI: `python main.py cli`
  - API: `python main.py api`
  - Scenario analysis: `python main.py scenario`
  - KPI calculation: `python main.py kpi`
- **Direct CLI:** `python cli.py solve-linear ...`
- **API:** `uvicorn api:app --reload`
- **Tests:** `pytest`

## Interpreting Outputs
- **Solution:** Contains procurement plan, inventory levels, and status.
- **KPIs:** Total cost, service level, inventory turnover, obsolescence.
- **Visuals:** Use visualization functions to plot and interpret results.

## Comments and Documentation
- All code is commented for clarity, especially in solvers and utilities.
- See each module for detailed docstrings and inline explanations.

## License
MIT
