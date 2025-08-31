import pytest
from unittest.mock import patch, MagicMock, ANY
from scanners.xss_scanner import check_xss, XSS_PAYLOADS

@patch('scanners.xss_scanner.requests.get')
def test_check_xss_on_url(mock_get):
    """Test finding a reflected XSS vulnerability in a URL parameter."""
    # We will test with the first payload from the scanner's list
    test_payload = XSS_PAYLOADS[0]

    # Mock the response to always reflect the payload, so we know the scanner will find it.
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = f"<html><body>Search results for: {test_payload}</body></html>"
    mock_get.return_value = mock_response

    # The target link should be clean
    targets = {
        'links': {'http://test.com/search?q=test'},
        'forms': []
    }

    vulnerabilities = check_xss(targets)

    # The scanner should find exactly one vulnerability because it stops after the first hit.
    assert len(vulnerabilities) == 1
    vuln = vulnerabilities[0]
    assert vuln['type'] == 'Reflected XSS'
    assert vuln['payload'] == test_payload

@patch('scanners.xss_scanner.requests.post')
def test_check_xss_on_form(mock_post):
    """Test finding a reflected XSS vulnerability in a form submission."""
    # We will test with the second payload to ensure the loop works
    test_payload = XSS_PAYLOADS[1]

    # Mock the response to only reflect the payload we are testing for
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

    vulnerabilities = check_xss(targets)

    assert len(vulnerabilities) == 1
    vuln = vulnerabilities[0]
    assert vuln['type'] == 'Reflected XSS'
    assert vuln['payload'] == test_payload

    mock_post.assert_any_call('http://test.com/login', data={'username': test_payload}, timeout=5, verify=False, headers=ANY)
