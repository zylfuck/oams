.PHONY: help install test lint format clean build upload

help:
	@echo "Available commands:"
	@echo "  install    Install package in development mode"
	@echo "  test       Run test suite"
	@echo "  lint       Run linting checks"
	@echo "  format     Format code with black"
	@echo "  clean      Clean build artifacts"
	@echo "  build      Build distribution packages"
	@echo "  upload     Upload to PyPI"

install:
	pip install -e .
	pip install pytest pytest-cov black mypy

test:
	pytest tests/ -v --cov=oams --cov-report=term-missing

lint:
	black --check src/ tests/
	mypy src/oams --ignore-missing-imports

format:
	black src/ tests/

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache .mypy_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: clean
	python setup.py sdist bdist_wheel

upload: build
	twine upload dist/*
