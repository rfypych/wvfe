import requests
from urllib.parse import urljoin

# A list of common sensitive files and directories. This can be expanded.
SENSITIVE_PATHS = [
    ".env",
    ".env.local",
    "wp-config.php",
    ".git/config",
]

def check_sensitive_files(base_url, log_callback):
    """
    Checks for publicly exposed sensitive files on a target server.

    Args:
        base_url (str): The base URL of the target website.
        log_callback (function): A function to call for logging messages.

    Returns:
        list: A list of dictionaries, where each dictionary represents a
              found vulnerability.
    """
    found_vulnerabilities = []
    headers = {
        'User-Agent': 'WVFE/1.0 (Web Vulnerability Finder and Exploiter)'
    }

    log_callback(f"[*] Checking for sensitive files on {base_url}")

    for path in SENSITIVE_PATHS:
        full_url = urljoin(base_url, path)

        try:
            response = requests.get(full_url, headers=headers, timeout=5, verify=False)

            if response.status_code == 200:
                log_callback(f"[+] Found sensitive file: {full_url}")
                vulnerability = {
                    "type": "Sensitive Data Exposure",
                    "url": full_url,
                    "payload": "N/A",
                    "details": f"The file at {full_url} is publicly accessible (Status Code: 200)."
                }
                found_vulnerabilities.append(vulnerability)

        except requests.exceptions.RequestException:
            pass

    return found_vulnerabilities
