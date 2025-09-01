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

@patch('app.get_db_connection')
def test_get_scan_logs_endpoint(mock_get_db, client):
    """Test the endpoint for fetching scan logs."""
    # --- Login Step ---
    mock_user_data_for_login = {'id': 1, 'username': 'testuser', 'password_hash': bcrypt.generate_password_hash('password').decode('utf-8')}
    mock_get_db.return_value.cursor.return_value.fetchone.return_value = mock_user_data_for_login
    login_response = client.post('/api/auth/login', data=json.dumps({'username': 'testuser', 'password': 'password'}), content_type='application/json')
    assert login_response.status_code == 200

    # --- Test Step ---
    mock_cursor = mock_get_db.return_value.cursor.return_value
    # 1. First fetchone call will be from load_user
    mock_user_data_for_loader = {'id': 1, 'username': 'testuser'}
    # 2. Second fetchone call will be from get_scan_logs for the ownership check
    mock_scan_ownership_data = {'user_id': 1}
    mock_cursor.fetchone.side_effect = [mock_user_data_for_loader, mock_scan_ownership_data]

    # Mock for the actual log data
    mock_cursor.fetchall.return_value = [{'timestamp': '2023-01-01', 'message': 'Scan started'}]

    response = client.get('/api/scans/1/logs')
    assert response.status_code == 200
    assert len(response.json) == 1
    assert response.json[0]['message'] == 'Scan started'


# --- Test Full Scan Logic ---

@patch('app.log_to_db')
@patch('app.check_xss')
@patch('app.check_sqli')
@patch('app.check_sensitive_files')
@patch('app.crawl_site')
@patch('app.get_db_connection')
def test_run_real_scan_orchestration(mock_get_db, mock_crawl, mock_sensitive_scan, mock_sqli_scan, mock_xss_scan, mock_log_db):
    """Test that run_real_scan correctly orchestrates all modules and logs messages."""
    from app import run_real_scan

    # --- Setup Mocks ---
    mock_crawl.return_value = {'links': set(), 'forms': []}
    mock_sensitive_scan.return_value = []
    mock_sqli_scan.return_value = []
    mock_xss_scan.return_value = []

    # --- Execute ---
    run_real_scan(app.app_context(), scan_id=1, target_url='http://test.com')

    # --- Asserts ---
    # Check that logging was called at key points
    mock_log_db.assert_any_call(1, 'Starting real scan on http://test.com')
    mock_log_db.assert_any_call(1, 'Starting web crawler...')
    mock_log_db.assert_any_call(1, '--- Running Sensitive File Scan ---')
    mock_log_db.assert_any_call(1, '--- Running SQL Injection Scan ---')
    mock_log_db.assert_any_call(1, '--- Running XSS Scan ---')
    mock_log_db.assert_any_call(1, 'Scan completed. Found 0 total vulnerabilities.')

    # Check that the final status was set to 'completed'
    mock_get_db.return_value.cursor.return_value.execute.assert_any_call("UPDATE scans SET status = 'completed' WHERE id = %s", (1,))
