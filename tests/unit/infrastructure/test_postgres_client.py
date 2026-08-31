from unittest.mock import MagicMock, patch

import psycopg2

from infrastructure.database.postgres import PostgresClient


def test_postgres_client_reconnects_when_closed():
    with patch("psycopg2.connect") as mock_connect:
        mock_conn1 = MagicMock()
        mock_conn1.closed = 0
        mock_conn2 = MagicMock()
        mock_conn2.closed = 0

        mock_connect.side_effect = [mock_conn1, mock_conn2]

        client = PostgresClient("testdb", "user", "pass")
        assert client.connection == mock_conn1

        # Simulate connection closure
        mock_conn1.closed = 1

        # Calling _ensure_connection should trigger reconnection
        client._ensure_connection()
        assert client.connection == mock_conn2
        assert mock_connect.call_count == 2


def test_postgres_client_retry_on_interface_error():
    with patch("psycopg2.connect") as mock_connect:
        mock_conn1 = MagicMock()
        mock_conn1.closed = 0
        mock_cur1 = MagicMock()
        mock_cur1.execute.side_effect = psycopg2.InterfaceError("connection already closed")
        mock_conn1.cursor.return_value.__enter__.return_value = mock_cur1

        mock_conn2 = MagicMock()
        mock_conn2.closed = 0
        mock_cur2 = MagicMock()
        mock_cur2.fetchone.return_value = {"id": 1, "name": "test"}
        mock_conn2.cursor.return_value.__enter__.return_value = mock_cur2

        mock_connect.side_effect = [mock_conn1, mock_conn2]

        client = PostgresClient("testdb", "user", "pass")
        result = client.fetchone("SELECT * FROM users WHERE id = %s", (1,))

        assert result == {"id": 1, "name": "test"}
        assert mock_connect.call_count == 2
