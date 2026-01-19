# Groundwork

> Open-source, self-hosted project management application built with Python FastAPI and PostgreSQL.

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)

## Overview

**Groundwork** is a comprehensive project management solution designed for teams who want complete control over their data. It provides issue tracking, sprint management, and team collaboration features while maintaining simplicity and extensibility.

### Key Features

- **Self-hosted**: Complete data ownership and privacy
- **Modern Stack**: FastAPI backend with HTMX + Jinja2 frontend
- **PostgreSQL Native**: Leverages PostgreSQL's advanced features
- **Role-Based Access**: Granular permissions for users and teams
- **Themeable**: Light and dark mode support

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python 3.12+, FastAPI |
| Database | PostgreSQL 15+ |
| Frontend | HTMX, Jinja2 Templates |
| Styling | Custom CSS with CSS Variables |
| Authentication | JWT with HTTP-only cookies |
| ORM | SQLAlchemy 2.0 (async) |

## Quick Start

### Prerequisites

- Python 3.12 or higher
- PostgreSQL 15 or higher
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### 1. Clone the Repository

```bash
git clone https://github.com/samanthvittal/groundwork.git
cd groundwork
```

### 2. Set Up Environment

```bash
# Create virtual environment and install dependencies
uv sync

# Or with pip
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### 3. Configure Database

Create a PostgreSQL database:

```bash
createdb groundwork
```

Copy the example environment file and configure:

```bash
cp .env.example .env
```

Edit `.env` with your database credentials:

```env
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/groundwork
SECRET_KEY=your-secret-key-here
DEBUG=true
```

### 4. Run Database Migrations

```bash
uv run alembic upgrade head
```

### 5. Start the Development Server

```bash
uv run uvicorn groundwork.main:app --reload
```

The application will be available at http://localhost:8000

### 6. Initial Setup

1. Navigate to http://localhost:8000
2. You'll be redirected to the Setup Wizard
3. Create your admin account
4. Start using Groundwork!

## Development

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src/groundwork

# Run specific test file
uv run pytest tests/auth/test_routes.py -v
```

### Code Quality

```bash
# Format code
uv run ruff format .

# Lint code
uv run ruff check .

# Type checking
uv run mypy src/
```

### Project Structure

```
groundwork/
├── src/groundwork/
│   ├── auth/           # Authentication module
│   ├── core/           # Core utilities (config, database, logging)
│   ├── health/         # Health check endpoints
│   ├── roles/          # Role management
│   ├── setup/          # Setup wizard
│   ├── users/          # User management
│   ├── views/          # HTML view routes
│   ├── static/         # CSS, JS, images
│   ├── templates/      # Jinja2 templates
│   └── main.py         # Application entry point
├── tests/              # Test suite
├── alembic/            # Database migrations
└── docs/               # Documentation
```

## Configuration

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `SECRET_KEY` | JWT signing key | Required |
| `DEBUG` | Enable debug mode | `false` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `APP_NAME` | Application name | `Groundwork` |

## Roadmap

See [overview.md](overview.md) for the full feature roadmap.

### Current Phase: P0 - Core Foundation (MVP)

- [x] P0.1 - Infrastructure & DevOps
- [x] P0.2 - Authentication & User Management
- [ ] P0.3 - Project Management Core
- [ ] P0.4 - Issue Management Foundation
- [ ] P0.5 - Issue Collaboration
- [ ] P0.6 - Views & Navigation
- [ ] P0.7 - Notifications & Email

## Contributing

Contributions are welcome! Please read our contributing guidelines before submitting a pull request.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- UI powered by [HTMX](https://htmx.org/)
- Inspired by the need for simple, self-hosted project management
