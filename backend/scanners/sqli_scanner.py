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
PAYLOAD = "'"

def check_sqli(targets):
    """
    Checks for error-based SQL injection vulnerabilities.

    Args:
        targets (dict): A dictionary from the crawler containing 'links' and 'forms'.

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

        print(f"[*] Testing SQLi on URL: {url}")
        for param, values in query_params.items():
            original_value = values[0]
            # Create a new query string with the payload
            test_params = query_params.copy()
            test_params[param] = original_value + PAYLOAD
            test_query = urlencode(test_params, doseq=True)
            test_url = parsed_url._replace(query=test_query).geturl()

            try:
                response = requests.get(test_url, timeout=5, verify=False, headers={'User-Agent': 'WVFE-Scanner/1.0'})
                for db, errors in SQL_ERRORS.items():
                    for error in errors:
                        if re.search(error, response.text, re.IGNORECASE):
                            print(f"[+] Found potential SQLi in {test_url} (param: {param})")
                            vulnerability = {
                                "type": f"SQL Injection ({db} Error)",
                                "url": test_url,
                                "payload": PAYLOAD,
                                "details": f"The parameter '{param}' seems to be vulnerable to SQL injection. A payload caused a database error message to be displayed."
                            }
                            found_vulnerabilities.append(vulnerability)
                            break # Move to next DB type
                    else:
                        continue # Only executed if the inner loop did not break
                    break # Only executed if the inner loop did break
            except requests.RequestException:
                pass

    # --- Test HTML Forms ---
    for form in targets.get('forms', []):
        form_url = form['url']
        form_method = form['method']
        form_inputs = form['inputs']

        print(f"[*] Testing SQLi on form at: {form_url}")

        # Create a dictionary of data to submit
        data = {}
        for i in form_inputs:
            # Assign a default value, we'll inject into one at a time
            if i['type'] in ('text', 'password', 'textarea', 'search'):
                data[i['name']] = 'test'
            elif i['type'] == 'email':
                data[i['name']] = 'test@test.com'
            else:
                data[i['name']] = '1'

        for input_to_test in form_inputs:
            test_data = data.copy()
            test_data[input_to_test['name']] = data[input_to_test['name']] + PAYLOAD

            try:
                if form_method == 'post':
                    response = requests.post(form_url, data=test_data, timeout=5, verify=False, headers={'User-Agent': 'WVFE-Scanner/1.0'})
                else: # get
                    response = requests.get(form_url, params=test_data, timeout=5, verify=False, headers={'User-Agent': 'WVFE-Scanner/1.0'})

                for db, errors in SQL_ERRORS.items():
                    for error in errors:
                        if re.search(error, response.text, re.IGNORECASE):
                            print(f"[+] Found potential SQLi in form at {form_url} (input: {input_to_test['name']})")
                            vulnerability = {
                                "type": f"SQL Injection ({db} Error)",
                                "url": form_url,
                                "payload": PAYLOAD,
                                "details": f"The form input '{input_to_test['name']}' seems to be vulnerable to SQL injection. A payload caused a database error message to be displayed."
                            }
                            found_vulnerabilities.append(vulnerability)
                            break
                    else:
                        continue
                    break
            except requests.RequestException:
                pass

    return found_vulnerabilities
