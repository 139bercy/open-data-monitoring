#!/usr/bin/env python3
"""
Script pour lancer l'audit qualité par LLM (Albert API par défaut)
sur tous les jeux de données publiés et non restreints d'une plateforme donnée.

Usage:
    # Lancer sur data.economie.gouv.fr avec Albert API (par défaut)
    python scripts/evaluate_platform_datasets.py

    # Mode test sur les 5 premiers datasets
    python scripts/evaluate_platform_datasets.py --limit 5

    # Voir les datasets ciblés sans lancer l'évaluation (dry-run)
    python scripts/evaluate_platform_datasets.py --dry-run

    # Forcer la ré-évaluation des datasets déjà audités
    python scripts/evaluate_platform_datasets.py --force

    # Spécifier un autre modèle ou délai
    python scripts/evaluate_platform_datasets.py --model AgentPublic/albert-light-rag-1.1 --delay 1.0
"""

import argparse
import sys
import time
from pathlib import Path

# Ajouter src/ au PYTHONPATH
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "src"))

from dotenv import load_dotenv

load_dotenv(BASE_DIR / ".env")

from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

from application.services.quality_assessment import QualityAssessmentService
from infrastructure.llm import AlbertEvaluator, GeminiEvaluator, OllamaEvaluator, OpenAIEvaluator
from settings import app

console = Console()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Évalue la qualité des métadonnées pour tous les datasets publiés et non restreints d'une plateforme."
    )
    parser.add_argument(
        "--domain",
        default="data.economie.gouv.fr",
        help="Domaine ou URL de la plateforme cible (défaut: data.economie.gouv.fr)",
    )
    parser.add_argument(
        "--provider",
        choices=["albert", "openai", "gemini", "ollama"],
        default="albert",
        help="Fournisseur LLM (défaut: albert)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Nom du modèle LLM à utiliser",
    )
    parser.add_argument(
        "--prompt-type",
        choices=["standard", "light"],
        default="standard",
        help="Type de prompt (défaut: standard)",
    )
    parser.add_argument(
        "--dcat",
        default=str(BASE_DIR / "docs/quality/dcat_reference.md"),
        help="Chemin vers le référentiel DCAT",
    )
    parser.add_argument(
        "--charter",
        default=str(BASE_DIR / "docs/quality/charter_opendata.md"),
        help="Chemin vers la charte Open Data",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Nombre maximum de jeux de données à traiter",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="Délai en secondes entre deux requêtes API (défaut: 0.5s)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Réévaluer les jeux de données déjà évalués",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Lister les datasets sans exécuter l'évaluation LLM",
    )
    return parser.parse_args()


def get_platform(domain: str):
    """Recherche la plateforme par domaine ou URL."""
    with app.uow:
        # Recherche directe par repository
        platform = app.uow.platforms.get_by_domain(domain)
        if not platform:
            # Recherche souple par SQL
            rows = app.uow.client.fetchall(
                "SELECT id, name, slug, url, type FROM platforms WHERE url ILIKE %s OR slug ILIKE %s LIMIT 1",
                (f"%{domain}%", f"%{domain}%"),
            )
            if rows:
                platform = app.uow.platforms.get(rows[0]["id"])
        return platform


def get_target_datasets(platform_id, force: bool = False, limit: int | None = None):
    """Récupère les jeux de données publiés, non restreints et non supprimés."""
    with app.uow:
        query = """
            SELECT d.id, d.slug, d.title, d.published, d.restricted, d.deleted,
                   (dq.evaluation_results IS NOT NULL) AS already_evaluated,
                   dq.health_quality_score, dq.health_score
            FROM datasets d
            LEFT JOIN dataset_quality dq ON d.id = dq.dataset_id
            WHERE d.platform_id = %s
              AND d.published IS TRUE
              AND (d.restricted IS FALSE OR d.restricted IS NULL)
              AND (d.deleted IS FALSE OR d.deleted IS NULL)
        """
        if not force:
            query += " AND (dq.evaluation_results IS NULL)"

        query += " ORDER BY d.modified DESC"

        if limit:
            query += f" LIMIT {int(limit)}"

        rows = app.uow.client.fetchall(query, (str(platform_id),))
        return rows


def init_evaluator(provider: str, model: str | None):
    """Instancie l'évaluateur LLM adéquat."""
    if provider == "albert":
        return AlbertEvaluator(model_name=model)
    elif provider == "openai":
        return OpenAIEvaluator(model_name=model or "gpt-4o-mini")
    elif provider == "gemini":
        return GeminiEvaluator(model_name=model or "gemini-1.5-pro")
    elif provider == "ollama":
        return OllamaEvaluator(model_name=model or "llama3.1")
    raise ValueError(f"Provider non reconnu: {provider}")


def main():
    args = parse_args()

    console.print(f"[bold cyan]🔍 Recherche de la plateforme '{args.domain}'...[/bold cyan]")
    platform = get_platform(args.domain)
    if not platform:
        console.print(f"[bold red]❌ Plateforme non trouvée pour '{args.domain}'.[/bold red]")
        sys.exit(1)

    console.print(
        f"[green]✔ Plateforme identifiée :[/green] [bold]{platform.name}[/bold] (ID: {platform.id}, Slug: {platform.slug})"
    )

    datasets = get_target_datasets(platform.id, force=args.force, limit=args.limit)
    total_count = len(datasets)

    if total_count == 0:
        console.print("[yellow]ℹ Aucun jeu de données à évaluer (tous déjà évalués ou critères non remplis).[/yellow]")
        console.print("[dim]Astuce : Utilisez '--force' pour réévaluer les datasets existants.[/dim]")
        return

    console.print(
        f"[bold blue]📊 {total_count} jeu(x) de données ciblé(s)[/bold blue] (Publiés: OUI, Restreints: NON, Déjà évalués: {'Inclus' if args.force else 'Exclus'})"
    )

    if args.dry_run:
        table = Table(title=f"Datasets ciblés sur {platform.name}")
        table.add_column("Slug", style="cyan")
        table.add_column("Titre", style="white")
        table.add_column("Déjà évalué", style="yellow")
        for d in datasets[:50]:
            table.add_row(
                d["slug"],
                (d["title"] or "")[:40],
                "Oui" if d["already_evaluated"] else "Non",
            )
        console.print(table)
        if total_count > 50:
            console.print(f"[dim]... et {total_count - 50} autres datasets.[/dim]")
        console.print("[yellow]Mode dry-run actif: aucune évaluation exécutée.[/yellow]")
        return

    try:
        evaluator = init_evaluator(args.provider, args.model)
        console.print(
            f"[bold green]🤖 Évaluateur initialisé :[/bold green] [magenta]{evaluator.__class__.__name__}[/magenta] (Modèle: {evaluator.model_name})"
        )
    except Exception as e:
        console.print(f"[bold red]❌ Erreur initialisation LLM : {e}[/bold red]")
        sys.exit(1)

    service = QualityAssessmentService(evaluator=evaluator, uow=app.uow, mappers=app.mappers)

    success_count = 0
    failure_count = 0
    scores = []

    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("({task.completed}/{task.total})"),
        TimeElapsedColumn(),
        console=console,
    )

    with progress:
        task = progress.add_task("[cyan]Évaluation en cours...", total=total_count)

        for dataset_row in datasets:
            slug = dataset_row["slug"]
            dataset_id = dataset_row["id"]
            progress.update(task, description=f"[cyan]Évaluation de [bold]{slug[:30]}[/bold]...")

            try:
                eval_res = service.evaluate_dataset(
                    dataset_id=dataset_id,
                    dcat_path=args.dcat,
                    charter_path=args.charter,
                    output="json",
                    prompt_type=args.prompt_type,
                )
                success_count += 1
                scores.append(eval_res.overall_score)
            except Exception as e:
                failure_count += 1
                console.print(f"[red]❌ Échec pour {slug} : {e}[/red]")

            progress.advance(task)
            if args.delay > 0:
                time.sleep(args.delay)

    avg_score = (sum(scores) / len(scores)) if scores else 0.0
    console.print("\n[bold green]🎉 Traitement terminé ![/bold green]")
    console.print(f"  • Succès : [green]{success_count}[/green]")
    console.print(f"  • Échecs : [red]{failure_count}[/red]")
    console.print(f"  • Score moyen de qualité : [bold cyan]{avg_score:.1f}/100[/bold cyan]\n")


if __name__ == "__main__":
    main()
