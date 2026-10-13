# Project Guidelines

## Tech Stack
- **Python**: 3.14+
- **Django**: 6.1+
- **Package Manager**: `uv`
- **Database**: SQLite3 (development)

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

## Commands

### Running the Development Server
```bash
uv run python manage.py runserver
```

### Running Tests
```bash
uv run python manage.py test
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

### Creating a Superuser
```bash
uv run python manage.py createsuperuser
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
- Use Django's `TestCase` for database tests
- Test edge cases and error conditions
- Aim for high test coverage on critical paths

## Data Modeling
- Create a base model with common fields (created_at, updated_at) if needed
- Use custom user model if authentication is required
- Keep models normalized but denormalize for performance when needed
- Add appropriate constraints and validations

## Security
- Never commit secrets or sensitive data
- Use environment variables for configuration
- Keep `DEBUG = False` in production
- Regularly update dependencies

## Notes
- This is a new Django project, conventions can be established as development progresses
- Feel free to suggest improvements to these guidelines as the project evolves
