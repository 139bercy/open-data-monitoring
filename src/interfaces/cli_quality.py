"""CLI commands for metadata quality evaluation."""

import click
from rich.console import Console
from rich.table import Table

from application.services.quality_assessment import QualityAssessmentService
from infrastructure.llm.ollama_evaluator import OllamaEvaluator
from infrastructure.llm.openai_evaluator import OpenAIEvaluator
from logger import logger
from settings import app

console = Console()


@click.group("quality")
def cli_quality():
    """Metadata quality evaluation commands"""
    pass


@cli_quality.command("evaluate")
@click.argument("dataset_id")
@click.option("--dcat", default="docs/quality/dcat_reference.md", help="Path to DCAT reference markdown file")
@click.option("--charter", default="docs/quality/charter_opendata.md", help="Path to Open Data charter markdown file")
@click.option(
    "--provider",
    type=click.Choice(["openai", "ollama"]),
    default="openai",
    help="LLM provider to use (default: openai)",
)
@click.option("--model", default=None, help="Model to use (default: gpt-4o-mini for OpenAI, llama3.1 for Ollama)")
@click.option(
    "--output",
    type=click.Choice(["text", "json"]),
    default="json",
    help="Output format (default: json)",
)
@click.option(
    "--report",
    is_flag=True,
    help="Export to md file",
)
def cli_evaluate_quality(
    dataset_id: str, dcat: str, charter: str, provider: str, model: str | None, output: str, report: bool
):
    """Evaluate metadata quality for a dataset."""
    console.print(f"\n[bold]Evaluating dataset {dataset_id}...[/bold]\n")
    try:
        # Initialize evaluator based on provider
        if provider == "openai":
            evaluator = OpenAIEvaluator(model_name=model or "gpt-4o-mini")
        else:  # ollama
            evaluator = OllamaEvaluator(model_name=model or "llama3.1")

        service = QualityAssessmentService(evaluator=evaluator, uow=app.uow)

        # Run evaluation
        evaluation = service.evaluate_dataset(
            dataset_id=dataset_id, dcat_path=dcat, charter_path=charter, output=output
        )

        # Display results
        report = _display_evaluation(evaluation, output)
        if report:
            with open("report.md", "w") as file:
                file.write(report)
            console.print(f"[green]Evaluation has been exported to report.md")
    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        console.print(f"[red]Evaluation failed: {e}[/red]")


@cli_quality.command("report")
@click.argument("dataset_id")
def cli_quality_report(dataset_id: str):
    """Display quality report for a dataset (placeholder for future persistence)."""
    console.print(f"[yellow]Report command not yet implemented. Use 'evaluate' to run a new evaluation.[/yellow]")


def _display_evaluation(evaluation, output: str):
    """Display evaluation results in a formatted table."""
    # For text format, just print the raw text
    if output == "text":
        console.print("\n[bold]Audit Qualité Métadonnées[/bold]\n")
        console.print(evaluation.raw_text)
        return

    # For JSON format, display structured results
    # Overall score
    score_color = "green" if evaluation.overall_score >= 70 else "yellow" if evaluation.overall_score >= 50 else "red"
    console.print(f"\n[bold]Dataset:[/bold] {evaluation.dataset_slug}")
    console.print(f"[bold]Overall Score:[/bold] [{score_color}]{evaluation.overall_score:.1f}/100[/{score_color}]\n")

    # Criteria scores by category
    for category in ["descriptive", "administrative", "geotemporal"]:
        scores = evaluation.get_scores_by_category(category)
        if not scores:
            continue

        table = Table(title=f"{category.title()} Metadata")
        table.add_column("Criterion", style="cyan")
        table.add_column("Score", justify="right")
        table.add_column("Weight", justify="right")
        table.add_column("Issues", style="yellow")

        for score in scores:
            score_str = f"{score.score:.0f}/100"
            weight_str = f"{score.weight * 100:.0f}%"
            issues_str = "\n".join(score.issues) if score.issues else "✓"
            table.add_row(score.criterion, score_str, weight_str, issues_str)

        console.print(table)
        console.print()

    # High priority suggestions
    high_priority = evaluation.get_high_priority_suggestions()
    if high_priority:
        console.print("[bold red]High Priority Suggestions:[/bold red]\n")
        for i, suggestion in enumerate(high_priority, 1):
            console.print(f"{i}. [bold]{suggestion.field}[/bold]")
            console.print(f"   Current: {suggestion.current_value or 'N/A'}")
            console.print(f"   Suggested: [green]{suggestion.suggested_value}[/green]")
            console.print(f"   Reason: {suggestion.reason}\n")

    # All suggestions summary
    if evaluation.suggestions:
        console.print(f"[bold]Total Suggestions:[/bold] {len(evaluation.suggestions)}")
        console.print(f"  High: {len([s for s in evaluation.suggestions if s.priority == 'high'])}")
        console.print(f"  Medium: {len([s for s in evaluation.suggestions if s.priority == 'medium'])}")
        console.print(f"  Low: {len([s for s in evaluation.suggestions if s.priority == 'low'])}")
