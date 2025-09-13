from flask import Flask, render_template, request, send_file
import requests
import pandas as pd
import io

app = Flask(__name__)

def make_finding(vuln_type, cwe, score, severity, tool, core, auth, exposed, desc_len, loc):
    return {
        "tool_name": tool,
        "vulnerability_type": vuln_type,
        "cwe_id": cwe,
        "cvss_score": score,
        "raw_severity": severity,
        "lines_in_function": loc,
        "cyclomatic_complexity": loc // 2 if loc else 1,
        "is_core_module": core,
        "requires_auth": auth,
        "exposed_to_internet": exposed,
        "description_length": desc_len
    }

def scan_website(url):
    findings = []
    tool_name = "Python Basic Scanner"
    exposed = True

    try:
        res = requests.get(url, timeout=10)
        html = res.text
        headers = res.headers
    except:
        return pd.DataFrame([make_finding("Unreachable Site", 0, 0.0, "Info", tool_name, 0, 0, exposed, 20, 0)])

    if not url.startswith("https://"):
        findings.append(make_finding("Missing HTTPS", 311, 6.5, "Medium", tool_name, 1, 0, exposed, 30, 10))

    try:
        test_url = url + "' OR '1'='1"
        sqli_res = requests.get(test_url, timeout=5)
        if sqli_res.status_code >= 500 or "sql" in sqli_res.text.lower():
            findings.append(make_finding("SQL Injection", 89, 8.0, "High", tool_name, 1, 0, exposed, 50, 20))
    except:
        pass

    if "<script" in html.lower():
        findings.append(make_finding("XSS", 79, 7.4, "Medium", tool_name, 1, 0, exposed, 40, 10))

    if "ping" in html.lower() or "cmd" in html.lower():
        findings.append(make_finding("Command Injection (possible)", 77, 7.8, "High", tool_name, 1, 0, exposed, 50, 15))

    if "eval" in html.lower():
        findings.append(make_finding("Remote Code Execution (eval)", 94, 9.0, "High", tool_name, 1, 0, exposed, 60, 20))

    if "error" in html.lower() or "exception" in html.lower() or "traceback" in html.lower():
        findings.append(make_finding("Information Disclosure", 200, 5.6, "Low", tool_name, 1, 0, exposed, 45, 8))

    for header in ['X-Powered-By', 'Server']:
        if header in headers:
            findings.append(make_finding(f"{header} Header Exposure", 200, 5.0, "Low", tool_name, 1, 0, exposed, len(headers[header]), 5))

    if 'Content-Security-Policy' not in headers:
        findings.append(make_finding("Missing CSP Header", 693, 6.0, "Medium", tool_name, 1, 0, exposed, 35, 5))

    cookies = res.cookies
    for c in cookies:
        if not c.secure or not c.has_nonstandard_attr("HttpOnly"):
            findings.append(make_finding("Weak Cookie Flags", 614, 5.5, "Medium", tool_name, 1, 0, exposed, 35, 4))
            break

    for path in ['/admin', '/login', '/dashboard']:
        try:
            r = requests.get(url.rstrip("/") + path, timeout=5)
            if r.status_code == 200:
                findings.append(make_finding(f"Exposed {path} Page", 285, 6.8, "Medium", tool_name, 1, 1, exposed, 40, 12))
        except:
            pass

    if not findings:
        findings.append(make_finding("No issues detected", 0, 0.0, "Info", tool_name, 1, 0, exposed, 10, 5))

    return pd.DataFrame(findings)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form['url']
        df = scan_website(url)

        # Convert booleans to 1/0 if not already ints
        bool_cols = ['is_core_module', 'requires_auth', 'exposed_to_internet']
        df[bool_cols] = df[bool_cols].astype(int)

        # Reorder columns
        ordered_cols = [
            'tool_name', 'vulnerability_type', 'cwe_id', 'cvss_score', 'raw_severity',
            'lines_in_function', 'cyclomatic_complexity', 'is_core_module',
            'requires_auth', 'exposed_to_internet', 'description_length'
        ]
        df = df[ordered_cols]

        # Generate CSV and preview
        preview_html = df.to_html(classes="table-auto border text-sm", index=False)
        buf = io.StringIO()
        df.to_csv(buf, index=False)
        buf.seek(0)
        return render_template('index.html', preview=preview_html, csv_data=buf.getvalue())

    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    csv_data = request.form['csv']
    return send_file(io.BytesIO(csv_data.encode()), mimetype='text/csv',
                     as_attachment=True, download_name='vulnerability_report.csv')

