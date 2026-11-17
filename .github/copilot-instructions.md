# Project general coding standards

## General Guidelines
- Write clear and concise documentation, using comments and docstrings where appropriate
- Use the NumPy docstring format for all functions and classes
- Use type hints for all function parameters and return types
- Use f-strings for string formatting instead of concatenation or the `format()` method
- Use pydantic datamodels, try to refrain from using plain dictionaries for structured data
- Keep functions and methods short and focused on a single responsibility
- Keep code readable and maintainable
- Follow the DRY (Don't Repeat Yourself) principle to avoid code duplication
- Look into using existing utilities and code in the repo before writing new ones
- When using external libraries, look up documentation and usage examples first

## Naming Conventions
- Use `kebab-case` for branch names (e.g., `nieuwe-parser`)
- Keep Dutch terminology in Dutch, use english otherwise

## Testing conventions
- Write unit tests for all new features and bug fixes
- Use descriptive names for test cases
- Keep the tests simple and focused on a single aspect of the code
- Be critical of your own tests; Code is not always correct, reason whether the test actually captures the desired functionality, or if it conforms to buggy code.

## Repo-specific
- Keep code compatible with Python 3.13
- Always use `uv` when running code such as pytests, debug scripts, etc.
- Use black and isort with a maximum line length of 119
- Run minimally targeted pytest tests for the modified parts when making changes
- Avoid real API calls (e.g. Azure Doc AI, OpenAI) in tests; use mocks, fixtures or cached data

## Assumptions and missing info
- When instructed, if you are making any assumptions, ask for clarification first before implementing a solution
- Document any assumptions you make clearly in the code or comments
- If you have missing information, ask for clarification before proceeding
- When you have multiple tasks, work with a to-do list to stay organized and keep the user informed of progress