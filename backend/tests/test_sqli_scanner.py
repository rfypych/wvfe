import pytest
from unittest.mock import patch, MagicMock, ANY
from scanners.sqli_scanner import check_sqli

@patch('scanners.sqli_scanner.requests.get')
def test_check_sqli_on_url(mock_get):
    """Test finding an error-based SQLi vulnerability in a URL parameter."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "Error: You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version..."
    mock_get.return_value = mock_response

    targets = {
        'links': {'http://test.com/search?q=test'},
        'forms': []
    }

    vulnerabilities = check_sqli(targets)

    assert len(vulnerabilities) == 1
    vuln = vulnerabilities[0]
    assert vuln['type'] == 'SQL Injection (MySQL Error)'
    # The scanner URL-encodes the payload
    assert vuln['url'] == "http://test.com/search?q=test%27"
    assert vuln['payload'] == "'"

    mock_get.assert_called_once_with("http://test.com/search?q=test%27", timeout=5, verify=False, headers=ANY)

@patch('scanners.sqli_scanner.requests.post')
def test_check_sqli_on_form(mock_post):
    """Test finding an error-based SQLi vulnerability in a form submission."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "ORA-01756: quoted string not properly terminated"
    mock_post.return_value = mock_response

    targets = {
        'links': set(),
        'forms': [{
            'url': 'http://test.com/login',
            'method': 'post',
            'inputs': [{'name': 'username', 'type': 'text'}, {'name': 'password', 'type': 'password'}]
        }]
    }

    vulnerabilities = check_sqli(targets)

    assert len(vulnerabilities) >= 1
    vuln = vulnerabilities[0]
    assert vuln['type'] == 'SQL Injection (Oracle Error)'
    assert vuln['url'] == 'http://test.com/login'
    assert vuln['payload'] == "'"

    mock_post.assert_any_call('http://test.com/login', data={'username': "test'", 'password': 'test'}, timeout=5, verify=False, headers=ANY)
