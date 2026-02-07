.PHONY: help install test coverage export-es clean clean-db docker-up docker-down dump load exec-db stats

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install-front: ## Install front-end dependencies
	cd front && npm install

install: ## Install dependencies and project in editable mode
	export PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1 && pip install --no-cache-dir -r requirements.txt
	export PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1 && pip install --no-cache-dir -e .
	$(MAKE) install-front

test: ## Run unit tests
	py.test

coverage: ## Run tests with coverage report
	pytest --cov=. --cov-report=html

export-es: ## Export SQLite DB (dev) to SQL
	sqlite3 db/writes-dev.db .dump > output.sql

clean: ## Clean temporary files and format code
	find . -name .DS_Store -print -delete
	black src tests
	isort .
	rm -rf htmlcov .coverage .pytest_cache

clean-db: ## Remove local dev data
	rm -rf db/dev/*

docker-up: ## Start database with Docker
	docker compose up --build -d

docker-down: ## Stop and remove database containers
	docker compose down --remove-orphans -v

dump: ## Create a database dump
	docker exec -t open-data-monitoring-db pg_dumpall -U postgres > dump.sql

load: ## Load database from dump.sql
	cat dump.sql | docker exec -i open-data-monitoring-db psql -U postgres

exec-db: ## Connect to database container via psql
	docker exec -it open-data-monitoring-db psql -U postgres -d postgres

stats: ## Run and push statistics
	./stats/stats.sh && python stats/push_stats.py
