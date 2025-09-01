import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

def crawl_site(base_url, log_callback):
    """
    Crawls a website starting from the base_url to discover links and forms.

    Args:
        base_url (str): The starting URL to crawl.
        log_callback (function): A function to call for logging messages.

    Returns:
        dict: A dictionary with two keys: 'links' (a set of unique URLs found
              on the site) and 'forms' (a list of dictionaries, each
              representing a form).
    """
    base_netloc = urlparse(base_url).netloc

    urls_to_visit = {base_url}
    visited_urls = set()
    discovered_forms = []

    while urls_to_visit:
        url = urls_to_visit.pop()
        if url in visited_urls:
            continue

        visited_urls.add(url)
        log_callback(f"  -> Crawling: {url}")

        try:
            response = requests.get(url, timeout=5, verify=False, headers={'User-Agent': 'WVFE-Crawler/1.0'})
            if 'text/html' not in response.headers.get('Content-Type', ''):
                continue
        except requests.RequestException as e:
            log_callback(f"[!] Could not fetch {url}: {e}")
            continue

        soup = BeautifulSoup(response.text, 'html.parser')

        # Discover all links
        for a_tag in soup.find_all('a', href=True):
            link = urljoin(base_url, a_tag['href'])
            if urlparse(link).netloc == base_netloc and link not in visited_urls:
                urls_to_visit.add(link)

        # Discover all forms
        for form_tag in soup.find_all('form'):
            action = form_tag.get('action', '')
            method = form_tag.get('method', 'get').lower()
            form_url = urljoin(base_url, action)

            inputs = []
            for input_tag in form_tag.find_all(['input', 'textarea', 'select']):
                input_name = input_tag.get('name')
                input_type = input_tag.get('type', 'text')
                if input_name:
                    inputs.append({'name': input_name, 'type': input_type})

            discovered_forms.append({
                'url': form_url,
                'method': method,
                'inputs': inputs
            })

    return {
        'links': visited_urls,
        'forms': discovered_forms
    }
