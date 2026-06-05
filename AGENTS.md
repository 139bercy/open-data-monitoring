# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build and Development Commands

### Backend (Python)
- **Install dependencies**: `make install`
- **Run unit tests**: `make test`
- **Run tests with coverage**: `make coverage`
- **Lint and format code**: `make lint`
- **Run API**: `python src/run_api.py`

### Frontend (Node.js)
- **Run frontend**: `./front/run_front.sh`

### Database (Docker/PostgreSQL)
- **Start database**: `make docker-up`
- **Stop database**: `make docker-down`
- **Create DB dump**: `make dump`
- **Load DB from dump**: `make load`
- **Connect to DB**: `make exec-db`

### CLI Tool
The application provides a CLI via the `app` command.
- **General help**: `app --help`
- **Platform management**: `app platform all`, `app platform create ...`
- **Dataset management**: `app dataset add <url>`
- **AI Quality evaluation**: `app quality evaluate <dataset_id> [--report]`

## Code Architecture

The project follows a layered architecture (Clean Architecture/DDD inspired) to separate business logic from technical implementation.

### Core Layers (`src/`)
- **`domain/`**: The heart of the application. Contains business entities, domain services, and the core logic for monitoring and AI quality evaluation.
- **`application/`**: Orchestrates the flow of data. Contains use cases, commands, DTOs, and handlers that implement specific application features.
- **`infrastructure/`**: Technical implementations. Includes database repositories, LLM adapters (OpenAI, Gemini, Ollama), security configurations, and external API adapters.
- **`interfaces/`**: Entry points to the application.
    - `api/`: REST API endpoints.
    - `cli.py`, `cli_quality.py`, `cli_impact.py`: Command-line interface implementations.

### Other Key Directories
- **`front/`**: React-based frontend application.
- **`scripts/`**: Utility scripts for various automation tasks.
- **`stats/`**: Logic for generating and pushing statistics.
- **`deployment/`**: Systemd service configurations and deployment scripts.
