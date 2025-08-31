import pytest
from unittest.mock import patch, MagicMock, ANY
from scanners.crawler import crawl_site

@patch('scanners.crawler.requests.get')
def test_crawl_site_finds_links_and_forms(mock_get):
    """Test that the crawler can find links and forms in simple HTML."""
    base_url = 'http://test.com'

    # Mock the response for the base URL
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {'Content-Type': 'text/html'}
    mock_response.text = """
    <html>
        <body>
            <a href="/about.html">About Us</a>
            <a href="https://external.com">External Link</a>
            <form action="/login" method="post">
                <input type="text" name="username">
                <input type="password" name="password">
            </form>
        </body>
    </html>
    """

    # Mock the response for the "/about.html" page
    mock_about_response = MagicMock()
    mock_about_response.status_code = 200
    mock_about_response.headers = {'Content-Type': 'text/html'}
    mock_about_response.text = "<html><body>About page</body></html>"

    mock_get.side_effect = [mock_response, mock_about_response]

    result = crawl_site(base_url)

    # Check discovered links
    assert len(result['links']) == 2
    assert 'http://test.com/about.html' in result['links']

    # Check discovered forms
    assert len(result['forms']) == 1

    # Check that we didn't follow the external link
    assert mock_get.call_count == 2
    mock_get.assert_any_call('http://test.com', timeout=5, verify=False, headers=ANY)
    mock_get.assert_any_call('http://test.com/about.html', timeout=5, verify=False, headers=ANY)
