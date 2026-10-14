# AI Agent Guidelines

This project is a Django 6.1 application using Python 3.14+ and `uv` as the package manager.

## Tech Stack
- **Python**: 3.14+
- **Django**: 6.1+
- **Package Manager**: `uv`
- **Testing**: pytest with pytest-django
- **Database**: SQLite3 (development)

## Commands

### Running the Development Server
```bash
uv run python manage.py runserver
```

### Running Tests
```bash
uv run pytest
```

For verbose output:
```bash
uv run pytest -v
```

To run specific tests:
```bash
uv run pytest tests/test_login.py -v
uv run pytest tests/test_login.py::LoginPageGetTests -v
```

### Adding Dependencies
```bash
uv add <package>
```

### Database Operations
```bash
uv run python manage.py makemigrations
uv run python manage.py migrate
```

## Project Structure
```
dj_ai_employees/
├── core/                 # Django project package
│   ├── settings.py       # Main settings
│   ├── urls.py           # Root URL configuration
│   ├── wsgi.py           # WSGI config
│   └── asgi.py           # ASGI config
├── templates/            # Global templates
├── manage.py             # Django management script
├── pyproject.toml        # Project dependencies
└── db.sqlite3            # SQLite database (gitignored)
```

## Coding Conventions

### Code Style
- Follow PEP 8 for Python code
- Use type hints where applicable
- Write docstrings for models, views, and complex functions
- Keep functions and methods focused and single-purpose

### Django Patterns
- Use Class-Based Views (CBVs) for complex views; Function-Based Views (FBVs) for simple ones
- Prefer async views where appropriate (Django 6.1 supports async throughout)
- Use Django's built-in authentication system
- Organize models by domain in separate apps
- Keep settings organized and use environment variables for sensitive data

### Database
- Use SQLite for development
- Migrations should be atomic and well-tested
- Add indexes on frequently queried fields
- Use `select_related` and `prefetch_related` to optimize queries

### Testing
- Write tests for models, views, and business logic
- Use pytest with pytest-django for testing
- Use Django's `TestCase` for database tests
- Test edge cases and error conditions
- Aim for high test coverage on critical paths
- Pytest configuration is in `pyproject.toml` under `[tool.pytest.ini_options]`

## Security
- Never commit secrets or sensitive data
- Use environment variables for configuration
- Keep `DEBUG = False` in production
- Regularly update dependencies
