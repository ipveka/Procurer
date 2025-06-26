import streamlit as st
import pandas as pd
from app_utils import (
    load_and_validate_data, run_solver, get_kpis,
    get_procurement_plot, get_inventory_plot, get_demand_vs_supply_plot,
    get_available_products, filter_products
)
import matplotlib.pyplot as plt
import time
import io

# --- App Config ---
st.set_page_config(
    page_title="Procurer Supply Chain Optimization",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for layout and centering tables ---
st.markdown("""
    <style>
    .block-container { padding-top: 2rem; }
    .centered-table { display: flex; justify-content: center; }
    .centered-table .stDataFrame { margin-left: auto; margin-right: auto; }
    .stDataFrame th, .stDataFrame td { text-align: center !important; }
    </style>
    """, unsafe_allow_html=True)

# --- Title and Subtitle ---
st.markdown("<h1 style='text-align:center;'>Procurer 🚚</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align:center; margin-top:-18px;'>Supply Chain Optimization</h3>", unsafe_allow_html=True)

# --- Sidebar: User Controls ---
st.sidebar.title("Controls")
st.sidebar.markdown("""
**Solver options:**
- Linear (MILP): Optimal
- Nonlinear (NLP): Discounts
- Heuristic: Fast baseline
""")
# Solver selection
solver_options = ["linear", "nonlinear", "heuristic"]
solver_labels = {
    "linear": "Linear (MILP)",
    "nonlinear": "Nonlinear (NLP with Discounts)",
    "heuristic": "Heuristic"
}
default_solvers = ["linear"]
selected_solvers = st.sidebar.multiselect(
    "Solvers to run:",
    options=solver_options,
    format_func=lambda x: solver_labels[x],
    default=default_solvers
)
# Product selection
all_products = get_available_products(load_and_validate_data())
selected_products = st.sidebar.multiselect(
    "Products to optimize:",
    options=all_products,
    default=all_products
)

# --- Animation state for progress bar ---
if 'show_animation' not in st.session_state:
    st.session_state['show_animation'] = False

# --- Initialize active tab state ---
if 'active_tab' not in st.session_state:
    st.session_state['active_tab'] = 0

def start_animation():
    """Set animation state to True when running solvers."""
    st.session_state['show_animation'] = True

def stop_animation():
    """Set animation state to False after solvers finish."""
    st.session_state['show_animation'] = False

run_btn = st.sidebar.button("Run Solvers", type="primary", on_click=start_animation)

# --- Data Loading and Filtering ---
data = load_and_validate_data()
filtered_data = filter_products(data, selected_products)

# --- Solver Execution (only if button pressed) ---
results = {}
kpis = {}
if st.session_state.get('show_animation', False) and run_btn and selected_solvers:
    with st.spinner("🚚 Optimizing your supply chain... Please wait!"):
        # Progress bar with moving truck emoji
        progress_placeholder = st.empty()
        truck_placeholder = st.empty()
        n_steps = 30
        for i in range(n_steps + 1):
            progress = i / n_steps
            bar = "<div style='width:100%;background:#eee;border-radius:8px;height:32px;position:relative;'>"
            bar += f"<div style='width:{progress*100:.1f}%;background:#1976d2;height:32px;border-radius:8px 0 0 8px;'></div>"
            bar += f"<div style='position:absolute;left:{progress*100:.1f}%;top:0;transform:translate(-50%,0);font-size:2rem;'>🚚</div>"
            bar += "</div>"
            progress_placeholder.markdown(bar, unsafe_allow_html=True)
            time.sleep(0.03)
        progress_placeholder.empty()
        truck_placeholder.empty()
        # Run each selected solver and collect results
        for solver in selected_solvers:
            solution = run_solver(solver, filtered_data)
            results[solver] = solution
            kpis[solver] = get_kpis(solution, filtered_data)
    stop_animation()

# --- Tabs Layout: Main App Sections ---
# Create tabs and capture the selected index
tab_names = ["Introduction", "Data Explorer", "Optimization", "Analysis"]
selected_tab = st.tabs(tab_names)

# Track which tab is currently active based on user interaction
# Note: Streamlit doesn't provide direct access to active tab index, 
# so we'll use a workaround with radio buttons in sidebar for tab navigation
st.sidebar.markdown("---")
st.sidebar.markdown("**Quick Navigation:**")
selected_tab_index = st.sidebar.radio(
    "Jump to tab:",
    options=range(len(tab_names)),
    format_func=lambda x: tab_names[x],
    index=st.session_state.get('active_tab', 0),
    key='tab_selector'
)

# Update active tab state
if selected_tab_index != st.session_state.get('active_tab', 0):
    st.session_state['active_tab'] = selected_tab_index

# --- Introduction Tab ---
with selected_tab[0]:
    if st.session_state.get('active_tab', 0) == 0 or selected_tab_index == 0:
        st.header("Introduction")
        st.subheader("What is Procurer?")
        st.markdown("""
        **Procurer** is a professional, modular supply chain optimization system for multi-period, multi-product, multi-supplier procurement planning. It empowers supply chain, operations, and finance teams to:
        - Optimize procurement and inventory across multiple products, suppliers, and time periods
        - Analyze and compare different solver methodologies (exact, nonlinear, heuristic)
        - Visualize procurement, inventory, and demand fulfillment plans
        - Explore all input data, constraints, and assumptions in detail
        - Make data-driven, transparent, and auditable supply chain decisions
        
        **Problems it solves:**
        - How much to order, from which supplier, and when, to minimize total cost while meeting demand and respecting constraints (capacity, safety stock, MOQ, discounts, etc.)
        - How to compare optimal, discounted, and heuristic (fast, human-like) approaches
        - How to understand the impact of safety stock, MOQ, and discounts on cost and service level
        
        **Data used:**
        - Products, suppliers, demand forecasts, inventory policies, logistics costs
        - All data is fully visible and explorable in the Data Explorer tab
        
        **Solver methodologies:**
        - **Linear (MILP):** Finds the optimal plan, respects all constraints (demand, inventory, safety stock, MOQ, etc.)
        - **Nonlinear (NLP):** Like linear, but models quantity discounts for bulk orders
        - **Heuristic:** Fast, simple, period-by-period, not always optimal, but interpretable and quick
        
        **Constraints:**
        - All constraints in the model are **hard constraints** (must be satisfied): demand fulfillment, inventory balance, warehouse capacity, safety stock, shelf life, and MOQ.
        - In some advanced scenarios, **soft constraints** (penalties for violations) can be used for flexibility or robustness, e.g., allowing small backorders or exceeding capacity with a cost penalty.
        
        **Assumptions:**
        - All demand must be met on time (no backorders allowed).
        - Products do not expire within the planning horizon (shelf life > periods).
        - All suppliers are reliable and always deliver as planned.
        - Costs and demand are deterministic (no uncertainty modeled here).
        - Safety stock is strictly enforced: inventory at end of each period must be at least the safety stock level.
        
        **How to use this app:**
        1. Select solvers and products in the sidebar
        2. Explore the input data in the Data Explorer tab
        3. Click 'Run Solvers' in the sidebar
        4. Review KPIs and detailed results in the Optimization tab
        5. Analyze and compare visualizations in the Analysis tab
        
        **Transparency & Best Practices:**
        - All logic, data, and results are fully transparent and documented
        - KPIs and plots help you understand cost, service level, inventory, and risk
        - Use the exact solver for strategic planning, the nonlinear for discount scenarios, and the heuristic for quick operational decisions
        """)

# --- Data Explorer Tab ---
with selected_tab[1]:
    if st.session_state.get('active_tab', 0) == 1 or selected_tab_index == 1:
        st.header("Data Explorer")
        # Show all input data tables with centered formatting
        st.subheader("Products")
        st.markdown('<div class="centered-table">', unsafe_allow_html=True)
        st.dataframe(pd.DataFrame([p.dict() for p in data['products']]), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        st.subheader("Suppliers")
        st.markdown('<div class="centered-table">', unsafe_allow_html=True)
        st.dataframe(pd.DataFrame([s.dict() for s in data['suppliers']]), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        st.subheader("Demand Forecast")
        st.markdown('<div class="centered-table">', unsafe_allow_html=True)
        st.dataframe(pd.DataFrame([d.dict() for d in data['demand']]), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        st.subheader("Inventory Policy")
        st.markdown('<div class="centered-table">', unsafe_allow_html=True)
        st.dataframe(pd.DataFrame([i.dict() for i in data['inventory']]), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        st.subheader("Logistics Cost")
        st.markdown('<div class="centered-table">', unsafe_allow_html=True)
        st.dataframe(pd.DataFrame([l.dict() for l in data['logistics_cost']]), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("**Constraints:** All constraints in the model are **hard constraints** (must be satisfied): demand fulfillment, inventory balance, warehouse capacity, safety stock, shelf life, and MOQ. In advanced scenarios, **soft constraints** (penalties for violations) can be used for flexibility or robustness, e.g., allowing small backorders or exceeding capacity with a cost penalty.\n\n**Assumptions:** All demand is met on time (no backorders), deterministic costs/demand, safety stock enforced, reliable suppliers.")

# --- Optimization Tab ---
with selected_tab[2]:
    if st.session_state.get('active_tab', 0) == 2 or selected_tab_index == 2:
        st.header("Optimization")
        if not st.session_state.get('show_animation', False) and not results:
            st.info("Select your solvers and products in the sidebar, then click 'Run Solvers' to see results.")
        elif not selected_solvers:
            st.warning("Please select at least one solver in the sidebar.")
        else:
            st.subheader("Key Performance Indicators (KPIs)")
            # Show KPI table for each solver
            kpi_expl = {
                "Total Procurement Cost": "Sum of all procurement quantities × unit cost (across all products, suppliers, periods). Lower is better, but not at the expense of service level.",
                "Service Level": "Total supplied / total demand (should be 1.0 if all demand is met).",
                "Inventory Turnover": "Total demand / average inventory (higher = more efficient use of stock).",
                "Obsolescence": "Inventory left after 4+ periods (risk of waste; should be low)."
            }
            kpi_rows = []
            for solver in selected_solvers:
                label = solver_labels[solver]
                k = kpis.get(solver, {})
                if k:
                    kpi_rows.append([
                        label,
                        f"{k.get('total_procurement_cost', ''):.2f}" if 'total_procurement_cost' in k else '',
                        f"{k.get('service_level', ''):.2f}" if 'service_level' in k else '',
                        f"{k.get('inventory_turnover', ''):.2f}" if 'inventory_turnover' in k else '',
                        f"{k.get('obsolescence', ''):.2f}" if 'obsolescence' in k else ''
                    ])
            if kpi_rows:
                kpi_df = pd.DataFrame(kpi_rows, columns=["Solver", "Total Procurement Cost", "Service Level", "Inventory Turnover", "Obsolescence"])
                st.table(kpi_df)
                with st.expander("KPI Explanations"):
                    for k, v in kpi_expl.items():
                        st.markdown(f"- **{k}:** {v}")
            # For each solver, show the detailed results table only (no plots)
            for solver in selected_solvers:
                label = solver_labels[solver]
                solution = results.get(solver, {})
                if not solution:
                    continue
                st.subheader(f"{label} — Detailed Results Table")
                rows = []
                for (i, j, t), v in solution['procurement_plan'].items():
                    w = solution['inventory'].get((i, t), 0)
                    x = next((d.expected_quantity for d in filtered_data['demand'] if d.product_id == i and d.period == t), 0)
                    rows.append([i, j, t, w, x, v])  # Procurement planned as rightmost column
                rows.sort(key=lambda row: (row[0], row[1], row[2]))
                detail_df = pd.DataFrame(rows, columns=["Product", "Supplier", "Period", "Inventory", "Demand", "Procurement Qty"])
                st.dataframe(detail_df, use_container_width=True)

# --- Analysis Tab ---
with selected_tab[3]:
    if st.session_state.get('active_tab', 0) == 3 or selected_tab_index == 3:
        st.header("Analysis")
        if not st.session_state.get('show_animation', False) and not results:
            st.info("Run solvers from the sidebar to see analysis plots.")
        else:
            for solver in selected_solvers:
                label = solver_labels[solver]
                solution = results.get(solver, {})
                if not solution:
                    continue
                st.subheader(f"{label} — Visualization")
                
                # Display plots directly using st.pyplot() - no PNG conversion
                cols = st.columns(3)
                
                with cols[0]:
                    fig1 = get_demand_vs_supply_plot(filtered_data['demand'], solution['procurement_plan'])
                    fig1.set_size_inches(5, 4)
                    st.pyplot(fig1)
                    st.caption("Demand vs. Supply")
                    plt.close(fig1)  # Clean up memory
                
                with cols[1]:
                    fig2 = get_inventory_plot(solution['inventory'])
                    fig2.set_size_inches(5, 4)
                    st.pyplot(fig2)
                    st.caption("Inventory Levels")
                    plt.close(fig2)  # Clean up memory
                
                with cols[2]:
                    fig3 = get_procurement_plot(solution['procurement_plan'])
                    fig3.set_size_inches(5, 4)
                    st.pyplot(fig3)
                    st.caption("Procurement Plan")
                    plt.close(fig3)  # Clean up memory
                
                # Add some spacing between different solvers
                if solver != selected_solvers[-1]:  # Not the last solver
                    st.markdown("---")

# --- Footer ---
st.markdown("---")
st.caption("Procurer | Professional Supply Chain Optimization | Streamlit App | MIT License")