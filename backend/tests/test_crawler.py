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

    # Create a mock logging function
    mock_log_callback = MagicMock()

    result = crawl_site(base_url, mock_log_callback)

    # Check discovered links
    assert len(result['links']) == 2

    # Check that the logger was called
    mock_log_callback.assert_any_call('  -> Crawling: http://test.com')
    mock_log_callback.assert_any_call('  -> Crawling: http://test.com/about.html')
