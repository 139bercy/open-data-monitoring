test:
	py.test

export-es:
	sqlite3 db/writes-dev.db .dump > output.sql

clean-db:
	rm -rf db/dev/*