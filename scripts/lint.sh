#!/bin/bash
# Code quality checks (linting and formatting)

set -e

INSTALL_DIR="/srv/Snapshotter"

if [ ! -d "${INSTALL_DIR}" ]; then
    echo "Error: Snapshotter not found at ${INSTALL_DIR}"
    exit 1
fi

source "${INSTALL_DIR}/venv/bin/activate"

echo "Running code quality checks..."
echo ""

echo "Running black (code formatting)..."
black --check "${INSTALL_DIR}/snapshotter" "${INSTALL_DIR}/tests" || {
    echo "Code formatting issues found. Run: black ${INSTALL_DIR}/snapshotter ${INSTALL_DIR}/tests"
    exit 1
}

echo "✓ Black check passed"
echo ""

echo "Running ruff (linting)..."
ruff check "${INSTALL_DIR}/snapshotter" "${INSTALL_DIR}/tests" || {
    echo "Linting issues found. Run: ruff check --fix ${INSTALL_DIR}/snapshotter ${INSTALL_DIR}/tests"
    exit 1
}

echo "✓ Ruff check passed"
echo ""

echo "Running pytest..."
pytest "${INSTALL_DIR}/tests" -v --cov=snapshotter --cov-report=term-missing

echo ""
echo "All checks passed!"
