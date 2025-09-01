import pytest
from unittest.mock import patch, MagicMock, ANY
from scanners.xss_scanner import check_xss, XSS_PAYLOADS

# A mock logging function to pass to the scanner
def mock_log_callback(message):
    print(f"LOG: {message}")

@patch('scanners.xss_scanner.requests.get')
def test_check_xss_on_url(mock_get):
    """Test finding a reflected XSS vulnerability in a URL parameter."""
    test_payload = XSS_PAYLOADS[0]

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = f"<html><body>Search results for: {test_payload}</body></html>"
    mock_get.return_value = mock_response

    targets = {
        'links': {'http://test.com/search?q=test'},
        'forms': []
    }

    vulnerabilities = check_xss(targets, mock_log_callback)

    assert len(vulnerabilities) == 1
    assert vulnerabilities[0]['payload'] == test_payload

@patch('scanners.xss_scanner.requests.post')
def test_check_xss_on_form(mock_post):
    """Test finding a reflected XSS vulnerability in a form submission."""
    test_payload = XSS_PAYLOADS[1]

    def response_side_effect(*args, **kwargs):
        data = kwargs.get('data', {})
        mock_res = MagicMock()
        mock_res.status_code = 200
        if data.get('username') == test_payload:
            mock_res.text = f"<html><body>Welcome, {test_payload}</body></html>"
        else:
            mock_res.text = "<html><body>Welcome, guest</body></html>"
        return mock_res

    mock_post.side_effect = response_side_effect

    targets = {
        'links': set(),
        'forms': [{
            'url': 'http://test.com/login',
            'method': 'post',
            'inputs': [{'name': 'username', 'type': 'text'}]
        }]
    }

    vulnerabilities = check_xss(targets, mock_log_callback)

    assert len(vulnerabilities) == 1
    assert vulnerabilities[0]['payload'] == test_payload
