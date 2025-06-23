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
	docker exec open-data-monitoring-db pg_dump -U postgres odm --create --clean --if-exists > /tmp/dump.sql
	docker cp open-data-monitoring-db:/tmp/dump.sql ./dump.sql

load:
	docker cp ./dump.sql open-data-monitoring-db:/tmp/dump.sql
	docker exec -u postgres -it open-data-monitoring-db psql -d postgres -f /tmp/dump.sql
