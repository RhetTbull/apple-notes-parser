# Package description

Read the file README.md to understand the package's purpose and usage.

# Python Usage

ALWAYS use uv to run python and install dependencies. Use uv to manage virtual environments. NEVER run pip directly.

# Coding Style

Use meaningful variable and function names.

Do not document obvious things. Use docstrings to explain the purpose and behavior of functions and classes. ALWAYS use Google style docstrings.

Use ruff to lint your code. Use ruff import sorting to sort imports. Use mypy to type check your code.

Use the ./check script to run all linting checks using ruff. This script will also fix linting errors that can be automatically fixed.

Write the code for python 3.11 compatibility and later. Use type hints and annotations to improve code readability and maintainability. Use type hints and annotations compatible with python 3.11 and later. For example, use `list[int]` for a list of integers instead of `List[int]`. Use the union operator `|` to define a union type and for optional values, for example, use `int | None` instead of `Optional[int]`.

# Testing

IMPORTANT: ALWAYS write tests using pytest style test functions. NEVER write tests using unittest style test classes. Use pytest fixtures for setup and teardown when appropriate. DO NOT CREATE TEST CLASSES. ALWAYS USE TEST FUNCTIONS WRITTEN IN PYTEST STYLE.

All tests should be written in a way that they can be run independently and in parallel. This means that each test should be self-contained and not rely on any external state or resources.

All tests should be in the tests/ directory.
