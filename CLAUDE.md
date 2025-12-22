# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build and Test Commands

- Run the server: `./script/server`
- Lint Python: `./script/lint` or `ruff check --fix`
- Lint TypeScript: `npm run lint`
- Format code: `./script/format`
- Run all tests: `./script/test`
- Run tests with coverage: `poetry run coverage run -m pytest -m 'not slow' && poetry run coverage report`
- Run a single test: `poetry run pytest tests/path/to/test_file.py::TestClass::test_method -v`
- Type checking: `pyright` or `npm run typecheck`
- Format single file: `ruff check --fix`

## After Creating Files

When creating new files, always run:

1. `ruff check --fix <filename>` - to apply code style and fix linting issues
2. `pyright <filename>` - to check for type errors

These should be run before committing any new files to ensure consistency and catch errors early.

## Code Style Guidelines

- Python: PEP8-based style with 120 character line limit
- Use type hints (Python type checking is in "strict" mode)
- Imports: grouped by standard library, third-party, and local imports
- Error handling: Use explicit exception types, never bare except
- Naming: snake_case for Python, camelCase for TypeScript
- Test coverage requirement: 90%
- Templates are Jinja2 (.html.j2)
- Automated formatting by ruff, prettier, and djlint
- Pre-commit hooks handle most formatting automatically
- Never add comments unless a code line is not self explanatory
- When creating a test, create it in the tests folder and keep the same folder structure
- A test file is always named as the original code, but prefixed with test\_
- Tests are written async and require the annotation @pytest.mark.asyncio
- When using mocks, we use mocker: MockerFixture to be provided in the method signature
- When writing tests, only import methods to be tested, avoid importing other objects from the main code, ask if unsure
- When writing tests, always use this flow: given, when, then, mark these blocks with a comment
- If methods are short, create one test method, if methods are long, divide tests into logic segments
