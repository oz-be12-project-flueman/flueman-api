set -eo pipefail  # 실패하면 더 진행하지 않음 -> 왜 실패했는지 조사 가능

COLOR_GREEN=`tput setaf 2;`  # 초록색 출력
COLOR_NC=`tput sgr0;`        # 색상 초기화

echo "Format (ruff-format)"
uv run ruff format .

echo "Lint (ruff check --fix)"
uv run ruff check --fix .

echo "Type check (mypy)"
uv run dmypy run -- .

# echo "Starting pytest (pytest-cov)"
# uv run pytest --cov=app --cov-report=term-missing --cov-report=html:htmlcov

echo "✅ All checks passed"
