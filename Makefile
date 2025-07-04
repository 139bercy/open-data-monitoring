install:
	pip install -r requirements.txt
	pip install -e .

test:
	py.test

coverage:
	pytest --cov=. --cov-report=html

export-es:
	sqlite3 db/writes-dev.db .dump > output.sql

clean:
	find . -name .DS_Store -print -delete
	black src tests
	isort .

clean-db:
	rm -rf db/dev/*

docker-up:
	docker compose up --build -d

docke r-down:
	docker compose down --remove-orphans -v

dump:
	docker exec -t open-data-monitoring-db pg_dumpall -U postgres > dump.sql

load:
	cat dump.sql | docker exec -i open-data-monitoring-db psql -U postgres

exec-db:
	docker exec -it open-data-monitoring-db psql -U postgres -d postgres
