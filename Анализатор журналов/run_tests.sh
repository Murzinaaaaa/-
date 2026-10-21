#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
python -m pytest test_app.py --cov=app --cov-report=term-missing --cov-report=html:htmlcov -v
echo "HTML report: $(pwd)/htmlcov/index.html"