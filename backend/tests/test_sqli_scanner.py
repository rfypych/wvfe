import pytest
import re
from unittest.mock import patch, MagicMock
from scanners.sqli_scanner import check_sqli, _get_column_count, _extract_data_with_union

# A mock logging function to pass to the scanner
def mock_log_callback(message):
    print(f"LOG: {message}")

# --- Test Helper Functions Directly ---

@patch('scanners.sqli_scanner.requests.Session')
def test_get_column_count(MockSession):
    """Test the _get_column_count helper function."""
    mock_session = MockSession.return_value
    mock_ok_response = MagicMock(text="OK")
    mock_fail_response = MagicMock(text="Unknown column '3'")

    def side_effect(url, params, **kwargs):
        if params['id'] == "1' ORDER BY 3-- ":
            return mock_fail_response
        return mock_ok_response

    mock_session.get.side_effect = side_effect

    count = _get_column_count(mock_session, 'http://test.com', 'get', mock_log_callback, params={'id':'1'})
    assert count == 2

@patch('scanners.sqli_scanner.requests.Session')
def test_extract_data_with_union(MockSession):
    """Test the _extract_data_with_union helper function."""
    mock_session = MockSession.return_value
    db_version = "10.4.13-MariaDB"
    mock_response = MagicMock(text=f"Some content WVFE-START{db_version}WVFE-END more content")
    mock_session.get.return_value = mock_response

    data = _extract_data_with_union(mock_session, 'http://test.com', 'get', 2, mock_log_callback, params={'id':'1'})

    assert data is not None
    assert data['Version'] == db_version

# --- Test Main Orchestration Function ---

@patch('scanners.sqli_scanner._extract_data_with_union')
@patch('scanners.sqli_scanner._get_column_count')
@patch('scanners.sqli_scanner.requests.Session')
def test_check_sqli_orchestration(MockSession, mock_get_cols, mock_extract_data):
    """
    Test that check_sqli correctly calls helper functions after finding an error.
    """
    mock_session = MockSession.return_value
    mock_session.get.return_value = MagicMock(text="SQL syntax.*MySQL")

    mock_get_cols.return_value = 3
    mock_extract_data.return_value = {"Version": "mocked_version"}

    targets = {'links': {'http://test.com/vuln?id=1'}, 'forms': []}
    vulnerabilities = check_sqli(targets, mock_log_callback)

    assert len(vulnerabilities) == 1
    mock_get_cols.assert_called_once()
    mock_extract_data.assert_called_once()
