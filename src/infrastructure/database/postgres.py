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
                # Safety: ensure we never send a NULL `modified` value to the
                # datasets table (DB enforces NOT NULL). If an INSERT into
                # datasets is attempted and the `modified` parameter is None,
                # fallback to the `created` value (params layout defined in
                # PostgresDatasetRepository.add).
                if params and isinstance(params, (list, tuple)) and "INSERT INTO datasets" in (
                    query or ""
                ):
                    p = list(params)
                    # params ordering in add(): id, platform_id, buid, slug, page, publisher, created, modified, published, restricted
                    if len(p) >= 8 and p[7] is None:
                        p[7] = p[6]
                        params = tuple(p)
                cur.execute(query, params)
            except Exception as e:
                import traceback

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
