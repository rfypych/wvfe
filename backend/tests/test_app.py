import pytest
from unittest.mock import patch
from app import app as flask_app

@pytest.fixture
def app():
    yield flask_app

@pytest.fixture
def client(app):
    return app.test_client()

def test_index(client):
    """Test the index page."""
    rv = client.get('/')
    assert rv.status_code == 200
    assert b"WVFE - Web Vulnerability Finder and Exploiter" in rv.data

def test_scan(client):
    """Test the scan page."""
    rv = client.post('/scan', data={'url': 'http://example.com'})
    assert rv.status_code == 200
    assert b"Scanning http://example.com..." in rv.data

def test_db_connection_failure(client):
    """Test the database connection endpoint for the failure case."""
    # This test relies on the fact that get_db_connection will return None
    # when it cannot connect, which is the case in the test environment.
    rv = client.get('/db_test')
    assert rv.status_code == 500
    json_data = rv.get_json()
    assert json_data['status'] == 'error'
    assert 'database connection failed' in json_data['message'].lower()

def test_db_connection_success_mocked(client):
    """Test the db_test endpoint with a mocked successful connection."""
    with patch('app.get_db_connection') as mock_get_db:
        # Mock the connection object. The actual object doesn't matter for this test,
        # as long as it's not None. We also need to mock the close() method.
        mock_conn = mock_get_db.return_value
        mock_conn.close.return_value = None

        rv = client.get('/db_test')
        assert rv.status_code == 200
        json_data = rv.get_json()
        assert json_data['status'] == 'success'
        # Check that our mock was called
        mock_get_db.assert_called_once()
        mock_conn.close.assert_called_once()
