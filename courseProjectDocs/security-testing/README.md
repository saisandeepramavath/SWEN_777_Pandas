# Security Testing - Execution Guide

This guide provides instructions to execute security tests and reproduce the results documented in `report.md`.

## Prerequisites

- Python 3.11+
- Virtual environment at `/Volumes/T7Shield/SWEN777/SWEN_777_Pandas/venv`
- Access to pandas source code repository

## Setup

### 1. Activate Virtual Environment
```bash
cd /Volumes/T7Shield/SWEN777/SWEN_777_Pandas
source venv/bin/activate
```

### 2. Install Bandit
```bash
pip install bandit
```

Verify installation:
```bash
bandit --version
# Expected: bandit 1.9.2
```

## Running Security Scans

### Targeted Module Scans

```bash
# Scan pickle module for deserialization vulnerabilities
bandit -r pandas/io/pickle.py -f json -o courseProjectDocs/security-testing/results/bandit_pickle.json

# Scan SQL module for SQL injection vulnerabilities
bandit -r pandas/io/sql.py -f json -o courseProjectDocs/security-testing/results/bandit_sql.json

# Scan style module for template injection vulnerabilities
bandit -r pandas/io/formats/style.py -f json -o courseProjectDocs/security-testing/results/bandit_style.json

# Scan test suite for insecure temp file usage
bandit -r pandas/tests/ -f json -o courseProjectDocs/security-testing/results/bandit_tests.json
```

### Full Codebase Scan

```bash
# Complete scan (all severity levels)
bandit -r pandas/ -f json -o courseProjectDocs/security-testing/results/bandit_full_complete.json
```

**Note:** Full scan analyzes 484,492 lines of code across 7,218 files and takes approximately 35 seconds.

## Viewing Results

### View HIGH Severity Issues Only
```bash
bandit -r pandas/ -lll
```

### View MEDIUM and HIGH Severity Issues
```bash
bandit -r pandas/ -ll
```

### View All Issues (Terminal Output)
```bash
bandit -r pandas/
```

## Expected Results

- **Total Issues:** 17,603
- **HIGH Severity:** 3 (Jinja2 autoescape disabled)
- **MEDIUM Severity:** 72 (pickle deserialization, SQL injection, eval usage, etc.)
- **LOW Severity:** 17,528 (primarily assert statements)

## Output Files

All scan results are stored in `courseProjectDocs/security-testing/results/`:
- `bandit_pickle.json` - 42 issues
- `bandit_sql.json` - 14 SQL injection issues + assertions
- `bandit_style.json` - 3 HIGH severity issues
- `bandit_tests.json` - 1 MEDIUM + thousands LOW severity
- `bandit_full_complete.json` - Complete scan (17,603 issues)


