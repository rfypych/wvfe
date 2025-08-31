import requests
from urllib.parse import urljoin

# A list of common sensitive files and directories. This can be expanded.
SENSITIVE_PATHS = [
    ".env",
    ".env.local",
    ".env.production",
    "wp-config.php",
    "wp-admin/maint.php",
    "web.config",
    "Dockerfile",
    "docker-compose.yml",
    ".git/config",
    ".git/HEAD",
    "/.svn/entries",
    "/.hg/dirstate",
    "/.bash_history",
    "/.ssh/id_rsa",
    "/.aws/credentials",
    "/.aws/config",
    "access_log",
    "error_log",
    "phpinfo.php",
]

def check_sensitive_files(base_url):
    """
    Checks for publicly exposed sensitive files on a target server.

    Args:
        base_url (str): The base URL of the target website.

    Returns:
        list: A list of dictionaries, where each dictionary represents a
              found vulnerability.
    """
    found_vulnerabilities = []
    headers = {
        'User-Agent': 'WVFE/1.0 (Web Vulnerability Finder and Exploiter)'
    }

    print(f"[*] Starting sensitive file scan on {base_url}")

    for path in SENSITIVE_PATHS:
        # Construct the full URL
        full_url = urljoin(base_url, path)

        try:
            # Send a GET request
            response = requests.get(full_url, headers=headers, timeout=5, verify=False)

            # Check if the file is accessible
            if response.status_code == 200:
                print(f"[+] Found sensitive file: {full_url}")
                vulnerability = {
                    "type": "Sensitive Data Exposure",
                    "url": full_url,
                    "payload": "N/A",
                    "details": f"The file at {full_url} is publicly accessible (Status Code: 200)."
                }
                found_vulnerabilities.append(vulnerability)

        except requests.exceptions.RequestException as e:
            # This can happen for timeouts, connection errors, etc.
            # We can choose to log this, but for now, we'll just skip it.
            # print(f"[!] Error checking {full_url}: {e}")
            pass

    print(f"[*] Sensitive file scan finished. Found {len(found_vulnerabilities)} potential issues.")
    return found_vulnerabilities
