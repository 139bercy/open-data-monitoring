install:
	pip install -r requirements.txt
	pip install -e .

test:
	py.test

coverage:
	pytest --cov=. --cov-report=html

export-es:
	sqlite3 db/writes-dev.db .dump > output.sql

clean-db:
	rm -rf db/dev/*