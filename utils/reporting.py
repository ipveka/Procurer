# reporting.py: Utilities for generating HTML and in-app reports for supply chain optimization results.
# Provides functions for KPI explanations, variable/assumption documentation, and solver result summaries.
# All reporting logic is documented for clarity and maintainability.

import os
import json
import base64
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from collections import defaultdict
from typing import Any, Dict, List, Optional

def print_data_section(name: str, items: List[Any]):
    """
    Print a section of data (e.g., products, suppliers) in a readable format.
    """
    print(f"{name}:")
    for item in items:
        print(json.dumps(item.dict(), indent=2))
    print()

def save_plot(filename: str, title: str = ""):
    """
    Save the current matplotlib plot to a file with improved formatting.
    """
    ax = plt.gca()
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.set_ylim(bottom=0)
    plt.grid(True, linestyle='--', alpha=0.7)
    if title:
        plt.title(title, fontsize=16, fontweight='bold', color='#2c3e50')
    plt.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Plot saved: {filename}")

def plot_procurement_plan(procurement_plan: Dict, filename: str, title: str, products_to_plot=None, moqs=None):
    plt.figure(figsize=(12, 8))
    data = defaultdict(lambda: defaultdict(float))
    for (product, supplier, period), qty in procurement_plan.items():
        data[(product, supplier)][period] += qty
    if products_to_plot is not None:
        data = {k: v for k, v in data.items() if k[0] in products_to_plot}
    for (product, supplier), period_qty in data.items():
        periods = sorted(period_qty.keys())
        quantities = [period_qty[p] for p in periods]
        plt.plot(periods, quantities, marker='o', linewidth=2, markersize=6, label=f'{product}-{supplier}')
        # Plot MOQ line if provided
        if moqs and product in moqs:
            plt.axhline(moqs[product], color='red', linestyle='--', linewidth=1, label=f'MOQ {product}')
    plt.xlabel('Period', fontsize=14)
    plt.ylabel('Procurement Quantity', fontsize=14)
    plt.legend(fontsize=12)
    save_plot(filename, title)

def plot_inventory_levels(inventory: Dict, filename: str, title: str, products_to_plot=None, safety_stocks=None):
    plt.figure(figsize=(12, 8))
    data = defaultdict(lambda: defaultdict(float))
    for (product, period), qty in inventory.items():
        data[product][period] += qty
    if products_to_plot is not None:
        data = {k: v for k, v in data.items() if k in products_to_plot}
    for product, period_qty in data.items():
        periods = sorted(period_qty.keys())
        quantities = [period_qty[p] for p in periods]
        plt.plot(periods, quantities, marker='o', linewidth=2, markersize=6, label=product)
        # Plot safety stock line if provided
        if safety_stocks and product in safety_stocks:
            plt.axhline(safety_stocks[product], color='orange', linestyle='--', linewidth=1, label=f'Safety Stock {product}')
    plt.xlabel('Period', fontsize=14)
    plt.ylabel('Inventory Level', fontsize=14)
    plt.legend(fontsize=12)
    save_plot(filename, title)

def plot_demand_vs_supply(demand: List[Any], shipments_plan: Dict, filename: str, title: str, products_to_plot=None):
    plt.figure(figsize=(12, 8))
    demand_map = defaultdict(float)
    for d in demand:
        demand_map[(d.product_id, d.period)] += d.expected_quantity
    supply_map = defaultdict(float)
    for (product, supplier, period), qty in shipments_plan.items():
        supply_map[(product, period)] += qty
    products = sorted(set(p for p, _ in demand_map.keys()))
    if products_to_plot is not None:
        products = [p for p in products if p in products_to_plot]
    periods = sorted(set(t for _, t in demand_map.keys()))
    for product in products:
        d_vals = [demand_map[(product, t)] for t in periods]
        s_vals = [supply_map[(product, t)] for t in periods]
        plt.plot(periods, d_vals, marker='o', linewidth=2, markersize=6, linestyle='--', label=f'Demand {product}')
        plt.plot(periods, s_vals, marker='s', linewidth=2, markersize=6, label=f'Supply {product}')
    plt.xlabel('Period', fontsize=14)
    plt.ylabel('Quantity', fontsize=14)
    plt.legend(fontsize=12)
    save_plot(filename, title)

def render_table(headers, rows):
    ths = ''.join(f'<th>{h}</th>' for h in headers)
    trs = ''
    for row in rows:
        tds = ''.join(f'<td>{v}</td>' for v in row)
        trs += f'<tr>{tds}</tr>'
    return f'<table class="data-table"><thead><tr>{ths}</tr></thead><tbody>{trs}</tbody></table>'

def img_to_base64(path):
    with open(path, 'rb') as f:
        encoded = base64.b64encode(f.read()).decode('utf-8')
    return f'data:image/png;base64,{encoded}'

def kpi_table_section(linear_kpis, heuristic_kpis, nonlinear_kpis):
    headers = ["KPI", "Heuristic Solver", "Linear Solver (MILP)", "Nonlinear Solver (Discounts)", "KPI Meaning"]
    kpi_explanations = {
        "total_procurement_cost": "Total cost of all products purchased including logistics costs",
        "service_level": "Fraction of demand fulfilled (1.0 = all demand met on time)",
        "inventory_turnover": "How many times inventory is used up per period (higher = more efficient)",
        "obsolescence": "Stock left at end that was not used (risk of waste/expiration)"
    }
    kpis = set(linear_kpis.keys()) | set(heuristic_kpis.keys()) | set(nonlinear_kpis.keys())
    rows = []
    for k in kpis:
        rows.append([
            k,
            f"{heuristic_kpis.get(k, 0):.2f}",
            f"{linear_kpis.get(k, 0):.2f}",
            f"{nonlinear_kpis.get(k, 0):.2f}",
            kpi_explanations.get(k, "-")
        ])
    return f'<div class="section"><h2>Key Performance Indicators (KPIs)</h2>{render_table(headers, rows)}</div>'

def generate_html_report(
    output_dir: str,
    linear_kpis: Dict,
    heuristic_kpis: Dict,
    nonlinear_kpis: Dict,
    plot_files: Dict[str, str],
    heuristic_solution: Dict,
    linear_solution: Dict,
    nonlinear_solution: Dict,
    data: Optional[Dict[str, Any]] = None
):
    # Determine which solvers were run
    solvers_run = []
    if linear_solution and any(k in plot_files for k in ['linear_demand_supply', 'linear_inventory', 'linear_procurement']):
        solvers_run.append('Linear (MILP)')
    if nonlinear_solution and any(k in plot_files for k in ['nonlinear_demand_supply', 'nonlinear_inventory', 'nonlinear_procurement']):
        solvers_run.append('Nonlinear (NLP with Discounts)')
    if heuristic_solution and any(k in plot_files for k in ['heuristic_demand_supply', 'heuristic_inventory', 'heuristic_procurement']):
        solvers_run.append('Heuristic')
    solvers_run_str = ', '.join(solvers_run) if solvers_run else 'None'

    # Variable/assumption explanation with updated concepts
    variables_explanation = """
    <div class="explanation">
      <h2>Key Concepts & Variables</h2>
      
      <h3>🔑 Understanding Procurement vs Shipments</h3>
      <p>This optimization model distinguishes between two critical moments in the supply chain timeline:</p>
      
      <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 10px 0;">
        <h4>📋 <b>Procurement Plan</b> - When Orders Are Placed</h4>
        <p><b>Procurement</b> is when you place an order with a supplier. This is when you pay and commit to purchasing.</p>
        <ul>
          <li><b>Timing:</b> Orders placed in advance, considering lead times</li>
          <li><b>Financial Impact:</b> Cash flows out when you place the order</li>
          <li><b>Example:</b> Need products in period 3, supplier has 2-period lead time → order in period 1</li>
        </ul>
      </div>
      
      <div style="background: #e8f5e8; padding: 15px; border-radius: 8px; margin: 10px 0;">
        <h4>📦 <b>Shipments Plan</b> - When Orders Actually Arrive</h4>
        <p><b>Shipments</b> is when ordered products arrive at your warehouse and become available for use.</p>
        <ul>
          <li><b>Timing:</b> Orders arrive after the lead time period</li>
          <li><b>Inventory Impact:</b> Available stock increases when shipments arrive</li>
          <li><b>Example:</b> Order placed in period 1 with 2-period lead time → arrives in period 3</li>
        </ul>
      </div>
      
      <h4>🎯 Why This Distinction Matters</h4>
      <ul>
        <li><b>💰 Cash Flow:</b> You pay when placing orders (procurement), not when they arrive</li>
        <li><b>📊 Inventory:</b> You can only use products that have arrived (shipments) to meet demand</li>
        <li><b>⏰ Planning:</b> You must order early enough for shipments to arrive when needed</li>
      </ul>
      
      <h3>Supply Chain Timeline Concepts:</h3>
      <ul>
        <li><b>Procurement Plan:</b> When orders are placed to suppliers (considering lead times)</li>
        <li><b>Shipments Plan:</b> When orders actually arrive at the warehouse (procurement + lead time)</li>
        <li><b>Inventory Levels:</b> Stock levels throughout the planning horizon</li>
        <li><b>Demand vs Supply:</b> Comparison of customer demand vs. available supply (shipments)</li>
      </ul>
      
      <h3>Model Variables:</h3>
      <ul>
        <li><b>Products:</b> Each product has a unique ID, name, cost per supplier, shelf life (expiration), and minimum order quantity (MOQ).</li>
        <li><b>Suppliers:</b> Each supplier offers certain products and has lead times per product.</li>
        <li><b>Demand:</b> Forecasted for each product and period. Assumed to be known and deterministic for this scenario.</li>
        <li><b>Inventory:</b> Initial stock, holding cost, warehouse capacity, and <b>safety stock</b> (minimum required inventory at all times) for each product.</li>
        <li><b>Logistics Cost:</b> Per-unit and fixed costs for each supplier-product pair.</li>
      </ul>
      
      <h3>Constraints & Assumptions:</h3>
      <ul>
        <li><b>Hard Constraints:</b> All constraints in the model are <b>hard constraints</b> (must be satisfied): demand fulfillment, inventory balance, warehouse capacity, safety stock, shelf life, and MOQ.</li>
        <li><b>Soft Constraints:</b> In some advanced scenarios, <b>soft constraints</b> (penalties for violations) can be used for flexibility or robustness, e.g., allowing small backorders or exceeding capacity with a cost penalty.</li>
        <li><b>Lead Times:</b> Realistic modeling of time between order placement and order arrival</li>
        <li><b>Safety Stock:</b> Minimum inventory required at all times as a buffer against uncertainty</li>
        <li><b>MOQ:</b> Minimum order quantities that must be met for each supplier</li>
      </ul>
      
      <h3>Assumptions:</h3>
      <ul>
        <li>All demand must be met on time (no backorders allowed).</li>
        <li>Products do not expire within the planning horizon (shelf life > periods).</li>
        <li>All suppliers are reliable and always deliver as planned.</li>
        <li>Costs and demand are deterministic (no uncertainty modeled here).</li>
        <li>Safety stock is strictly enforced: inventory at end of each period must be at least the safety stock level.</li>
        <li>Lead times are deterministic and supplier-specific.</li>
      </ul>
      
      <h3>Variable Details:</h3>
      <ul>
        <li><b>product_id</b>: Unique product identifier.</li>
        <li><b>supplier_id</b>: Unique supplier identifier.</li>
        <li><b>period</b>: Integer time index (e.g., 0, 1, 2, 3, ...).</li>
        <li><b>initial_stock</b>: Starting inventory for each product.</li>
        <li><b>holding_cost</b>: Cost per unit per period for holding inventory.</li>
        <li><b>warehouse_capacity</b>: Maximum inventory allowed for each product.</li>
        <li><b>safety_stock</b>: Minimum inventory required for each product at all times (buffer against uncertainty).</li>
        <li><b>unit_cost_by_supplier</b>: Cost per unit for each product from each supplier.</li>
        <li><b>MOQ</b>: Minimum order quantity for each product.</li>
        <li><b>lead_times</b>: Number of periods between order placement and delivery for each product-supplier pair.</li>
        <li><b>cost_per_unit</b>: Logistics cost per unit shipped.</li>
        <li><b>fixed_cost</b>: Fixed logistics cost per shipment.</li>
      </ul>
    </div>
    """
    
    # Plain-language solver explanation with updated concepts
    solver_explanation = f"""
    <div class='section'>
      <h2 class='section-title'>2. Solver Logic & Approach</h2>
      <div class='explanation'>
        <b>Solvers Activated in This Report:</b> <span style='color:#1976d2;font-weight:bold'>{solvers_run_str}</span><br><br>
        
        <h3>Linear Solver (MILP):</h3>
        <ul>
          <li>Finds the optimal procurement and inventory plan by minimizing total cost (procurement, logistics, holding).</li>
          <li>Respects all constraints: demand fulfillment, inventory balance, warehouse capacity, safety stock, shelf life, and minimum order quantity (MOQ).</li>
          <li>Models realistic lead times: orders placed in period t arrive in period t + lead_time.</li>
          <li>Uses a mathematical programming solver to guarantee the best solution for the given data.</li>
          <li>Distinguishes between procurement (order placement) and shipments (order arrival).</li>
        </ul>
        
        <h3>Nonlinear Solver (NLP with Discounts):</h3>
        <ul>
          <li>Similar to the linear solver, but models quantity discounts: if you buy more than a threshold, you get a lower price for the extra units.</li>
          <li>Minimizes total cost, including the effect of discounts, using a nonlinear optimization approach.</li>
          <li>Also models lead times and distinguishes procurement from shipments.</li>
        </ul>
        
        <h3>Heuristic Solver:</h3>
        <ul>
          <li>Works period by period, projecting inventory forward and ordering when safety stock is threatened.</li>
          <li>Orders from the cheapest available supplier when projected inventory falls below safety stock.</li>
          <li>Fast and simple, but may not find the absolute best solution.</li>
          <li>Applies discounts greedily if order quantity exceeds the discount threshold.</li>
          <li>Models lead times and distinguishes procurement from shipments.</li>
        </ul>
      </div>
    </div>
    """
    
    # KPI table: only show results for solvers that were executed
    kpi_rows = []
    kpi_headers = ["Solver", "Total Procurement Cost", "Service Level", "Inventory Turnover", "Obsolescence"]
    if linear_kpis:
        kpi_rows.append([
            "Linear (MILP)",
            f"{linear_kpis.get('total_procurement_cost', ''):.2f}" if 'total_procurement_cost' in linear_kpis else '',
            f"{linear_kpis.get('service_level', ''):.2f}" if 'service_level' in linear_kpis else '',
            f"{linear_kpis.get('inventory_turnover', ''):.2f}" if 'inventory_turnover' in linear_kpis else '',
            f"{linear_kpis.get('obsolescence', ''):.2f}" if 'obsolescence' in linear_kpis else ''
        ])
    if heuristic_kpis:
        kpi_rows.append([
            "Heuristic",
            f"{heuristic_kpis.get('total_procurement_cost', ''):.2f}" if 'total_procurement_cost' in heuristic_kpis else '',
            f"{heuristic_kpis.get('service_level', ''):.2f}" if 'service_level' in heuristic_kpis else '',
            f"{heuristic_kpis.get('inventory_turnover', ''):.2f}" if 'inventory_turnover' in heuristic_kpis else '',
            f"{heuristic_kpis.get('obsolescence', ''):.2f}" if 'obsolescence' in heuristic_kpis else ''
        ])
    if nonlinear_kpis:
        kpi_rows.append([
            "Nonlinear (NLP with Discounts)",
            f"{nonlinear_kpis.get('total_procurement_cost', ''):.2f}" if 'total_procurement_cost' in nonlinear_kpis else '',
            f"{nonlinear_kpis.get('service_level', ''):.2f}" if 'service_level' in nonlinear_kpis else '',
            f"{nonlinear_kpis.get('inventory_turnover', ''):.2f}" if 'inventory_turnover' in nonlinear_kpis else '',
            f"{nonlinear_kpis.get('obsolescence', ''):.2f}" if 'obsolescence' in nonlinear_kpis else ''
        ])
    kpi_table = f'<div class="section"><h2>Key Performance Indicators (KPIs)</h2>{render_table(kpi_headers, kpi_rows)}</div>'

    def table_section(title, headers, rows):
        return f'<div class="section"><h2>{title}</h2>{render_table(headers, rows)}</div>'
    if data is None:
        data = {}
    products_table = table_section(
        "Products",
        ["ID", "Name", "Unit Cost by Supplier", "Expiration Periods", "MOQ"],
        [[p.id, p.name, json.dumps(p.unit_cost_by_supplier), p.expiration_periods, p.MOQ] for p in data.get('products', [])]
    )
    suppliers_table = table_section(
        "Suppliers",
        ["ID", "Name", "Products Offered", "Lead Times"],
        [[s.id, s.name, ', '.join(s.products_offered), json.dumps(s.lead_times)] for s in data.get('suppliers', [])]
    )
    demand_table = table_section(
        "Demand Forecast",
        ["Product", "Period", "Expected Quantity"],
        [[d.product_id, d.period, d.expected_quantity] for d in data.get('demand', [])]
    )
    inventory_table = table_section(
        "Inventory Policy",
        ["Product", "Initial Stock", "Holding Cost", "Warehouse Capacity", "Safety Stock"],
        [[i.product_id, i.initial_stock, i.holding_cost, i.warehouse_capacity, getattr(i, 'safety_stock', 0)] for i in data.get('inventory', [])]
    )
    logistics_table = table_section(
        "Logistics Cost",
        ["Supplier", "Product", "Cost per Unit", "Fixed Cost"],
        [[l.supplier_id, l.product_id, l.cost_per_unit, l.fixed_cost] for l in data.get('logistics_cost', [])]
    )
    
    # Helper for detailed results tables with procurement and shipments
    def build_solution_rows(procurement_plan, inventory, demand, shipments_plan):
        rows = []
        for (i, j, t), v in procurement_plan.items():
            w = inventory.get((i, t), 0)
            x = next((d.expected_quantity for d in demand if d.product_id == i and d.period == t), 0)
            # Get shipment quantity for this period
            shipment_qty = shipments_plan.get((i, j, t), 0)
            rows.append([i, j, t, w, x, v, shipment_qty])
        # Sort ascending by product, supplier, period
        rows.sort(key=lambda row: (row[0], row[1], row[2]))
        return rows
    
    # Helper for 2x2 plot layout
    def create_2x2_plot_layout(plot_files, solver_name):
        plots_html = '<div class="grid-container">'
        
        # Top left: Procurement Plan
        if f'{solver_name}_procurement' in plot_files:
            plots_html += f'''
            <div class="plot-item">
                <h4>Procurement Plan (Orders Placed)</h4>
                <img src="{img_to_base64(plot_files[f"{solver_name}_procurement"])}" 
                     alt="{solver_name} Procurement Plan" 
                     style="max-width: 100%; height: auto;">
            </div>
            '''
        else:
            plots_html += '<div class="plot-item"><h4>Procurement Plan</h4><p>No data available</p></div>'
        
        # Top right: Shipments Plan
        if f'{solver_name}_shipments' in plot_files:
            plots_html += f'''
            <div class="plot-item">
                <h4>Shipments Plan (Orders Received)</h4>
                <img src="{img_to_base64(plot_files[f"{solver_name}_shipments"])}" 
                     alt="{solver_name} Shipments Plan" 
                     style="max-width: 100%; height: auto;">
            </div>
            '''
        else:
            plots_html += '<div class="plot-item"><h4>Shipments Plan</h4><p>No data available</p></div>'
        
        # Bottom left: Inventory Levels
        if f'{solver_name}_inventory' in plot_files:
            plots_html += f'''
            <div class="plot-item">
                <h4>Inventory Levels</h4>
                <img src="{img_to_base64(plot_files[f"{solver_name}_inventory"])}" 
                     alt="{solver_name} Inventory Levels" 
                     style="max-width: 100%; height: auto;">
            </div>
            '''
        else:
            plots_html += '<div class="plot-item"><h4>Inventory Levels</h4><p>No data available</p></div>'
        
        # Bottom right: Demand vs Supply
        if f'{solver_name}_demand_supply' in plot_files:
            plots_html += f'''
            <div class="plot-item">
                <h4>Demand vs Supply</h4>
                <img src="{img_to_base64(plot_files[f"{solver_name}_demand_supply"])}" 
                     alt="{solver_name} Demand vs Supply" 
                     style="max-width: 100%; height: auto;">
            </div>
            '''
        else:
            plots_html += '<div class="plot-item"><h4>Demand vs Supply</h4><p>No data available</p></div>'
        
        plots_html += '</div>'
        return plots_html
    
    html = f"""
    <html>
    <head>
        <title>Procurer Supply Chain Optimization Report</title>
        <style>
            body {{ 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                margin: 0; 
                padding: 0;
                background: #ffffff;
                min-height: 100vh;
            }}
            .container {{
                max-width: 1400px;
                margin: 0 auto;
                padding: 20px;
            }}
            h1 {{ 
                color: #2c3e50; 
                font-size: 3em; 
                margin-bottom: 0.5em; 
                text-align: center;
                font-weight: 300;
                letter-spacing: 2px;
            }}
            h2.section-title {{ 
                color: #2c3e50; 
                font-size: 2.2em; 
                margin-top: 1.5em; 
                margin-bottom: 0.8em; 
                border-bottom: 3px solid #3498db; 
                padding-bottom: 0.3em;
                font-weight: 400;
                position: relative;
            }}
            h2.section-title::after {{
                content: '';
                position: absolute;
                bottom: -3px;
                left: 0;
                width: 60px;
                height: 3px;
                background: #e74c3c;
            }}
            h3.subsection-title {{ 
                color: #34495e; 
                font-size: 1.5em; 
                margin-top: 1.5em; 
                margin-bottom: 0.8em;
                font-weight: 500;
                border-left: 4px solid #3498db;
                padding-left: 15px;
            }}
            h4 {{ 
                color: #2c3e50; 
                font-size: 1.3em; 
                margin-top: 1.2em; 
                margin-bottom: 0.5em; 
                text-align: center;
                font-weight: 500;
                background: linear-gradient(45deg, #3498db, #2980b9);
                color: white;
                padding: 10px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .section {{ 
                margin-bottom: 50px; 
                padding: 30px; 
                background: #ffffff; 
                border-radius: 15px; 
                box-shadow: 0 8px 32px rgba(0,0,0,0.1);
                border: 1px solid #e0e0e0;
            }}
            img {{ 
                width: 100%;
                max-width: 600px; 
                height: auto;
                margin: 15px auto; 
                border: 3px solid #3498db; 
                border-radius: 12px; 
                box-shadow: 0 8px 25px rgba(52, 152, 219, 0.3);
                transition: transform 0.3s ease, box-shadow 0.3s ease;
                display: block;
            }}
            img:hover {{
                transform: scale(1.02);
                box-shadow: 0 12px 35px rgba(52, 152, 219, 0.4);
            }}
            .explanation {{ 
                background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%); 
                padding: 25px; 
                border-radius: 15px; 
                margin-bottom: 40px; 
                border-left: 6px solid #2196f3;
                box-shadow: 0 4px 15px rgba(33, 150, 243, 0.1);
            }}
            .data-table {{ 
                border-collapse: collapse; 
                margin: 25px 0 40px 0; 
                width: 100%; 
                background: #ffffff;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            }}
            .data-table th, .data-table td {{ 
                border: 1px solid #e0e0e0; 
                padding: 15px 20px; 
                text-align: left; 
            }}
            .data-table th {{ 
                background: linear-gradient(135deg, #3498db 0%, #2980b9 100%); 
                color: #ffffff;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 1px;
                font-size: 0.9em;
            }}
            .data-table tr:nth-child(even) {{
                background-color: #f8f9fa;
            }}
            .data-table tr:hover {{
                background-color: #e3f2fd;
                transition: background-color 0.3s ease;
            }}
            .plot-container {{ 
                text-align: center; 
                margin: 30px 0; 
                padding: 20px;
                background: #f8f9fa;
                border-radius: 15px;
            }}
            .grid-container {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 30px;
                margin: 30px 0;
                padding: 20px;
                background: #f8f9fa;
                border-radius: 15px;
            }}
            .plot-item {{
                text-align: center;
                padding: 15px;
                background: #ffffff;
                border-radius: 12px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                transition: transform 0.3s ease;
                display: flex;
                flex-direction: column;
                align-items: center;
            }}
            .plot-item:hover {{
                transform: translateY(-5px);
            }}
            .plot-item img {{
                width: 100%;
                max-width: 550px;
                height: auto;
                margin: 10px 0;
                object-fit: contain;
            }}
            ul {{
                line-height: 1.8;
                color: #2c3e50;
            }}
            li {{
                margin-bottom: 8px;
            }}
            p {{
                line-height: 1.7;
                color: #34495e;
                margin-bottom: 15px;
            }}
            .highlight {{
                background: linear-gradient(120deg, #a8edea 0%, #fed6e3 100%);
                padding: 20px;
                border-radius: 12px;
                margin: 20px 0;
                border-left: 5px solid #e74c3c;
            }}
            .kpi-highlight {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 15px;
                border-radius: 10px;
                margin: 10px 0;
                text-align: center;
                font-weight: 600;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚚 Procurer Supply Chain Optimization Report</h1>
            <div class="section">
                <h2 class="section-title">1. Executive Summary</h2>
                <div class="explanation">
                    <p>This report presents a comprehensive, data-driven analysis of supply chain procurement using one or more solver methods. 
                    The analysis includes realistic modeling of lead times, distinguishing between when orders are placed (procurement) 
                    and when they arrive (shipments). All input data, model logic, and results are fully transparent for technical and executive review.</p>
                    
                    <div class="highlight">
                        <h3>Key Insights:</h3>
                        <ul>
                            <li><b>Procurement vs Shipments:</b> Orders are placed in advance considering lead times, with shipments arriving later</li>
                            <li><b>Safety Stock Management:</b> Minimum inventory levels are maintained throughout the planning horizon</li>
                            <li><b>Cost Optimization:</b> Total cost includes procurement, logistics, and holding costs</li>
                            <li><b>Constraint Satisfaction:</b> All demand must be met while respecting capacity and MOQ constraints</li>
                        </ul>
                    </div>
                </div>
            </div>
            {solver_explanation}
            <div class="section">
                <h2 class="section-title">3. Model Variables, Data & Assumptions</h2>
                {variables_explanation}
                <h3 class="subsection-title">Input Data Tables</h3>
                {products_table}
                {suppliers_table}
                {demand_table}
                {inventory_table}
                {logistics_table}
            </div>
            <div class="section">
                <h2 class="section-title">4. Key Performance Indicators (KPIs) & Evaluation</h2>
                {kpi_table}
            </div>
"""
    
    # Heuristic section with 2x2 plot layout
    if heuristic_solution and any(k in plot_files for k in ['heuristic_demand_supply', 'heuristic_inventory', 'heuristic_procurement']):
        html += f'''
        <div class="section">
            <h2 class="section-title">5. Heuristic Solver — Results Overview</h2>
            <div class="explanation">
                The following 2x2 plot layout shows the comprehensive supply chain plan determined by the Heuristic solver:
                <ul>
                    <li><b>Procurement Plan:</b> When orders are placed to suppliers (considering lead times)</li>
                    <li><b>Shipments Plan:</b> When orders actually arrive at the warehouse</li>
                    <li><b>Inventory Levels:</b> Stock levels throughout the planning horizon</li>
                    <li><b>Demand vs Supply:</b> Comparison of customer demand vs. available supply (shipments)</li>
                </ul>
            </div>
            <div class="plot-container">
                {create_2x2_plot_layout(plot_files, 'heuristic')}
            </div>
            <h3 class="subsection-title">Detailed Period-by-Period Results</h3>
            {render_table(["Product", "Supplier", "Period", "Inventory", "Demand", "Procurement Qty", "Shipment Qty"], build_solution_rows(heuristic_solution.get('procurement_plan', {}), heuristic_solution.get('inventory', {}), data.get('demand', []), heuristic_solution.get('shipments_plan', {})))}
        </div>
        '''
    
    # Linear section with 2x2 plot layout
    if linear_solution and any(k in plot_files for k in ['linear_demand_supply', 'linear_inventory', 'linear_procurement']):
        html += f'''
        <div class="section">
            <h2 class="section-title">6. Linear Solver (MILP) — Results Overview</h2>
            <div class="explanation">
                The following 2x2 plot layout shows the optimal supply chain plan determined by the Linear (MILP) solver:
                <ul>
                    <li><b>Procurement Plan:</b> When orders are placed to suppliers (considering lead times)</li>
                    <li><b>Shipments Plan:</b> When orders actually arrive at the warehouse</li>
                    <li><b>Inventory Levels:</b> Stock levels throughout the planning horizon</li>
                    <li><b>Demand vs Supply:</b> Comparison of customer demand vs. available supply (shipments)</li>
                </ul>
            </div>
            <div class="plot-container">
                {create_2x2_plot_layout(plot_files, 'linear')}
            </div>
            <h3 class="subsection-title">Detailed Period-by-Period Results</h3>
            {render_table(["Product", "Supplier", "Period", "Inventory", "Demand", "Procurement Qty", "Shipment Qty"], build_solution_rows(linear_solution.get('procurement_plan', {}), linear_solution.get('inventory', {}), data.get('demand', []), linear_solution.get('shipments_plan', {})))}
        </div>
        '''
    
    # Nonlinear section with 2x2 plot layout
    if nonlinear_solution and any(k in plot_files for k in ['nonlinear_demand_supply', 'nonlinear_inventory', 'nonlinear_procurement']):
        html += f'''
        <div class="section">
            <h2 class="section-title">7. Nonlinear Solver (Discounts) — Results Overview</h2>
            <div class="explanation">
                The following 2x2 plot layout shows the supply chain plan determined by the Nonlinear solver with quantity discounts:
                <ul>
                    <li><b>Procurement Plan:</b> When orders are placed to suppliers (considering lead times)</li>
                    <li><b>Shipments Plan:</b> When orders actually arrive at the warehouse</li>
                    <li><b>Inventory Levels:</b> Stock levels throughout the planning horizon</li>
                    <li><b>Demand vs Supply:</b> Comparison of customer demand vs. available supply (shipments)</li>
                </ul>
            </div>
            <div class="plot-container">
                {create_2x2_plot_layout(plot_files, 'nonlinear')}
            </div>
            <h3 class="subsection-title">Detailed Period-by-Period Results</h3>
            {render_table(["Product", "Supplier", "Period", "Inventory", "Demand", "Procurement Qty", "Shipment Qty"], build_solution_rows(nonlinear_solution.get('procurement_plan', {}), nonlinear_solution.get('inventory', {}), data.get('demand', []), nonlinear_solution.get('shipments_plan', {})))}
        </div>
        '''
    
    html += """
        </div>
    </body>
    </html>
    """
    if isinstance(output_dir, bytes):
        output_dir = output_dir.decode()
    report_path = os.path.join(output_dir, 'procurer_e2e_report.html')
    with open(report_path, 'w') as f:
        f.write(html)
    print(f"HTML report generated: {report_path}") 