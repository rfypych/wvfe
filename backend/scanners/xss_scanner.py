import requests
from urllib.parse import urlparse, parse_qs, urlencode

# A list of simple, non-malicious XSS payloads for detection
XSS_PAYLOADS = [
    "<script>alert('WVFE-XSS-TEST')</script>",
    "'\"<img src=x onerror=alert('WVFE-XSS-TEST')>",
    "<svg/onload=alert('WVFE-XSS-TEST')>",
]

def check_xss(targets, log_callback):
    """
    Checks for reflected Cross-Site Scripting (XSS) vulnerabilities.

    Args:
        targets (dict): A dictionary from the crawler containing 'links' and 'forms'.
        log_callback (function): A function to call for logging messages.

    Returns:
        list: A list of dictionaries, where each dictionary represents a
              found vulnerability.
    """
    found_vulnerabilities = []

    # --- Test URLs with query parameters ---
    for url in targets.get('links', set()):
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        if not query_params:
            continue

        log_callback(f"[*] Testing XSS on URL: {url}")
        for param, values in query_params.items():
            for payload in XSS_PAYLOADS:
                test_params = query_params.copy()
                test_params[param] = payload
                test_query = urlencode(test_params, doseq=True)
                test_url = parsed_url._replace(query=test_query).geturl()

                try:
                    response = requests.get(test_url, timeout=5, verify=False, headers={'User-Agent': 'WVFE-Scanner/1.0'})
                    if payload in response.text:
                        log_callback(f"[+] Found potential XSS in {test_url} (param: {param})")
                        vulnerability = {
                            "type": "Reflected XSS",
                            "url": test_url,
                            "payload": payload,
                            "details": f"The parameter '{param}' seems to be vulnerable to reflected XSS. The payload was found in the server's response."
                        }
                        found_vulnerabilities.append(vulnerability)
                        break
                except requests.RequestException:
                    pass

    # --- Test HTML Forms ---
    for form in targets.get('forms', []):
        form_url = form['url']
        form_method = form['method']
        form_inputs = form['inputs']

        log_callback(f"[*] Testing XSS on form at: {form_url}")

        data = {i['name']: 'test' for i in form_inputs if i['name']}

        for input_to_test in form_inputs:
            if input_to_test.get('type') not in ('text', 'search', 'textarea'):
                continue

            for payload in XSS_PAYLOADS:
                test_data = data.copy()
                test_data[input_to_test['name']] = payload

                try:
                    if form_method == 'post':
                        response = requests.post(form_url, data=test_data, timeout=5, verify=False, headers={'User-Agent': 'WVFE-Scanner/1.0'})
                    else:
                        response = requests.get(form_url, params=test_data, timeout=5, verify=False, headers={'User-Agent': 'WVFE-Scanner/1.0'})

                    if payload in response.text:
                        log_callback(f"[+] Found potential XSS in form at {form_url} (input: {input_to_test['name']})")
                        vulnerability = {
                            "type": "Reflected XSS",
                            "url": form_url,
                            "payload": payload,
                            "details": f"The form input '{input_to_test['name']}' seems to be vulnerable to reflected XSS. The payload was found in the server's response."
                        }
                        found_vulnerabilities.append(vulnerability)
                        break
                except requests.RequestException:
                    pass

    return found_vulnerabilities
