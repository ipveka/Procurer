#!/usr/bin/python3
"""
Procurer End-to-End Example

This script demonstrates how to use the Procurer system for supply chain optimization:
- Load and validate data
- Show the data used
- Run both the exact (MILP) and heuristic solvers
- Calculate KPIs
- Save procurement, shipments, inventory, and demand/supply plots to the output folder
- Generate a comprehensive HTML report with 2x2 plot layout

Key Concepts:
- Procurement Plan: When orders are placed (considering lead times)
- Shipments Plan: When orders actually arrive at the warehouse
- Inventory Levels: Stock levels throughout the planning horizon
- Demand vs Supply: Comparison of customer demand vs. available supply
"""
import os
import sys
import pandas as pd
import argparse
import json
import matplotlib.pyplot as plt

# Ensure working directory is always the project root
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(project_root)
sys.path.insert(0, project_root)

from utils.data_loader import load_all_data
from utils.validation import validate_data
from utils.metrics import calculate_kpis
from utils.reporting import (
    print_data_section,
    plot_procurement_plan,
    plot_inventory_levels,
    plot_demand_vs_supply,
    generate_html_report
)
from utils.visualization import plot_shipments_plan

# --- Ensure output directory exists ---
output_dir = 'output'
os.makedirs(output_dir, exist_ok=True)

# --- Solver selection parameter ---
def parse_solver_args():
    parser = argparse.ArgumentParser(description='Procurer E2E Example')
    parser.add_argument('--solvers', nargs='+', choices=['linear', 'heuristic', 'nonlinear'], default=['linear'],
                        help='Which solvers to run (default: linear)')
    return parser.parse_args()

args = parse_solver_args()
run_linear = 'linear' in args.solvers
run_heuristic = 'heuristic' in args.solvers
run_nonlinear = 'nonlinear' in args.solvers

# --- 1. Setup data paths ---
print("\n--- Procurer E2E Example ---\n")
print("This example demonstrates supply chain optimization with realistic lead times.")
print("Key concepts:")
print("- Procurement Plan: When orders are placed (considering lead times)")
print("- Shipments Plan: When orders actually arrive at the warehouse")
print("- Inventory Levels: Stock levels throughout the planning horizon")
print("- Demand vs Supply: Comparison of customer demand vs. available supply\n")

data_dir = 'data'
paths = {
    'products': f'{data_dir}/products.json',
    'suppliers': f'{data_dir}/suppliers.json',
    'demand': f'{data_dir}/demand.json',
    'inventory': f'{data_dir}/inventory.json',
    'logistics_cost': f'{data_dir}/logistics_cost.json'
}

# --- 2. Load and validate data ---
print("Loading and validating data...")
data = load_all_data(paths)
validate_data(data)
print("Data loaded and validated!\n")

# --- 3. Show the data used ---
print_data_section("Products", data['products'])
print_data_section("Suppliers", data['suppliers'])
print_data_section("Demand", data['demand'])
print_data_section("Inventory", data['inventory'])
print_data_section("Logistics Cost", data['logistics_cost'])

def dict_keys_to_str(d):
    if isinstance(d, dict):
        return {str(k): dict_keys_to_str(v) for k, v in d.items()}
    elif isinstance(d, list):
        return [dict_keys_to_str(i) for i in d]
    else:
        return d

# --- 4. Run Linear Solver (MILP) ---
if run_linear:
    from solvers.linear import LinearSolver
    print("Running Linear Solver (MILP)...")
    print("This solver finds the optimal procurement plan by minimizing total cost")
    print("while respecting all constraints including lead times, MOQs, and safety stock.\n")
    linear_solver = LinearSolver()
    linear_solution = linear_solver.solve(data)
    print(f"Linear Solver Status: {linear_solution['status']}")
    print(f"Objective Value: {linear_solution['objective']}\n")
    print("Full Linear Solution:")
    print(json.dumps(dict_keys_to_str(linear_solution), indent=2, default=str))
else:
    linear_solution = None

# --- 5. Run Heuristic Solver ---
if run_heuristic:
    from solvers.heuristic import HeuristicSolver
    print("Running Heuristic Solver...")
    print("This solver uses a rule-based approach to create a feasible procurement plan")
    print("by projecting inventory forward and ordering when safety stock is threatened.\n")
    heuristic_solver = HeuristicSolver()
    heuristic_solution = heuristic_solver.solve(data)
    print(f"Heuristic Solver Status: {heuristic_solution['status']}\n")
    print("Full Heuristic Solution:")
    print(json.dumps(dict_keys_to_str(heuristic_solution), indent=2, default=str))
else:
    heuristic_solution = None

# --- 6. Run Nonlinear Solver ---
if run_nonlinear:
    from solvers.nonlinear import NonlinearSolver
    print("Running Nonlinear Solver (with discounts)...")
    print("This solver considers volume discounts and finds the optimal procurement plan")
    print("with nonlinear cost structures.\n")
    nonlinear_solver = NonlinearSolver()
    nonlinear_solution = nonlinear_solver.solve(data)
    print(f"Nonlinear Solver Status: {nonlinear_solution['status']}")
    print(f"Objective Value: {nonlinear_solution['objective']}\n")
    print("Full Nonlinear Solution:")
    print(json.dumps(dict_keys_to_str(nonlinear_solution), indent=2, default=str))
else:
    nonlinear_solution = None

# --- 7. Calculate KPIs for All Solutions ---
print("Calculating KPIs...")
print("Key Performance Indicators measure the quality of the procurement plan:")
print("- Total Procurement Cost: Sum of all product and logistics costs")
print("- Service Level: Fraction of demand fulfilled (1.0 = perfect)")
print("- Inventory Turnover: How efficiently inventory is used")
print("- Obsolescence: Risk of unused inventory at the end\n")

if linear_solution:
    linear_kpis = calculate_kpis(linear_solution, data)
    import json
    print(f"Linear Solver KPIs: {json.dumps(linear_kpis, indent=2)}")
else:
    linear_kpis = None
if heuristic_solution:
    heuristic_kpis = calculate_kpis(heuristic_solution, data)
    import json
    print(f"Heuristic Solver KPIs: {json.dumps(heuristic_kpis, indent=2)}")
else:
    heuristic_kpis = None
if nonlinear_solution:
    nonlinear_kpis = calculate_kpis(nonlinear_solution, data)
    import json
    print(f"Nonlinear Solver KPIs: {json.dumps(nonlinear_kpis, indent=2)}\n")
else:
    nonlinear_kpis = None

# --- 8-10. Visualize and Save Results with 2x2 Layout ---
plot_files = {}
if linear_solution:
    print("Saving plots for Linear Solution (2x2 layout)...")
    print("Creating comprehensive visualization with:")
    print("- Procurement Plan: When orders are placed")
    print("- Shipments Plan: When orders arrive")
    print("- Inventory Levels: Stock throughout time")
    print("- Demand vs Supply: Customer needs vs available stock\n")
    
    linear_procurement_plot = os.path.join(output_dir, 'linear_procurement_plan.png')
    linear_shipments_plot = os.path.join(output_dir, 'linear_shipments_plan.png')
    linear_inventory_plot = os.path.join(output_dir, 'linear_inventory_levels.png')
    linear_demand_supply_plot = os.path.join(output_dir, 'linear_demand_vs_supply.png')
    
    # Create procurement plan plot
    plot_procurement_plan(
        linear_solution['procurement_plan'],
        linear_procurement_plot,
        'Linear Solution: Procurement Plan (Orders Placed)'
    )
    
    # Create shipments plan plot
    fig = plot_shipments_plan(linear_solution['shipments_plan'])
    fig.savefig(linear_shipments_plot, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"Plot saved: {linear_shipments_plot}")
    
    # Create inventory levels plot
    plot_inventory_levels(
        linear_solution['inventory'],
        linear_inventory_plot,
        'Linear Solution: Inventory Levels'
    )
    
    # Create demand vs supply plot (using shipments, not procurement)
    plot_demand_vs_supply(
        data['demand'],
        linear_solution['shipments_plan'],
        linear_demand_supply_plot,
        'Linear Solution: Demand vs. Supply (Shipments)'
    )
    
    plot_files['linear_procurement'] = linear_procurement_plot
    plot_files['linear_shipments'] = linear_shipments_plot
    plot_files['linear_inventory'] = linear_inventory_plot
    plot_files['linear_demand_supply'] = linear_demand_supply_plot

if heuristic_solution:
    print("Saving plots for Heuristic Solution (2x2 layout)...")
    heuristic_procurement_plot = os.path.join(output_dir, 'heuristic_procurement_plan.png')
    heuristic_shipments_plot = os.path.join(output_dir, 'heuristic_shipments_plan.png')
    heuristic_inventory_plot = os.path.join(output_dir, 'heuristic_inventory_levels.png')
    heuristic_demand_supply_plot = os.path.join(output_dir, 'heuristic_demand_vs_supply.png')
    
    plot_procurement_plan(
        heuristic_solution['procurement_plan'],
        heuristic_procurement_plot,
        'Heuristic Solution: Procurement Plan (Orders Placed)'
    )
    
    fig = plot_shipments_plan(heuristic_solution['shipments_plan'])
    fig.savefig(heuristic_shipments_plot, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"Plot saved: {heuristic_shipments_plot}")
    
    plot_inventory_levels(
        heuristic_solution['inventory'],
        heuristic_inventory_plot,
        'Heuristic Solution: Inventory Levels'
    )
    
    plot_demand_vs_supply(
        data['demand'],
        heuristic_solution['shipments_plan'],
        heuristic_demand_supply_plot,
        'Heuristic Solution: Demand vs. Supply (Shipments)'
    )
    
    plot_files['heuristic_procurement'] = heuristic_procurement_plot
    plot_files['heuristic_shipments'] = heuristic_shipments_plot
    plot_files['heuristic_inventory'] = heuristic_inventory_plot
    plot_files['heuristic_demand_supply'] = heuristic_demand_supply_plot

if nonlinear_solution:
    print("Saving plots for Nonlinear Solution (2x2 layout)...")
    nonlinear_procurement_plot = os.path.join(output_dir, 'nonlinear_procurement_plan.png')
    nonlinear_shipments_plot = os.path.join(output_dir, 'nonlinear_shipments_plan.png')
    nonlinear_inventory_plot = os.path.join(output_dir, 'nonlinear_inventory_levels.png')
    nonlinear_demand_supply_plot = os.path.join(output_dir, 'nonlinear_demand_vs_supply.png')
    
    plot_procurement_plan(
        nonlinear_solution['procurement_plan'],
        nonlinear_procurement_plot,
        'Nonlinear Solution: Procurement Plan (Orders Placed)'
    )
    
    fig = plot_shipments_plan(nonlinear_solution['shipments_plan'])
    fig.savefig(nonlinear_shipments_plot, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"Plot saved: {nonlinear_shipments_plot}")
    
    plot_inventory_levels(
        nonlinear_solution['inventory'],
        nonlinear_inventory_plot,
        'Nonlinear Solution: Inventory Levels'
    )
    
    plot_demand_vs_supply(
        data['demand'],
        nonlinear_solution['shipments_plan'],
        nonlinear_demand_supply_plot,
        'Nonlinear Solution: Demand vs. Supply (Shipments)'
    )
    
    plot_files['nonlinear_procurement'] = nonlinear_procurement_plot
    plot_files['nonlinear_shipments'] = nonlinear_shipments_plot
    plot_files['nonlinear_inventory'] = nonlinear_inventory_plot
    plot_files['nonlinear_demand_supply'] = nonlinear_demand_supply_plot

# --- 11. Generate HTML Report ---
print("Generating comprehensive HTML report...")
print("The report includes:")
print("- Detailed KPI analysis and explanations")
print("- 2x2 plot layout showing all aspects of the solution")
print("- Solver comparison and methodology explanations")
print("- Variable definitions and constraint explanations\n")

generate_html_report(
    output_dir,
    linear_kpis=linear_kpis or {},
    heuristic_kpis=heuristic_kpis or {},
    nonlinear_kpis=nonlinear_kpis or {},
    plot_files=plot_files,
    heuristic_solution=heuristic_solution or {},
    linear_solution=linear_solution or {},
    nonlinear_solution=nonlinear_solution or {},
    data=data
)

def save_solution_csv(filename, solution, data):
    products = {p.id: p for p in data['products']}
    suppliers = {s.id: s for s in data['suppliers']}
    demand_map = {(d.product_id, d.period): d.expected_quantity for d in data['demand']}
    logistics_map = {(l.supplier_id, l.product_id): l for l in data['logistics_cost']}
    rows = []
    for (p, s, t), procurement_qty in solution['procurement_plan'].items():
        inventory = solution['inventory'].get((p, t), 0)
        demand = demand_map.get((p, t), 0)
        unit_cost = products[p].unit_cost_by_supplier.get(s, None)
        logistics_cost = logistics_map.get((s, p), None)
        logistics_cost_val = logistics_cost.cost_per_unit if logistics_cost else None
        discount_applied = 0
        if hasattr(products[p], 'discounts') and products[p].discounts:
            threshold = products[p].discounts.get('threshold', 0)
            discount = products[p].discounts.get('discount', 0.0)
            if procurement_qty > threshold:
                discount_applied = discount
        rows.append({
            'product': p,
            'supplier': s,
            'period': t,
            'procurement_qty': procurement_qty,
            'inventory': inventory,
            'demand': demand,
            'unit_cost': unit_cost,
            'logistics_cost': logistics_cost_val,
            'discount_applied': discount_applied
        })
    df = pd.DataFrame(rows)
    df.to_csv(filename, index=False)

print("Saving results as CSV...")
if heuristic_solution:
    save_solution_csv(os.path.join(output_dir, 'heuristic_results.csv'), heuristic_solution, data)
if linear_solution:
    save_solution_csv(os.path.join(output_dir, 'linear_results.csv'), linear_solution, data)
if nonlinear_solution:
    save_solution_csv(os.path.join(output_dir, 'nonlinear_results.csv'), nonlinear_solution, data)
print("CSV files saved in output directory.")

print("\nAll plots and the HTML report are saved in the 'output' folder.")
print("The 2x2 plot layout provides a comprehensive view of:")
print("1. Procurement Plan (when orders are placed)")
print("2. Shipments Plan (when orders arrive)")
print("3. Inventory Levels (stock throughout time)")
print("4. Demand vs Supply (customer needs vs available stock)")
print("\nE2E process complete!\n") 