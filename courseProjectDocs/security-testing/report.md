# Security Testing Report

**Testing Tool:** Bandit 1.9.2 (Python Static Application Security Testing)  
**Team Members:** Sandeep Ramavath, Nithikesh Reddy, Mallikarjuna

---

## Test Scope and Coverage

### Areas Tested

**1. Full Codebase Scan**
- Entire `pandas/` directory recursively scanned
- Total Python files scanned: 7,218
- Total lines of code analyzed: 484,492
- Execution time: ~35 seconds

**2. Targeted Vulnerability Scans**

Individual modules were analyzed to identify specific vulnerability types:

- **`pandas/io/pickle.py`** - Insecure Deserialization (CWE-502)
  - Found: 29 MEDIUM severity (B301), 13 LOW severity (B403)
  - Total: 42 pickle-related issues
  
- **`pandas/io/sql.py`** - SQL Injection (CWE-89)
  - Found: 14 MEDIUM severity SQL injection vectors (B608)
  
- **`pandas/io/formats/style.py`** - Code Injection (CWE-94)
  - Found: 3 HIGH severity Jinja2 autoescape issues (B701)
  
- **`pandas/tests/`** - Insecure Temporary Files (CWE-377)
  - Found: 1 MEDIUM severity temp file issue (B108)
  - Additional: Thousands of LOW severity assertion statements (B101)

**3. Other Vulnerability Types Scanned**
- Eval-like functions (B307) - 24 instances
- XML parsing vulnerabilities (B314, B318, etc.) - 17 instances
- Subprocess calls (B603, B607) - 33 instances

### Testing Methodology

**Tool:** Bandit 1.9.2
- **Type:** Static Application Security Testing (SAST)
- **Language:** Python
- **Method:** Abstract Syntax Tree (AST) pattern matching
- **Configuration:** Default profile with all vulnerability checks enabled

---

## Vulnerability Summary

### Total Issues Found: 17,603

| Severity | Count | Percentage |
|----------|-------|------------|
| **HIGH** | 3 | 0.02% |
| **MEDIUM** | 72 | 0.41% |
| **LOW** | 17,528 | 99.57% |

### Detailed Vulnerability List

| # | Title | Type | Severity | Location | Recommended Fix | Identified By |
|---|-------|------|----------|----------|-----------------|---------------|
| 1 | Jinja2 Autoescape Disabled | Code Injection (CWE-94) | HIGH | `pandas/io/formats/style.py:3816`<br>`pandas/io/formats/style_render.py:77`<br>`pandas/tests/io/formats/style/test_html.py:25` | Enable autoescape in Jinja2 Environment:<br>`Environment(autoescape=True)` or<br>`Environment(autoescape=select_autoescape(['html', 'xml']))` | Sandeep Ramavath |
| 2 | Pickle Deserialization (29 instances) | Insecure Deserialization (CWE-502) | MEDIUM | `pandas/io/pickle.py` and 28 other locations throughout codebase | 1. Only unpickle from trusted sources<br>2. Validate data origin before deserializing<br>3. Use safer formats (JSON, Parquet, HDF5)<br>4. Implement HMAC signing for pickle files | Nithikesh Reddy |
| 3 | SQL Injection Vectors (14 instances) | SQL Injection (CWE-89) | MEDIUM | `pandas/io/sql.py` (14 locations with string-based query construction) | 1. Use parameterized queries exclusively<br>2. Replace string formatting with query parameters<br>3. Example: `cursor.execute("SELECT * FROM ?", (table,))` | Mallikarjuna |
| 4 | Eval-like Function Usage (24 instances) | Code Execution | MEDIUM | Various pandas modules using `eval()` | 1. Use `ast.literal_eval()` for literal evaluation<br>2. Validate and sanitize all input before eval<br>3. Consider safer alternatives for expression parsing | Sandeep Ramavath |
| 5 | Insecure Temp File | Insecure Temporary File (CWE-377) | MEDIUM | `pandas/tests/io/test_http_headers.py:174` | Replace `tempfile.mktemp()` with:<br>`fd, path = tempfile.mkstemp()`<br>`os.close(fd)` | Nithikesh Reddy |
| 6 | XML Parsing Vulnerabilities (17 instances) | XML External Entity (XXE) | MEDIUM/LOW | Various modules using XML parsing | 1. Use `defusedxml` library instead<br>2. Disable external entity processing<br>3. Configure parsers securely | Mallikarjuna |
| 7 | Assert Statement Usage (17,462 instances) | Improper Exception Handling (CWE-703) | LOW | Throughout codebase (tests, core modules, I/O) | 1. Replace asserts with explicit checks in production code:<br>`if not condition: raise ValueError("msg")`<br>2. Keep asserts in test code (acceptable)<br>**Note:** Low priority - pandas not run with `-O` flag | Sandeep Ramavath |

### Vulnerability Type Summary

| Vulnerability Type | CWE | Severity | Count |
|-------------------|-----|----------|-------|
| Assert Statement Usage | CWE-703 | LOW | 17,462 |
| Pickle Deserialization | CWE-502 | MEDIUM | 29 |
| Pickle Imports | CWE-502 | LOW | 13 |
| Eval-like Functions | N/A | MEDIUM | 24 |
| Subprocess Calls | N/A | LOW | 22 |
| SQL Injection Vectors | CWE-89 | MEDIUM | 14 |
| Partial Executable Paths | N/A | LOW | 11 |
| Jinja2 Autoescape Disabled | CWE-94 | HIGH | 3 |
| XML Parsing Issues | N/A | MEDIUM/LOW | 17 |
| Try/Except/Pass | N/A | LOW | 4 |
| Insecure Temp Files | CWE-377 | MEDIUM | 1 |

---

## Execution and Results

**Scan Statistics:**
- **Tool Used:** Bandit 1.9.2 (Static Application Security Testing)
- **Total Lines of Code Scanned:** 484,492
- **Total Python Files Scanned:** 7,218
- **Total Issues Identified:** 17,603
- **Scan Duration:** ~35 seconds (full scan)

**Severity Breakdown:**
- **HIGH severity:** 3 issues (0.02%)
  - B701: Jinja2 autoescape disabled (3 locations)
  
- **MEDIUM severity:** 72 issues (0.41%)
  - B301: Pickle deserialization (29 instances)
  - B307: Eval-like functions (24 instances)
  - B608: SQL injection vectors (14 instances)
  - B314, B318: XML parsing (3 instances)
  - B310: URL open audit (1 instance)
  - B108: Insecure temp file (1 instance)
  
- **LOW severity:** 17,528 issues (99.57%)
  - B101: Assert statements (17,462 instances)
  - B603: Subprocess calls (22 instances)
  - B403: Pickle imports (13 instances)
  - B607: Partial executable paths (11 instances)
  - B404, B405, B408, B110: Other minor issues (20 instances)

**Output Files Generated:**
1. `bandit_pickle.json` - Pickle module scan results (42 issues)
2. `bandit_sql.json` - SQL module scan results (14 SQL injection + assertions)
3. `bandit_style.json` - Style module scan results (3 HIGH severity)
4. `bandit_tests.json` - Test suite scan results (1 MEDIUM + thousands LOW)
5. `bandit_full_complete.json` - Complete codebase scan (17,603 issues total)


---

## Group Contributions

**Sandeep Ramavath**
- Researched and selected Bandit as the security testing tool for Python codebase analysis
- Set up the testing environment and installed Bandit 1.9.2 in the virtual environment
- Executed targeted security scans on critical modules (pickle, SQL, style, tests)
- Performed comprehensive full codebase scan analyzing 484,492 lines of code
- Identified and documented HIGH severity vulnerability: Jinja2 Autoescape Disabled (CWE-94)
- Identified and documented MEDIUM severity vulnerability: Eval-like Function Usage (24 instances)
- Identified and documented LOW severity vulnerability: Assert Statement Usage (CWE-703, 17,462 instances)
- Authored the complete security testing report with detailed vulnerability analysis
- Created README.md documentation with step-by-step execution instructions

**Nithikesh Reddy**
- Analyzed pickle deserialization vulnerabilities throughout the pandas codebase
- Identified and documented MEDIUM severity vulnerability: Pickle Deserialization (CWE-502, 29 instances)
- Researched security implications and remediation strategies for insecure deserialization
- Identified and documented MEDIUM severity vulnerability: Insecure Temp File (CWE-377)
- Contributed to vulnerability risk assessment and severity classification
- Verified scan results and validated JSON output files
- Participated in security analysis discussions and vulnerability prioritization

**Mallikarjuna**
- Analyzed SQL injection vulnerabilities in the pandas I/O module
- Identified and documented MEDIUM severity vulnerability: SQL Injection Vectors (CWE-89, 14 instances)
- Researched SQL injection prevention techniques and parameterized query best practices
- Identified and documented XML parsing vulnerabilities (17 instances across MEDIUM/LOW severity)
- Contributed to vulnerability type categorization and CWE mapping
- Assisted with interpretation of Bandit scan results and issue classification
- Participated in group strategy sessions for security testing approach


