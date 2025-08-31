import pytest
import json
from unittest.mock import patch, MagicMock, ANY
from app import app, bcrypt

@pytest.fixture
def client():
    """A test client for the app."""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        yield client

# --- Test API Endpoints ---

def test_start_scan_unauthorized(client):
    """Test that starting a scan requires login."""
    response = client.post('/api/scans', data=json.dumps({'target_url': 'http://example.com'}), content_type='application/json')
    assert response.status_code == 401

@patch('app.run_real_scan')
@patch('app.get_db_connection')
def test_start_scan_endpoint(mock_get_db, mock_run_scan, client):
    """Test that the start_scan endpoint correctly creates a DB record and calls the scanner function."""
    # --- Login Step ---
    mock_user_data_for_login = {'id': 1, 'username': 'testuser', 'password_hash': bcrypt.generate_password_hash('password').decode('utf-8')}
    mock_cursor_login = MagicMock()
    mock_cursor_login.fetchone.return_value = mock_user_data_for_login
    mock_get_db.return_value.cursor.return_value = mock_cursor_login

    login_response = client.post('/api/auth/login', data=json.dumps({'username': 'testuser', 'password': 'password'}), content_type='application/json')
    assert login_response.status_code == 200

    # --- Test Endpoint Step ---
    mock_cursor_scan = MagicMock()
    mock_cursor_scan.lastrowid = 123
    mock_get_db.return_value.cursor.return_value = mock_cursor_scan
    # This mock is for the @login_required decorator on the endpoint
    mock_cursor_scan.fetchone.return_value = {'id': 1, 'username': 'testuser'}

    response = client.post('/api/scans', data=json.dumps({'target_url': 'http://example.com'}), content_type='application/json')

    assert response.status_code == 202
    assert response.json['scan_id'] == 123
    mock_run_scan.assert_called_once_with(ANY, 123, 'http://example.com')


# --- Test Full Scan Logic ---

@patch('app.check_sqli')
@patch('app.check_sensitive_files')
@patch('app.crawl_site')
@patch('app.get_db_connection')
def test_run_real_scan_orchestration(mock_get_db, mock_crawl, mock_sensitive_scan, mock_sqli_scan):
    """Test that run_real_scan correctly orchestrates all modules."""
    from app import run_real_scan

    # --- Setup Mocks ---
    # Mock crawler results
    mock_crawl.return_value = {'links': {'http://test.com/page1'}, 'forms': []}
    # Mock scanner results
    mock_sensitive_scan.return_value = [{'type': 'Sensitive Data Exposure', 'url': 'http://test.com/.env', 'payload': 'N/A', 'details': '...'}]
    mock_sqli_scan.return_value = [{'type': 'SQL Injection', 'url': 'http://test.com/page1?id=1', 'payload': "'", 'details': '...'}]

    mock_cursor = mock_get_db.return_value.cursor.return_value

    # --- Execute ---
    run_real_scan(app.app_context(), scan_id=1, target_url='http://test.com')

    # --- Asserts ---
    # 1. Check that the orchestrator called all the necessary modules
    mock_crawl.assert_called_once_with('http://test.com')
    mock_sensitive_scan.assert_called_with('http://test.com/page1')
    mock_sqli_scan.assert_called_once_with({'links': {'http://test.com/page1'}, 'forms': []})

    # 2. Check that both vulnerabilities were inserted into the database
    assert mock_cursor.execute.call_count >= 4 # 1 for running, 2 for inserts, 1 for completed
    mock_cursor.execute.assert_any_call(
        "INSERT INTO vulnerabilities (scan_id, type, url, payload, details) VALUES (%s, %s, %s, %s, %s)",
        (1, 'Sensitive Data Exposure', 'http://test.com/.env', 'N/A', '...')
    )
    mock_cursor.execute.assert_any_call(
        "INSERT INTO vulnerabilities (scan_id, type, url, payload, details) VALUES (%s, %s, %s, %s, %s)",
        (1, 'SQL Injection', 'http://test.com/page1?id=1', "'", '...')
    )

    # 3. Check that the final status was set to 'completed'
    mock_cursor.execute.assert_any_call("UPDATE scans SET status = 'completed' WHERE id = %s", (1,))
