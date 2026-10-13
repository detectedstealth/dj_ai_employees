# DJ AI Employees

A Django 6.1 application with Docker support and full OpenTelemetry observability.

## Tech Stack

- **Python**: 3.14+
- **Django**: 6.1+
- **Package Manager**: `uv`
- **Database**: PostgreSQL 17 (Docker) / SQLite3 (local development)
- **WSGI Server**: Gunicorn
- **Observability**: OpenTelemetry, Grafana, Loki, Tempo, Prometheus

## Prerequisites

- **Docker** and **Docker Compose** installed on your system
- Python 3.14+ and `uv` (for local development without Docker)

## Quick Start

### 1. Configure Environment Variables

Copy the example environment file and adjust the values:

```bash
cp .env.example .env
```

Edit `.env` and update at minimum:

- `SECRET_KEY` — generate a secure key for production
- `DB_PASSWORD` — set a strong database password
- `GRAFANA_ADMIN_PASSWORD` — set a secure Grafana admin password

### 2. Build and Start All Services

```bash
docker compose up --build
```

This starts all services:

| Service | URL | Default Credentials |
|---------|-----|---------------------|
| Django App | http://localhost:8000 | — |
| Grafana | http://localhost:3000 | admin / admin |
| Prometheus | http://localhost:9090 | — |
| Tempo | http://localhost:3200 | — |
| Loki | http://localhost:3100 | — |
| PostgreSQL | localhost:5432 | see `.env` |

### 3. Run Database Migrations

```bash
docker compose exec web python manage.py migrate
```

### 4. Create a Superuser (Optional)

```bash
docker compose exec web python manage.py createsuperuser
```

## Service Architecture

The project uses two Docker networks:

- **`app`** — Django web server and PostgreSQL database
- **`observability`** — Grafana, Prometheus, Tempo, and Loki

The OpenTelemetry Collector bridges both networks, receiving traces and logs from Django and forwarding them to the appropriate backends.

```
┌─────────────────────────────────────────────────────┐
│                   app network                       │
│                                                     │
│  ┌─────────┐     ┌──────────┐                      │
│  │  Django  │────▶│ PostgreSQL│                      │
│  │  :8000   │     │  :5432   │                      │
│  └────┬─────┘     └──────────┘                      │
│       │                                              │
└───────┼──────────────────────────────────────────────┘
        │ OTLP (traces & logs)
        ▼
┌─────────────────────────────────────────────────────┐
│              OTel Collector (bridge)                 │
│              :4317 (gRPC) / :4318 (HTTP)             │
└───────┬──────────────────────────────────────────────┘
        │
        ├──────────────────┐
        ▼                  ▼
┌─────────────────────────────────────────────────────┐
│              observability network                   │
│                                                     │
│  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐   │
│  │Tempo   │  │ Loki   │  │Prometh. │  │Grafana │   │
│  │:3200   │  │:3100   │  │:9090    │  │:3000   │   │
│  └────────┘  └────────┘  └────────┘  └────────┘   │
└─────────────────────────────────────────────────────┘
```

## Data Persistence

All data persists across runs using Docker named volumes:

| Volume | Service | Purpose |
|--------|---------|---------|
| `postgres_data` | PostgreSQL | Database files |
| `tempo_data` | Tempo | Trace data |
| `loki_data` | Loki | Log data |
| `prometheus_data` | Prometheus | Metrics data |
| `grafana_data` | Grafana | Dashboards and settings |

To reset all data:

```bash
docker compose down -v
```

## Observability

### Grafana Dashboards

Grafana is pre-configured with three data sources:

- **Prometheus** (default) — metrics and dashboards
- **Tempo** — distributed traces
- **Loki** — log aggregation

Cross-referencing is enabled: you can navigate from traces to logs and from traces to metrics directly within Grafana.

### OpenTelemetry Instrumentation

Django is automatically instrumented via `opentelemetry-instrumentation-django`. All HTTP requests generate traces that flow through the OTel Collector to Tempo. Application logs are routed to Loki.

To disable OpenTelemetry instrumentation, set in `.env`:

```
OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED=false
```

## Local Development (Without Docker)

### 1. Install Dependencies

```bash
uv sync
```

### 2. Run Migrations

```bash
uv run python manage.py migrate
```

### 3. Start the Development Server

```bash
uv run python manage.py runserver
```

### 4. Run Tests

```bash
uv run python manage.py test
```

## Docker Commands

| Command | Description |
|---------|-------------|
| `docker compose up --build` | Build and start all services in the foreground |
| `docker compose up --build -d` | Build and start all services in detached mode |
| `docker compose down` | Stop and remove containers, preserve volumes |
| `docker compose down -v` | Stop and remove containers and all volumes |
| `docker compose logs -f web` | Follow Django app logs |
| `docker compose exec web <cmd>` | Run a command inside the Django container |
| `docker compose exec db psql -U dj_ai_employees -d dj_ai_employees` | Connect to PostgreSQL |

## Project Structure

```
dj_ai_employees/
├── core/                         # Django project package
│   ├── settings.py               # Settings with env var support & OTEL
│   ├── urls.py                   # Root URL configuration
│   ├── wsgi.py                   # WSGI application
│   └── asgi.py                   # ASGI application
├── templates/                    # Global templates
├── otel/                         # Observability configuration
│   ├── config.yaml               # OTel Collector pipeline config
│   ├── tempo.yaml                # Tempo trace backend config
│   ├── loki.yaml                 # Loki log backend config
│   ├── prometheus.yaml           # Prometheus scrape config
│   └── grafana/
│       └── provisioning/         # Grafana auto-provisioning
│           ├── datasources/      # Prometheus, Tempo, Loki
│           └── dashboards/       # Dashboard providers
├── manage.py                     # Django management script
├── pyproject.toml                # Project dependencies
├── Dockerfile                    # Multi-stage Docker build
├── docker-compose.yml            # Service orchestration
├── .env.example                  # Environment variable template
├── .env                          # Local environment (gitignored)
└── .dockerignore                 # Docker build exclusions
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | *(insecure default)* | Django secret key |
| `DEBUG` | `True` | Django debug mode |
| `ALLOWED_HOSTS` | `*` | Comma-separated allowed hosts |
| `DB_ENGINE` | `django.db.backends.postgresql` | Database backend |
| `DB_NAME` | `dj_ai_employees` | Database name |
| `DB_USER` | `dj_ai_employees` | Database user |
| `DB_PASSWORD` | `changeme` | Database password |
| `DB_HOST` | `db` | Database host |
| `DB_PORT` | `5432` | Database port |
| `OTEL_SERVICE_NAME` | `dj_ai_employees` | OpenTelemetry service name |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://otel-collector:4317` | OTLP exporter endpoint |
| `OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED` | `true` | Enable OTEL logging |
| `GRAFANA_ADMIN_USER` | `admin` | Grafana admin username |
| `GRAFANA_ADMIN_PASSWORD` | `admin` | Grafana admin password |

## Security Notes

- Always generate a unique `SECRET_KEY` for production
- Set `DEBUG=False` in production
- Use strong passwords for the database and Grafana
- Restrict `ALLOWED_HOSTS` to your domain in production
- Never commit `.env` files containing secrets
