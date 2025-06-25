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

docker-down:
	docker compose down --remove-orphans -v

dump:
	docker exec -i open-data-monitoring-db /bin/bash -c "PGPASSWORD=password pg_dump --username postgres odm" > /tmp/dump.sql
	cp /tmp/dump.sql ./dump.sql

load:
	docker exec -i open-data-monitoring-db /bin/bash -c "PGPASSWORD=password psql --username postgres postgres" < ./dump.sql

exec-db:
	docker exec -it open-data-monitoring-db psql -U postgres -d postgres
