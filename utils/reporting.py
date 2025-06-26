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
        plt.title(title, fontsize=14, color='#2c3e50')
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()
    print(f"Plot saved: {filename}")

def plot_procurement_plan(procurement_plan: Dict, filename: str, title: str, products_to_plot=None, moqs=None):
    data = defaultdict(lambda: defaultdict(float))
    for (product, supplier, period), qty in procurement_plan.items():
        data[(product, supplier)][period] += qty
    if products_to_plot is not None:
        data = {k: v for k, v in data.items() if k[0] in products_to_plot}
    for (product, supplier), period_qty in data.items():
        periods = sorted(period_qty.keys())
        quantities = [period_qty[p] for p in periods]
        plt.plot(periods, quantities, marker='o', label=f'{product}-{supplier}')
        # Plot MOQ line if provided
        if moqs and product in moqs:
            plt.axhline(moqs[product], color='red', linestyle='--', linewidth=1, label=f'MOQ {product}')
    plt.xlabel('Period', fontsize=12)
    plt.ylabel('Procurement Quantity', fontsize=12)
    plt.legend()
    save_plot(filename, title)

def plot_inventory_levels(inventory: Dict, filename: str, title: str, products_to_plot=None, safety_stocks=None):
    data = defaultdict(lambda: defaultdict(float))
    for (product, period), qty in inventory.items():
        data[product][period] += qty
    if products_to_plot is not None:
        data = {k: v for k, v in data.items() if k in products_to_plot}
    for product, period_qty in data.items():
        periods = sorted(period_qty.keys())
        quantities = [period_qty[p] for p in periods]
        plt.plot(periods, quantities, marker='o', label=product)
        # Plot safety stock line if provided
        if safety_stocks and product in safety_stocks:
            plt.axhline(safety_stocks[product], color='orange', linestyle='--', linewidth=1, label=f'Safety Stock {product}')
    plt.xlabel('Period', fontsize=12)
    plt.ylabel('Inventory Level', fontsize=12)
    plt.legend()
    save_plot(filename, title)

def plot_demand_vs_supply(demand: List[Any], procurement_plan: Dict, filename: str, title: str, products_to_plot=None):
    demand_map = defaultdict(float)
    for d in demand:
        demand_map[(d.product_id, d.period)] += d.expected_quantity
    supply_map = defaultdict(float)
    for (product, supplier, period), qty in procurement_plan.items():
        supply_map[(product, period)] += qty
    products = sorted(set(p for p, _ in demand_map.keys()))
    if products_to_plot is not None:
        products = [p for p in products if p in products_to_plot]
    periods = sorted(set(t for _, t in demand_map.keys()))
    for product in products:
        d_vals = [demand_map[(product, t)] for t in periods]
        s_vals = [supply_map[(product, t)] for t in periods]
        plt.plot(periods, d_vals, label=f'Demand {product}', linestyle='--')
        plt.plot(periods, s_vals, label=f'Supply {product}', marker='o')
    plt.xlabel('Period', fontsize=12)
    plt.ylabel('Quantity', fontsize=12)
    plt.legend()
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
        "total_procurement_cost": "Total cost of all products purchased (excludes holding/logistics)",
        "service_level": "Fraction of demand fulfilled (1.0 = all demand met)",
        "inventory_turnover": "How many times inventory is used up per period (higher = more efficient)",
        "obsolescence": "Stock left at end that was not used (risk of waste)"
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

    # Variable/assumption explanation
    variables_explanation = """
    <div class="explanation">
      <h2>Variables & Assumptions</h2>
      <ul>
        <li><b>Products:</b> Each product has a unique ID, name, cost per supplier, shelf life (expiration), and minimum order quantity (MOQ).</li>
        <li><b>Suppliers:</b> Each supplier offers certain products, with minimum order values and lead times per product.</li>
        <li><b>Demand:</b> Forecasted for each product and period. Assumed to be known and deterministic for this scenario.</li>
        <li><b>Inventory:</b> Initial stock, holding cost, warehouse capacity, and <b>safety stock</b> (minimum required inventory at all times) for each product.</li>
        <li><b>Logistics Cost:</b> Per-unit and fixed costs for each supplier-product pair.</li>
      </ul>
      <b>Assumptions:</b>
      <ul>
        <li>All demand must be met on time (no backorders allowed).</li>
        <li>Products do not expire within the planning horizon (shelf life &gt; periods).</li>
        <li>All suppliers are reliable and always deliver as planned.</li>
        <li>Costs and demand are deterministic (no uncertainty modeled here).</li>
        <li>Safety stock is strictly enforced: inventory at end of each period must be at least the safety stock level.</li>
      </ul>
      <b>Variable Details:</b>
      <ul>
        <li><b>product_id</b>: Unique product identifier.</li>
        <li><b>supplier_id</b>: Unique supplier identifier.</li>
        <li><b>period</b>: Integer time index (e.g., 1, 2, 3, ...).</li>
        <li><b>initial_stock</b>: Starting inventory for each product.</li>
        <li><b>holding_cost</b>: Cost per unit per period for holding inventory.</li>
        <li><b>warehouse_capacity</b>: Maximum inventory allowed for each product.</li>
        <li><b>safety_stock</b>: Minimum inventory required for each product at all times (buffer against uncertainty).</li>
        <li><b>unit_cost_by_supplier</b>: Cost per unit for each product from each supplier.</li>
        <li><b>MOQ</b>: Minimum order quantity for each product.</li>
        <li><b>minimum_order_value</b>: Minimum order value per supplier per order.</li>
        <li><b>lead_times</b>: Number of periods between order and delivery for each product-supplier pair.</li>
        <li><b>cost_per_unit</b>: Logistics cost per unit shipped.</li>
        <li><b>fixed_cost</b>: Fixed logistics cost per shipment.</li>
      </ul>
    </div>
    """
    # Plain-language solver explanation
    solver_explanation = f"""
    <div class='section'>
      <h2 class='section-title'>2. Solver Logic & Approach</h2>
      <div class='explanation'>
        <b>Solvers Activated in This Report:</b> <span style='color:#1976d2;font-weight:bold'>{solvers_run_str}</span><br><br>
        <b>Linear Solver (MILP):</b>
        <ul>
          <li>Finds the optimal procurement and inventory plan by minimizing total cost (procurement, logistics, holding).</li>
          <li>Respects all constraints: demand fulfillment, inventory balance, warehouse capacity, safety stock, shelf life, and minimum order quantity (MOQ).</li>
          <li>Uses a mathematical programming solver to guarantee the best solution for the given data.</li>
        </ul>
        <b>Nonlinear Solver (NLP with Discounts):</b>
        <ul>
          <li>Similar to the linear solver, but models quantity discounts: if you buy more than a threshold, you get a lower price for the extra units.</li>
          <li>Minimizes total cost, including the effect of discounts, using a nonlinear optimization approach.</li>
        </ul>
        <b>Heuristic Solver:</b>
        <ul>
          <li>Works period by period, fulfilling demand and safety stock from the cheapest available supplier.</li>
          <li>Fast and simple, but may not find the absolute best solution.</li>
          <li>Applies discounts greedily if order quantity exceeds the discount threshold.</li>
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
        ["ID", "Name", "Products Offered", "Min Order Value", "Lead Times"],
        [[s.id, s.name, ', '.join(s.products_offered), s.minimum_order_value, json.dumps(s.lead_times)] for s in data.get('suppliers', [])]
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
    # Helper for detailed results tables
    def build_solution_rows(procurement_plan, inventory, demand):
        rows = []
        for (i, j, t), v in procurement_plan.items():
            w = inventory.get((i, t), 0)
            x = next((d.expected_quantity for d in demand if d.product_id == i and d.period == t), 0)
            rows.append([i, j, t, v, w, x])
        # Sort ascending by product, supplier, period
        rows.sort(key=lambda row: (row[0], row[1], row[2]))
        return rows
    html = f"""
    <html>
    <head>
        <title>Procurer Supply Chain Optimization Report</title>
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 40px; background: #f4f6fa; }}
            h1 {{ color: #1976d2; font-size: 2.5em; margin-bottom: 0.2em; }}
            h2.section-title {{ color: #1976d2; font-size: 2em; margin-top: 1.5em; margin-bottom: 0.5em; border-bottom: 2px solid #1976d2; padding-bottom: 0.2em; }}
            h3.subsection-title {{ color: #2c3e50; font-size: 1.3em; margin-top: 1.2em; margin-bottom: 0.5em; }}
            .section {{ margin-bottom: 48px; padding: 24px 28px; background: #fff; border-radius: 10px; box-shadow: 0 2px 12px #e3e3e3; }}
            img {{ max-width: 520px; margin: 18px 18px 18px 0; border: 2px solid #1976d2; border-radius: 6px; box-shadow: 2px 2px 10px #cfd8dc; display: inline-block; vertical-align: top; }}
            .explanation {{ background: #e3f2fd; padding: 22px; border-radius: 10px; margin-bottom: 36px; border-left: 7px solid #1976d2; }}
            .data-table {{ border-collapse: collapse; margin: 18px 0 36px 0; width: 100%; background: #fff; }}
            .data-table th, .data-table td {{ border: 1px solid #bbb; padding: 10px 16px; text-align: left; }}
            .data-table th {{ background: #1976d2; color: #fff; }}
        </style>
    </head>
    <body>
        <h1>Procurer Supply Chain Optimization Report</h1>
        <div class="section">
            <h2 class="section-title">1. Executive Summary</h2>
            <div class="explanation">
                This report presents a comprehensive, data-driven analysis of supply chain procurement using one or more solver methods. All input data, model logic, and results are fully transparent for technical and executive review.
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
    # Heuristic section
    if heuristic_solution and any(k in plot_files for k in ['heuristic_demand_supply', 'heuristic_inventory', 'heuristic_procurement']):
        html += f'''
        <div class="section">
            <h2 class="section-title">5. Heuristic Solver — Results Overview</h2>
            <div class="explanation">The following plots and table summarize the procurement, inventory, and demand fulfillment plan as determined by the baseline Heuristic solver.</div>
            {f'<img src="{img_to_base64(plot_files["heuristic_demand_supply"])}" alt="Heuristic Solver: Demand vs Supply">' if 'heuristic_demand_supply' in plot_files else ''}
            {f'<img src="{img_to_base64(plot_files["heuristic_inventory"])}" alt="Heuristic Solver: Inventory Levels">' if 'heuristic_inventory' in plot_files else ''}
            {f'<img src="{img_to_base64(plot_files["heuristic_procurement"])}" alt="Heuristic Solver: Procurement Plan">' if 'heuristic_procurement' in plot_files else ''}
            <h3 class="subsection-title">Detailed Period-by-Period Results</h3>
            {render_table(["Product", "Supplier", "Period", "Procurement Qty", "Inventory", "Demand"], build_solution_rows(heuristic_solution.get('procurement_plan', {}), heuristic_solution.get('inventory', {}), data.get('demand', [])))}
        </div>
        '''
    # Linear section
    if linear_solution and any(k in plot_files for k in ['linear_demand_supply', 'linear_inventory', 'linear_procurement']):
        html += f'''
        <div class="section">
            <h2 class="section-title">6. Linear Solver (MILP) — Results Overview</h2>
            <div class="explanation">The following plots and table summarize the optimal procurement, inventory, and demand fulfillment plan as determined by the Linear (MILP) solver.</div>
            {f'<img src="{img_to_base64(plot_files["linear_demand_supply"])}" alt="Linear Solver: Demand vs Supply">' if 'linear_demand_supply' in plot_files else ''}
            {f'<img src="{img_to_base64(plot_files["linear_inventory"])}" alt="Linear Solver: Inventory Levels">' if 'linear_inventory' in plot_files else ''}
            {f'<img src="{img_to_base64(plot_files["linear_procurement"])}" alt="Linear Solver: Procurement Plan">' if 'linear_procurement' in plot_files else ''}
            <h3 class="subsection-title">Detailed Period-by-Period Results</h3>
            {render_table(["Product", "Supplier", "Period", "Procurement Qty", "Inventory", "Demand"], build_solution_rows(linear_solution.get('procurement_plan', {}), linear_solution.get('inventory', {}), data.get('demand', [])))}
        </div>
        '''
    # Nonlinear section
    if nonlinear_solution and any(k in plot_files for k in ['nonlinear_demand_supply', 'nonlinear_inventory', 'nonlinear_procurement']):
        html += f'''
        <div class="section">
            <h2 class="section-title">7. Nonlinear Solver (Discounts) — Results Overview</h2>
            <div class="explanation">The following plots and table summarize the procurement, inventory, and demand fulfillment plan as determined by the Nonlinear solver with quantity discounts.</div>
            {f'<img src="{img_to_base64(plot_files["nonlinear_demand_supply"])}" alt="Nonlinear Solver: Demand vs Supply">' if 'nonlinear_demand_supply' in plot_files else ''}
            {f'<img src="{img_to_base64(plot_files["nonlinear_inventory"])}" alt="Nonlinear Solver: Inventory Levels">' if 'nonlinear_inventory' in plot_files else ''}
            {f'<img src="{img_to_base64(plot_files["nonlinear_procurement"])}" alt="Nonlinear Solver: Procurement Plan">' if 'nonlinear_procurement' in plot_files else ''}
            <h3 class="subsection-title">Detailed Period-by-Period Results</h3>
            {render_table(["Product", "Supplier", "Period", "Procurement Qty", "Inventory", "Demand"], build_solution_rows(nonlinear_solution.get('procurement_plan', {}), nonlinear_solution.get('inventory', {}), data.get('demand', [])))}
        </div>
        '''
    html += """
    </body>
    </html>
    """
    if isinstance(output_dir, bytes):
        output_dir = output_dir.decode()
    report_path = os.path.join(output_dir, 'procurer_e2e_report.html')
    with open(report_path, 'w') as f:
        f.write(html)
    print(f"HTML report generated: {report_path}") 