# Project general coding standards

## General Guidelines
- Write clear and concise documentation
- Use the NumPy docstring format for all functions and classes
- Use Dutch in all coding and documentation where possible

## Naming Conventions
- Use `kebab-case` for branch names (e.g., `nieuwe-parser`)
- Use descriptive names for variables and functions in Dutch

## Testing conventions
- Write unit tests for all new features and bug fixes
- Use descriptive names for test cases in Dutch
- Keep the tests simple and focused on a single aspect of the code

## Repo-specifieke afspraken
- Houd code compatibel met Python 3.13
- Gebuik ALTIJD uv wanneer je code draait zoals pytests, debug scripts, et cetera.
- Gebruik black en isort met een maximale regellengte van 119
- Draai bij wijzigingen minimaal gerichte pytest-tests voor de aangepaste onderdelen
- Vermijd echte Azure/OpenAI-calls in tests; gebruik mocks, fixtures of gecachte testdata
- Houd wijzigingen klein en binnen de scope van de vraag (geen brede refactors)