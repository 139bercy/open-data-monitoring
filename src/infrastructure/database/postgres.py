import psycopg2
import psycopg2.extras


class PostgresClient:
    def __init__(self, dbname, user, password, host="localhost", port=5432):
        self.connection = psycopg2.connect(
            dbname=dbname, user=user, password=password, host=host, port=port
        )
        self.connection.autocommit = False

    def execute(self, query, params=None):
        """Execute a query without returning results (INSERT, UPDATE, DELETE)"""
        with self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            try:
                cur.execute(query, params)
            except Exception as e:
                print(cur.mogrify(query, params))
                print(e)
                self.rollback()

    def fetchone(self, query, params=None):
        """Execute a query and return a single result as a dict"""
        with self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(query, params)
            row = cur.fetchone()
            return dict(row) if row else None

    def fetchall(self, query, params=None):
        """Execute a query and return all results as a list of dicts"""
        with self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(query, params)
            rows = cur.fetchall()
            return [dict(row) for row in rows]

    def commit(self):
        self.connection.commit()

    def rollback(self):
        self.connection.rollback()

    def close(self):
        self.connection.close()
