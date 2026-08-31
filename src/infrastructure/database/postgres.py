import psycopg2
import psycopg2.extras


class PostgresClient:
    def __init__(self, dbname, user, password, host="localhost", port=5432):
        self.conn_params = {
            "dbname": dbname,
            "user": user,
            "password": password,
            "host": host,
            "port": port,
        }
        self.connection = None
        self._connect()

    def _connect(self):
        if self.connection is not None and not self.connection.closed:
            try:
                self.connection.close()
            except Exception:
                pass
        self.connection = psycopg2.connect(**self.conn_params)
        self.connection.autocommit = False

    def _ensure_connection(self):
        if self.connection is None or self.connection.closed != 0:
            self._connect()

    def execute(self, query, params=None):
        """Execute a query without returning results (INSERT, UPDATE, DELETE)"""
        self._ensure_connection()
        try:
            with self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                try:
                    cur.execute(query, params)
                except Exception as e:
                    print(cur.mogrify(query, params))
                    print(e)
                    self.rollback()
                    raise e
        except (psycopg2.InterfaceError, psycopg2.OperationalError):
            self._connect()
            with self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                try:
                    cur.execute(query, params)
                except Exception as e:
                    print(cur.mogrify(query, params))
                    print(e)
                    self.rollback()
                    raise e

    def fetchone(self, query, params=None):
        """Execute a query and return a single result as a dict"""
        self._ensure_connection()
        try:
            with self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute(query, params)
                row = cur.fetchone()
                return dict(row) if row else None
        except (psycopg2.InterfaceError, psycopg2.OperationalError):
            self._connect()
            with self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute(query, params)
                row = cur.fetchone()
                return dict(row) if row else None

    def fetchall(self, query, params=None):
        """Execute a query and return all results as a list of dicts"""
        self._ensure_connection()
        try:
            with self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute(query, params)
                rows = cur.fetchall()
                return [dict(row) for row in rows]
        except (psycopg2.InterfaceError, psycopg2.OperationalError):
            self._connect()
            with self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute(query, params)
                rows = cur.fetchall()
                return [dict(row) for row in rows]

    def stream_fetchall(self, query, params=None, name="streaming_cursor"):
        """Execute a query using a server-side cursor to stream results (memory-efficient)"""
        self._ensure_connection()
        try:
            cur = self.connection.cursor(name=name, cursor_factory=psycopg2.extras.DictCursor)
            cur.itersize = 2000  # Fetch 2000 rows at a time
            cur.execute(query, params)
        except (psycopg2.InterfaceError, psycopg2.OperationalError):
            self._connect()
            cur = self.connection.cursor(name=name, cursor_factory=psycopg2.extras.DictCursor)
            cur.itersize = 2000
            cur.execute(query, params)
        for row in cur:
            yield dict(row)
        cur.close()

    def commit(self):
        if self.connection is not None and not self.connection.closed:
            self.connection.commit()

    def rollback(self):
        if self.connection is not None and not self.connection.closed:
            self.connection.rollback()

    def close(self):
        if self.connection is not None and not self.connection.closed:
            self.connection.close()
