import pytest
import json
from unittest.mock import patch, MagicMock

# Since we are in a different file, we need to adjust the import path
# We assume pytest is run with PYTHONPATH=backend
from app import app, bcrypt

@pytest.fixture
def client():
    app.config['TESTING'] = True
    # This is important for Flask-Login tests
    app.config['LOGIN_DISABLED'] = False
    with app.test_client() as client:
        yield client

# --- Registration Tests ---

@patch('app.get_db_connection')
def test_register_success(mock_get_db, client):
    """Test successful user registration."""
    # Mock the database connection and cursor
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_db.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor

    response = client.post('/api/auth/register',
                             data=json.dumps({'username': 'testuser', 'password': 'password'}),
                             content_type='application/json')

    assert response.status_code == 201
    assert response.json['status'] == 'success'
    mock_cursor.execute.assert_called_once()
    mock_conn.commit.assert_called_once()

@patch('app.get_db_connection')
def test_register_duplicate_user(mock_get_db, client):
    """Test registration with a username that already exists."""
    # Mock the database to raise a duplicate entry error
    from mysql.connector.errors import IntegrityError
    mock_get_db.return_value.cursor.return_value.execute.side_effect = IntegrityError(errno=1062)

    response = client.post('/api/auth/register',
                             data=json.dumps({'username': 'testuser', 'password': 'password'}),
                             content_type='application/json')

    assert response.status_code == 409
    assert response.json['message'] == 'Username already exists.'

# --- Login Tests ---

@patch('app.get_db_connection')
def test_login_success(mock_get_db, client):
    """Test successful user login."""
    # Mock the database to return a user
    mock_user_data = {
        'id': 1,
        'username': 'testuser',
        'password_hash': bcrypt.generate_password_hash('password').decode('utf-8')
    }
    mock_get_db.return_value.cursor.return_value.fetchone.return_value = mock_user_data

    response = client.post('/api/auth/login',
                             data=json.dumps({'username': 'testuser', 'password': 'password'}),
                             content_type='application/json')

    assert response.status_code == 200
    assert response.json['status'] == 'success'

@patch('app.get_db_connection')
def test_login_invalid_password(mock_get_db, client):
    """Test login with an incorrect password."""
    # Mock the database to return a user
    mock_user_data = {
        'id': 1,
        'username': 'testuser',
        'password_hash': bcrypt.generate_password_hash('password').decode('utf-8')
    }
    mock_get_db.return_value.cursor.return_value.fetchone.return_value = mock_user_data

    response = client.post('/api/auth/login',
                             data=json.dumps({'username': 'testuser', 'password': 'wrongpassword'}),
                             content_type='application/json')

    assert response.status_code == 401
    assert response.json['message'] == 'Invalid username or password.'

@patch('app.get_db_connection')
def test_login_user_not_found(mock_get_db, client):
    """Test login with a username that does not exist."""
    # Mock the database to return no user
    mock_get_db.return_value.cursor.return_value.fetchone.return_value = None

    response = client.post('/api/auth/login',
                             data=json.dumps({'username': 'nouser', 'password': 'password'}),
                             content_type='application/json')

    assert response.status_code == 401
    assert response.json['message'] == 'Invalid username or password.'
