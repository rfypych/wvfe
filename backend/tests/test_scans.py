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

def test_start_scan_unauthorized(client):
    """Test that starting a scan requires login."""
    response = client.post('/api/scans', data=json.dumps({'target_url': 'http://example.com'}), content_type='application/json')
    assert response.status_code == 401

@patch('app.run_real_scan')
@patch('app.get_db_connection')
def test_start_scan_endpoint(mock_get_db, mock_run_scan, client):
    """Test that the start_scan endpoint correctly creates a DB record and calls the scanner function."""
    # --- Login Step ---
    mock_cursor_login = MagicMock()
    mock_user_data_for_login = {'id': 1, 'username': 'testuser', 'password_hash': bcrypt.generate_password_hash('password').decode('utf-8')}
    mock_cursor_login.fetchone.return_value = mock_user_data_for_login
    mock_get_db.return_value.cursor.return_value = mock_cursor_login

    login_response = client.post('/api/auth/login', data=json.dumps({'username': 'testuser', 'password': 'password'}), content_type='application/json')
    assert login_response.status_code == 200

    # --- Test Step ---
    mock_cursor_scan = MagicMock()
    mock_cursor_scan.lastrowid = 123
    mock_user_data_for_loader = {'id': 1, 'username': 'testuser'}
    # The first fetchone will be for the user loader
    mock_cursor_scan.fetchone.return_value = mock_user_data_for_loader
    mock_get_db.return_value.cursor.return_value = mock_cursor_scan

    response = client.post('/api/scans', data=json.dumps({'target_url': 'http://example.com'}), content_type='application/json')

    assert response.status_code == 202
    assert response.json['scan_id'] == 123

    mock_cursor_scan.execute.assert_any_call(
        "INSERT INTO scans (user_id, target_url) VALUES (%s, %s)",
        (1, 'http://example.com')
    )
    mock_run_scan.assert_called_once_with(ANY, 123, 'http://example.com')


@patch('scanners.sensitive_file_scanner.requests.get')
@patch('app.get_db_connection')
def test_run_real_scan_finds_vulnerability(mock_get_db, mock_requests_get):
    """Test the run_real_scan function to ensure it finds a vulnerability and updates the DB."""
    from app import run_real_scan

    # --- Setup Mocks ---
    mock_response_ok = MagicMock(status_code=200)
    mock_requests_get.return_value = mock_response_ok
    mock_cursor = mock_get_db.return_value.cursor.return_value

    # --- Execute ---
    run_real_scan(app.app_context(), scan_id=1, target_url='http://example.com')

    # --- Asserts ---
    mock_cursor.execute.assert_any_call("UPDATE scans SET status = 'running' WHERE id = %s", (1,))
    mock_cursor.execute.assert_any_call(
        "INSERT INTO vulnerabilities (scan_id, type, url, payload, details) VALUES (%s, %s, %s, %s, %s)",
        (1, 'Sensitive Data Exposure', 'http://example.com/.env', 'N/A', ANY)
    )
    mock_cursor.execute.assert_any_call("UPDATE scans SET status = 'completed' WHERE id = %s", (1,))
    assert mock_get_db.return_value.commit.call_count >= 2
    mock_requests_get.assert_any_call('http://example.com/.env', headers=ANY, timeout=ANY, verify=False)
