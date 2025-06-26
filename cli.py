import click
from utils.logging import get_logger
from utils.validation import validate_data
from utils.data_loader import load_all_data
from solvers.linear import LinearSolver
from solvers.heuristic import HeuristicSolver

logger = get_logger("CLI")

def get_data_paths(products, suppliers, demand, inventory, logistics_cost):
    return {
        'products': products,
        'suppliers': suppliers,
        'demand': demand,
        'inventory': inventory,
        'logistics_cost': logistics_cost
    }

@click.group()
def cli():
    """Procurer CLI: Supply Chain Optimization System"""
    pass

@cli.command()
@click.option('--products', type=click.Path(exists=True), required=True, help='Path to products JSON file.')
@click.option('--suppliers', type=click.Path(exists=True), required=True, help='Path to suppliers JSON file.')
@click.option('--demand', type=click.Path(exists=True), required=True, help='Path to demand JSON file.')
@click.option('--inventory', type=click.Path(exists=True), required=True, help='Path to inventory JSON file.')
@click.option('--logistics-cost', type=click.Path(exists=True), required=True, help='Path to logistics cost JSON file.')
def solve_linear(products, suppliers, demand, inventory, logistics_cost):
    """Run the linear MILP solver."""
    paths = get_data_paths(products, suppliers, demand, inventory, logistics_cost)
    data = load_all_data(paths)
    validate_data(data)
    solver = LinearSolver()
    solution = solver.solve(data)
    click.echo(f"Solution: {solution}")

@cli.command()
@click.option('--products', type=click.Path(exists=True), required=True, help='Path to products JSON file.')
@click.option('--suppliers', type=click.Path(exists=True), required=True, help='Path to suppliers JSON file.')
@click.option('--demand', type=click.Path(exists=True), required=True, help='Path to demand JSON file.')
@click.option('--inventory', type=click.Path(exists=True), required=True, help='Path to inventory JSON file.')
@click.option('--logistics-cost', type=click.Path(exists=True), required=True, help='Path to logistics cost JSON file.')
def solve_heuristic(products, suppliers, demand, inventory, logistics_cost):
    """Run the heuristic solver."""
    paths = get_data_paths(products, suppliers, demand, inventory, logistics_cost)
    data = load_all_data(paths)
    validate_data(data)
    solver = HeuristicSolver()
    solution = solver.solve(data)
    click.echo(f"Solution: {solution}")

if __name__ == '__main__':
    cli() 