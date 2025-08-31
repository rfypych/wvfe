import pytest
import json
from unittest.mock import patch
from app import app, User, bcrypt

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_index(client):
    """Test the main API endpoint."""
    rv = client.get('/')
    assert rv.status_code == 200
    assert b"Welcome to the WVFE API" in rv.data

def test_dashboard_unauthorized(client):
    """Test that the dashboard requires login."""
    rv = client.get('/api/dashboard')
    assert rv.status_code == 401

@patch('app.get_db_connection')
def test_dashboard_after_login(mock_get_db, client):
    """Test accessing the dashboard after a successful login."""
    # --- Mock database for the login process ---
    mock_user_data = {
        'id': 1,
        'username': 'testuser',
        'password_hash': bcrypt.generate_password_hash('password').decode('utf-8')
    }
    # Configure the mock cursor
    mock_cursor = mock_get_db.return_value.cursor.return_value
    mock_cursor.fetchone.return_value = mock_user_data

    # --- Step 1: Log in the user ---
    login_response = client.post('/api/auth/login',
                                 data=json.dumps({'username': 'testuser', 'password': 'password'}),
                                 content_type='application/json')
    assert login_response.status_code == 200

    # --- Step 2: Access the dashboard with the session cookie ---
    dashboard_response = client.get('/api/dashboard')

    # Assert that we can now access the protected route
    assert dashboard_response.status_code == 200
    assert dashboard_response.json['status'] == 'success'
    assert 'testuser' in dashboard_response.json['message']
