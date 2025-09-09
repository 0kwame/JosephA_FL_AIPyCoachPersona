VENV = .venv

.PHONY: venv install run test clean

# Create venv with uv
venv:
	uv venv $(VENV)

# Install dependencies
install: venv
	uv sync

# Run app
run:
	uv run python main.py

# Run tests
test:
	uv run pytest -v

# Clean up venv + cache files
clean:
	rm -rf $(VENV) __pycache__ .pytest_cache .mypy_cache .ruff_cache
