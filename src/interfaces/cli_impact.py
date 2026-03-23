"""CLI commands for dataset impact reporting."""

import click
from rich.console import Console
from uuid import UUID
from application.services.report import ReportGenerator
from logger import logger
from settings import app

console = Console()


@click.group("impact")
def cli_impact():
    """Dataset impact and attendance commands"""
    pass


@cli_impact.command("report")
@click.argument("dataset_id")
@click.option("--output", default=None, help="Output path for the PDF report")
def cli_generate_impact_report(dataset_id: str, output: str | None):
    """Generate a business-oriented impact report (PDF) for a dataset."""
    console.print(f"\n[bold]Generating impact report for {dataset_id}...[/bold]\n")
    try:
        with app.uow:
            # Resolve ID/Slug
            uid = None
            try:
                uid = UUID(dataset_id)
            except ValueError:
                uid = app.uow.datasets.get_id_by_slug_globally(dataset_id)

            if not uid:
                console.print(f"[red]Error: Dataset {dataset_id} not found.[/red]")
                return

            # Get dataset with versions
            dataset = app.uow.datasets.get(uid)
            if not dataset:
                console.print(f"[red]Error: Dataset {uid} not found in repository.[/red]")
                return

            # Note: The repository.get() should ideally include versions. 
            # If not, we might need a specific method.
            # Let's check if versions are loaded.
            if not dataset.versions:
                # Try to load versions explicitly if repo doesn't do it by default
                dataset.versions, _ = app.uow.datasets.get_versions(uid, page=1, page_size=100)

            generator = ReportGenerator()
            pdf_buffer = generator.generate_impact_report(dataset)

            out_path = output or f"impact_report_{dataset.slug}.pdf"
            with open(out_path, "wb") as f:
                f.write(pdf_buffer.getbuffer())

            console.print(f"[green]Success! Impact report generated: [bold]{out_path}[/bold][/green]")

    except Exception as e:
        logger.error(f"Impact report generation failed: {e}")
        console.print(f"[red]Failed to generate report: {e}[/red]")
