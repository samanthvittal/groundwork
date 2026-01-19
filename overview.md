# Groundwork - Open Source Self-Hosted Project Management

> A comprehensive, self-hosted project management application built with Python FastAPI and PostgreSQL.
> Licensed under GPL 3.0

---

## Table of Contents

1. [Overview](#overview)
2. [Technology Stack](#technology-stack)
3. [Development Philosophy](#development-philosophy)
4. [Design Patterns](#design-patterns)
5. [Phase Structure](#phase-structure)
6. [Feature Roadmap](#feature-roadmap)
   - [P0 - Core Foundation (MVP)](#p0---core-foundation-mvp)
   - [P1 - Essential Features](#p1---essential-features)
   - [P2 - Enhanced Functionality](#p2---enhanced-functionality)
   - [P3 - Advanced Features](#p3---advanced-features)
   - [P4 - Enterprise Features](#p4---enterprise-features)
7. [Appendix: Design Pattern Reference](#appendix-design-pattern-reference)

---

## Overview

**Groundwork** is an open-source, self-hosted project management application licensed under GPL 3.0. It provides comprehensive issue tracking, sprint management, and team collaboration features while maintaining simplicity, extensibility, and Python-first development principles.

### Key Principles

- **Self-hosted first**: Complete data ownership and privacy
- **Python ecosystem**: FastAPI backend, no bloated JavaScript frameworks
- **Lightweight frontend**: HTMX + Jinja2 templates with modern CSS
- **PostgreSQL native**: Leveraging PostgreSQL's advanced features
- **Modular design**: Enable/disable features per project
- **Flexible authentication**: Local auth or external IAM (Keycloak) — chosen at setup
- **Open source**: GPL 3.0 licensed, community-driven
- **Pattern-driven architecture**: Gang of Four design patterns for maintainability

---

## Technology Stack

| Layer | Technology |
|-------|------------|
| **Framework** | FastAPI |
| **ORM** | SQLAlchemy 2.0 + Alembic |
| **Validation** | Pydantic v2 |
| **Database** | PostgreSQL |
| **Templates** | Jinja2 |
| **Interactivity** | HTMX |
| **Styling** | Tailwind CSS |
| **Color Palette** | Catppuccin (Frappé default) |
| **Testing** | pytest, pytest-asyncio, httpx |
| **CI/CD** | GitHub Actions |
| **Containers** | Docker, Docker Compose |
| **Caching** (P1+) | Redis |
| **Task Queue** (P2+) | Celery |
| **IAM** (P4) | Keycloak (optional) |

---

## Development Philosophy

### Vertical Slice Architecture

Each phase delivers **complete, deployable, testable functionality**. No phase is complete without:

1. **Feature Implementation** — The actual functionality
2. **Database Migrations** — Schema changes via Alembic
3. **API Endpoints** — REST API with OpenAPI documentation
4. **UI Components** — HTMX + Jinja2 templates
5. **Unit Tests** — Minimum 80% coverage for new code
6. **Integration Tests** — API endpoint testing
7. **Documentation** — User docs, API docs, changelog
8. **Deployment Update** — Docker/Compose changes if needed

### Dependency Rules

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         DEPENDENCY FLOW                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   P0.1 Infrastructure ──► ALL OTHER FEATURES                            │
│         │                                                               │
│         ▼                                                               │
│   P0.2 Auth ──► P0.3 Projects ──► P0.4 Issues ──► P0.5 Collaboration   │
│         │              │                │                               │
│         │              ▼                ▼                               │
│         │        P0.6 Views ◄──────────┘                               │
│         │              │                                                │
│         ▼              ▼                                                │
│   P0.7 API ◄───────────┴──► P0.8 Notifications                         │
│                                                                         │
│   ════════════════════════════════════════════════════════════════     │
│                         P0 COMPLETE = MVP RELEASE                       │
│   ════════════════════════════════════════════════════════════════     │
│                                                                         │
│   P1.1 Sprints ◄── P0.4 Issues                                         │
│   P1.2 Backlog ◄── P1.1 Sprints                                        │
│   P1.3 Time Tracking ◄── P0.4 Issues                                   │
│   P1.4 Custom Fields ◄── P0.4 Issues                                   │
│   P1.5 Workflows ◄── P0.4 Issues                                       │
│   P1.6 Permissions ◄── P0.2 Auth, P0.3 Projects                        │
│                                                                         │
│   (Features within same phase CAN be developed in parallel)            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Milestone Definitions

| Milestone | Phase | Deliverable | Deployment |
|-----------|-------|-------------|------------|
| **M0** | P0.1-P0.2 | Bootable app with auth | Docker dev environment |
| **M1** | P0.3-P0.4 | Project & issue CRUD | Docker dev + staging |
| **M2** | P0.5-P0.8 | Full MVP | Production-ready Docker Compose |
| **MVP Release** | P0 Complete | Usable product | v0.1.0 release |
| **M3** | P1 Complete | Sprint management | v0.2.0 release |
| **M4** | P2 Complete | Reports & integrations | v0.3.0 release |
| **M5** | P3 Complete | Automation & advanced | v0.4.0 release |
| **M6** | P4 Complete | Enterprise-ready | v1.0.0 release |

---

## Phase Structure

Each phase follows this structure:

```
Phase X.Y - Feature Name
├── X.Y.0 - Infrastructure & Setup (if needed)
│   ├── Dependencies
│   ├── New packages/services required
│   └── Database schema additions
├── X.Y.1 - Core Implementation
│   ├── Models
│   ├── Repositories
│   ├── Services
│   └── Design Patterns
├── X.Y.2 - API Layer
│   ├── Endpoints
│   ├── Schemas (Pydantic)
│   └── Authentication/Authorization
├── X.Y.3 - UI Layer
│   ├── Templates
│   ├── HTMX interactions
│   └── Forms
├── X.Y.4 - Testing
│   ├── Unit tests
│   ├── Integration tests
│   └── E2E tests (if applicable)
├── X.Y.5 - Documentation
│   ├── API docs
│   ├── User guide
│   └── Changelog entry
└── X.Y.6 - Deployment
    ├── Migration scripts
    ├── Docker updates
    └── Configuration changes
```

---

## Design Patterns

### Pattern-to-Feature Mapping

| Feature Area | Primary Patterns | Secondary Patterns |
|--------------|------------------|-------------------|
| **Authentication** | Strategy, Abstract Factory | Adapter, Proxy |
| **Issue Management** | Factory Method, State, Memento | Observer, Composite |
| **Workflow Engine** | State, Template Method | Strategy, Chain of Responsibility |
| **Notifications** | Observer, Strategy, Factory | Decorator, Adapter |
| **Time Tracking** | Command, Strategy | Observer, Visitor |
| **Reports & Analytics** | Builder, Template Method, Visitor | Strategy, Iterator |
| **Integrations** | Adapter, Facade | Observer, Proxy |
| **Query Language (LQL)** | Interpreter, Builder | Iterator, Visitor |
| **Automation Rules** | Chain of Responsibility, Command | Strategy, Observer |
| **File Storage** | Abstract Factory, Strategy | Adapter, Proxy |
| **Caching** | Proxy, Decorator, Flyweight | Singleton |
| **Permissions** | Decorator, Chain of Responsibility | Strategy, Proxy |
| **Templates** | Prototype, Builder | Factory Method |
| **Multi-tenancy** | Strategy, Abstract Factory | Proxy, Decorator |

*See [Appendix: Design Pattern Reference](#appendix-design-pattern-reference) for detailed pattern descriptions.*

---

## Feature Roadmap

---

# P0 - Core Foundation (MVP)

> **Goal**: Minimum viable product — deployable, testable, usable for basic issue tracking.
>
> **Timeline**: 8-12 weeks
>
> **Milestone**: MVP Release (v0.1.0)

---

## P0.1 - Infrastructure & DevOps Foundation

> **Priority**: CRITICAL — All other features depend on this
>
> **Estimated Effort**: 2 weeks
>
> **Parallelization**: None — must complete first

### P0.1.0 - Project Bootstrap

| Task | Description | Patterns |
|------|-------------|----------|
| Repository setup | Git repo, branch protection, PR templates | — |
| Project scaffolding | FastAPI project with src layout, pyproject.toml | — |
| Dependency management | uv/pip-tools, dependency pinning | — |
| Pre-commit hooks | Ruff, mypy, formatting checks | — |
| Editor configs | .editorconfig, VS Code settings | — |

### P0.1.1 - Configuration Management

| Task | Description | Patterns |
|------|-------------|----------|
| Settings module | Pydantic Settings with env support | **Singleton** |
| Environment handling | Dev, staging, production configs | **Strategy** |
| Secrets management | Secure handling of secrets | — |
| Feature flags | Simple feature toggle system | **Strategy** |

### P0.1.2 - Database Foundation

| Task | Description | Patterns |
|------|-------------|----------|
| PostgreSQL setup | Docker Compose service | — |
| SQLAlchemy setup | Async engine, session factory | **Singleton** |
| Alembic setup | Migration infrastructure | — |
| Base model | Timestamped base class | — |
| Connection pooling | Async pool configuration | **Singleton** |

### P0.1.3 - Application Framework

| Task | Description | Patterns |
|------|-------------|----------|
| FastAPI app factory | Application initialization | **Factory Method** |
| Middleware stack | CORS, request ID, timing | **Chain of Responsibility** |
| Exception handlers | Global error handling | **Chain of Responsibility** |
| Logging setup | Structured JSON logging | **Decorator** |
| Health endpoints | /health/live, /health/ready | — |

### P0.1.4 - Testing Infrastructure

| Task | Description | Patterns |
|------|-------------|----------|
| pytest setup | conftest.py, fixtures | — |
| Test database | Isolated test DB, transactions | — |
| Factory Boy | Model factories for tests | **Factory Method** |
| Coverage config | pytest-cov, minimum 80% | — |
| Async test support | pytest-asyncio configuration | — |

### P0.1.5 - CI/CD Pipeline

| Task | Description | Patterns |
|------|-------------|----------|
| GitHub Actions | Workflow for tests, lint, type check | — |
| Docker build | Multi-stage Dockerfile | — |
| Docker Compose (dev) | Development environment | — |
| Automated versioning | Semantic versioning setup | — |
| Artifact publishing | Docker image to registry | — |

### P0.1.6 - Theming Infrastructure (Catppuccin)

| Task | Description | Patterns |
|------|-------------|----------|
| CSS custom properties | Define all colors as variables | **Strategy** |
| Catppuccin palettes | Latte, Frappé, Macchiato, Mocha CSS files | **Strategy** |
| Semantic color mapping | Map palette to semantic names (primary, error, etc.) | **Strategy** |
| Tailwind integration | Extend Tailwind with theme tokens | — |
| Theme configuration | Python config for theme settings | **Singleton** |
| Theme detection | System preference detection | **Strategy** |
| Theme persistence | LocalStorage + user preference sync | **Memento** |
| Theme switcher component | UI component for theme selection | **Command** |

#### Catppuccin Color System

| Role | Frappé (Default) | Usage |
|------|------------------|-------|
| **Primary** | `mauve` (#ca9ee6) | Primary actions, links |
| **Success** | `green` (#a6d189) | Success states, positive |
| **Warning** | `peach` (#ef9f76) | Warnings, caution |
| **Error** | `red` (#e78284) | Errors, destructive |
| **Info** | `blue` (#8caaee) | Information, interactive |
| **Background** | `base` (#303446) | Main background |
| **Surface** | `surface0` (#414559) | Cards, inputs |
| **Text** | `text` (#c6d0f5) | Primary text |
| **Text Muted** | `subtext0` (#a5adce) | Secondary text |
| **Border** | `overlay0` (#737994) | Borders, dividers |

#### Theme Configuration

```yaml
# config/Groundwork.yaml
theme:
  default: frappe          # Default theme
  allow_user_override: true
  respect_system_preference: true
  system_light_theme: latte
  system_dark_theme: frappe
  available_themes: []     # Empty = all available
```

#### Critical Rules

1. **NO hardcoded colors** — All colors must use CSS variables or Tailwind theme tokens
2. **Semantic naming** — Use `--color-primary`, not `--color-purple`
3. **WCAG compliance** — All text must meet 4.5:1 contrast ratio
4. **Test all themes** — Visual regression tests for all 4 palettes

### P0.1.7 - Documentation Foundation

| Task | Description | Patterns |
|------|-------------|----------|
| README.md | Project overview, quick start | — |
| CONTRIBUTING.md | Contribution guidelines | — |
| THEMING.md | Catppuccin theming guide | — |
| docs/ structure | MkDocs or Sphinx setup | — |
| ADR template | Architecture Decision Records | — |

**Deliverables for P0.1:**
- [ ] `docker-compose up` starts PostgreSQL and app
- [ ] `/health/live` returns 200
- [ ] `pytest` runs with 0 tests (infrastructure ready)
- [ ] CI pipeline passes on PR
- [ ] Alembic can create/rollback migrations
- [ ] All 4 Catppuccin themes render correctly
- [ ] Theme switcher works (persists to localStorage)
- [ ] No hardcoded colors in any CSS/templates

---

## P0.2 - Authentication & User Management

> **Priority**: CRITICAL — Required for all protected features
>
> **Depends On**: P0.1
>
> **Estimated Effort**: 2 weeks
>
> **Parallelization**: Can split Local Auth vs User Management

### P0.2.0 - Auth Infrastructure

| Task | Description | Patterns |
|------|-------------|----------|
| User model | SQLAlchemy User model | — |
| Password hashing | Argon2 implementation | **Strategy** |
| JWT utilities | Token creation/validation | **Factory Method** |
| Auth dependencies | FastAPI Depends for auth | **Decorator** |

### P0.2.1 - Setup Wizard

| Task | Description | Patterns |
|------|-------------|----------|
| First-run detection | Check for initial setup | **State** |
| Setup wizard UI | Multi-step setup flow | **Template Method** |
| Auth mode selection | Local vs Keycloak choice | **Strategy** |
| Admin account creation | Initial admin user | **Factory Method** |
| Database configuration | Connection validation | **Builder** |
| SMTP configuration | Email settings wizard | **Builder** |
| Setup completion | Mark instance configured | **State** |

### P0.2.2 - Local Authentication

| Task | Description | Patterns |
|------|-------------|----------|
| Registration endpoint | POST /api/v1/auth/register | **Factory Method** |
| Email verification | Token generation, verification | **Template Method** |
| Login endpoint | POST /api/v1/auth/login | **Strategy** |
| Token refresh | POST /api/v1/auth/refresh | **State** |
| Logout | POST /api/v1/auth/logout | **Command** |
| Password reset request | POST /api/v1/auth/password-reset | **Template Method** |
| Password reset confirm | PUT /api/v1/auth/password-reset | **Command** |

### P0.2.3 - User Profile Management

| Task | Description | Patterns |
|------|-------------|----------|
| Profile model | Extended user profile | — |
| Get profile | GET /api/v1/users/me | — |
| Update profile | PATCH /api/v1/users/me | **Command**, **Memento** |
| Change password | PUT /api/v1/users/me/password | **Command** |
| Upload avatar | PUT /api/v1/users/me/avatar | **Strategy** |
| Account settings | Timezone, language, theme preferences | **Memento** |
| Theme preference | Store user's preferred theme | **Strategy** |
| Theme sync | Sync localStorage with server preference | **Observer** |
| Account deactivation | DELETE /api/v1/users/me | **State** |

### P0.2.4 - Auth UI

| Task | Description | Patterns |
|------|-------------|----------|
| Login page | Template + HTMX form | — |
| Registration page | Template + validation | — |
| Password reset pages | Request + confirm forms | — |
| Profile page | View/edit profile | — |
| Settings page | User preferences | — |

### P0.2.5 - Testing (Auth)

| Task | Description | Patterns |
|------|-------------|----------|
| User factory | Factory Boy user factory | **Factory Method** |
| Auth unit tests | Password hashing, JWT tests | — |
| Auth integration tests | Full auth flow tests | — |
| Auth fixtures | Authenticated client fixture | — |

**Deliverables for P0.2:**
- [ ] User can register, verify email, login
- [ ] JWT authentication works on protected endpoints
- [ ] User can update profile and change password
- [ ] Setup wizard completes initial configuration
- [ ] 80%+ test coverage on auth module

---

## P0.3 - Project Management Core

> **Priority**: HIGH — Foundation for issue tracking
>
> **Depends On**: P0.2
>
> **Estimated Effort**: 1.5 weeks
>
> **Parallelization**: Can develop alongside P0.4 once models exist

### P0.3.1 - Project Data Layer

| Task | Description | Patterns |
|------|-------------|----------|
| Project model | Name, key, description, visibility | — |
| ProjectMember model | User-project association with role | — |
| Project repository | CRUD operations | **Repository** |
| Project key validation | Unique uppercase alphanumeric | **Chain of Responsibility** |

### P0.3.2 - Project Service Layer

| Task | Description | Patterns |
|------|-------------|----------|
| ProjectService | Business logic | **Facade** |
| Create project | With owner assignment | **Factory Method** |
| Project lifecycle | Active, archived, deleted states | **State** |
| Membership management | Add/remove/update members | **Command** |
| Role enforcement | Owner, Admin, Member, Viewer | **Strategy** |

### P0.3.3 - Project API

| Task | Description | Patterns |
|------|-------------|----------|
| List projects | GET /api/v1/projects | **Iterator** |
| Create project | POST /api/v1/projects | **Factory Method** |
| Get project | GET /api/v1/projects/{key} | — |
| Update project | PATCH /api/v1/projects/{key} | **Command** |
| Delete project | DELETE /api/v1/projects/{key} | **Command**, **State** |
| List members | GET /api/v1/projects/{key}/members | **Iterator** |
| Add member | POST /api/v1/projects/{key}/members | **Command** |
| Update member | PATCH /api/v1/projects/{key}/members/{id} | **Command** |
| Remove member | DELETE /api/v1/projects/{key}/members/{id} | **Command** |

### P0.3.4 - Project UI

| Task | Description | Patterns |
|------|-------------|----------|
| Project list page | Cards/table view | — |
| Create project modal | Form with validation | — |
| Project settings page | Edit project details | — |
| Members management | Add/remove/change roles | — |
| Project switcher | Header dropdown | — |

### P0.3.5 - Testing (Projects)

| Task | Description | Patterns |
|------|-------------|----------|
| Project factory | Factory Boy project factory | **Factory Method** |
| Project unit tests | Service layer tests | — |
| Project API tests | Endpoint tests | — |
| Permission tests | Role-based access tests | — |

**Deliverables for P0.3:**
- [ ] User can create/edit/delete projects
- [ ] Project membership with roles works
- [ ] Project key uniqueness enforced
- [ ] Archive/restore functionality works
- [ ] 80%+ test coverage on project module

---

## P0.4 - Issue Management Foundation

> **Priority**: HIGH — Core value proposition
>
> **Depends On**: P0.3
>
> **Estimated Effort**: 2 weeks
>
> **Parallelization**: Can split Types/Statuses vs CRUD vs Relationships

### P0.4.1 - Issue Types & Statuses

| Task | Description | Patterns |
|------|-------------|----------|
| IssueType model | Task, Bug, Story, Epic | **Flyweight** |
| Status model | To Do, In Progress, Done | **State** |
| StatusCategory enum | Categorization for grouping | — |
| Default data seeding | Migration with defaults | — |
| Type/Status icons | Icon mapping | **Flyweight** |

### P0.4.2 - Issue Data Layer

| Task | Description | Patterns |
|------|-------------|----------|
| Issue model | Core issue entity | — |
| Issue key generation | PROJECT-123 format | **Factory Method** |
| Priority enum | Critical→None | — |
| Label model | Many-to-many labels | **Flyweight** |
| Issue repository | CRUD + complex queries | **Repository** |

### P0.4.3 - Issue Service Layer

| Task | Description | Patterns |
|------|-------------|----------|
| IssueService | Business logic | **Facade** |
| Create issue | With key generation | **Factory Method** |
| Update issue | Field changes with history | **Command**, **Memento** |
| Status transitions | Validate allowed transitions | **State** |
| Delete/restore | Soft delete with recovery | **State**, **Command** |

### P0.4.4 - Issue Relationships

| Task | Description | Patterns |
|------|-------------|----------|
| Parent-child | Subtask relationship | **Composite** |
| IssueLink model | Issue-to-issue links | — |
| Link types | Blocks, relates to, duplicates | **Strategy** |
| Circular detection | Prevent circular parents | **Visitor** |

### P0.4.5 - Issue API

| Task | Description | Patterns |
|------|-------------|----------|
| List issues | GET /api/v1/projects/{key}/issues | **Iterator** |
| Create issue | POST /api/v1/projects/{key}/issues | **Factory Method** |
| Get issue | GET /api/v1/issues/{key} | — |
| Update issue | PATCH /api/v1/issues/{key} | **Command** |
| Delete issue | DELETE /api/v1/issues/{key} | **Command** |
| List labels | GET /api/v1/projects/{key}/labels | **Iterator** |
| Manage labels | CRUD for labels | **Factory Method** |
| Link issues | POST /api/v1/issues/{key}/links | **Command** |
| Unlink issues | DELETE /api/v1/issues/{key}/links/{id} | **Command** |

### P0.4.6 - Issue UI (Basic)

| Task | Description | Patterns |
|------|-------------|----------|
| Issue list (table) | Sortable, filterable | **Strategy** |
| Create issue form | Modal or page | — |
| Issue detail page | Full issue view | **Composite** |
| Inline editing | HTMX field updates | **Command** |
| Quick filters | Status, assignee, type | **Strategy** |

### P0.4.7 - Testing (Issues)

| Task | Description | Patterns |
|------|-------------|----------|
| Issue factory | Factory Boy with relationships | **Factory Method** |
| Issue unit tests | Service + state tests | — |
| Issue API tests | Full CRUD tests | — |
| Relationship tests | Parent/child, links | — |

**Deliverables for P0.4:**
- [ ] User can create/edit/delete issues
- [ ] Issue keys auto-generate correctly
- [ ] Status transitions work
- [ ] Parent-child and linking works
- [ ] Labels can be managed
- [ ] 80%+ test coverage

---

## P0.5 - Issue Collaboration

> **Priority**: HIGH — Essential for team usage
>
> **Depends On**: P0.4
>
> **Estimated Effort**: 1.5 weeks
>
> **Parallelization**: Comments, Activity, Attachments can be parallel

### P0.5.1 - Comments

| Task | Description | Patterns |
|------|-------------|----------|
| Comment model | Issue comments | — |
| Comment repository | CRUD operations | **Repository** |
| CommentService | Business logic | **Facade** |
| Markdown rendering | CommonMark support | **Strategy** |
| Comment API | CRUD endpoints | **Factory Method**, **Command** |
| Comment UI | Threaded display, add/edit | — |
| Comment tests | Unit + integration | — |

### P0.5.2 - Activity & History

| Task | Description | Patterns |
|------|-------------|----------|
| Activity model | Change tracking | **Memento** |
| Field change capture | Old/new value storage | **Memento** |
| Activity types | Created, updated, commented, etc. | **Strategy** |
| Activity service | Recording + querying | **Observer** |
| Activity API | GET /api/v1/issues/{key}/activity | **Iterator** |
| Activity UI | Combined timeline view | **Composite** |
| Activity tests | Change capture tests | — |

### P0.5.3 - File Attachments

| Task | Description | Patterns |
|------|-------------|----------|
| Attachment model | File metadata | — |
| Storage backend | Local filesystem (default) | **Strategy** |
| Upload handling | Chunked upload support | — |
| File validation | Type, size limits | **Chain of Responsibility** |
| Attachment API | Upload, download, delete | **Strategy** |
| Attachment UI | Upload zone, preview, list | — |
| Attachment tests | Upload/download tests | — |

**Deliverables for P0.5:**
- [ ] Users can comment on issues
- [ ] Activity log tracks all changes
- [ ] Files can be attached to issues
- [ ] Markdown renders in comments/descriptions
- [ ] 80%+ test coverage

---

## P0.6 - Views & Navigation

> **Priority**: MEDIUM-HIGH — Usability critical
>
> **Depends On**: P0.4
>
> **Estimated Effort**: 1.5 weeks
>
> **Parallelization**: List View, Board View, Search can be parallel

### P0.6.1 - List View Enhancements

| Task | Description | Patterns |
|------|-------------|----------|
| Column configuration | Show/hide columns | **Strategy** |
| Multi-column sorting | Sort by multiple fields | **Strategy** |
| Advanced filters | Complex filter combinations | **Builder** |
| Filter persistence | Save filter state | **Memento** |
| Pagination controls | Page size, navigation | **Iterator** |
| Bulk selection | Select multiple issues | — |

### P0.6.2 - Kanban Board

| Task | Description | Patterns |
|------|-------------|----------|
| Board view page | Columns by status | **Strategy** |
| Card component | Issue card display | **Template Method** |
| Drag and drop | Status change via drag | **Command** |
| Board filters | Filter cards shown | **Strategy** |
| Column counts | Issue count badges | — |
| Board settings | Column visibility | **Strategy** |

### P0.6.3 - Issue Detail Enhancements

| Task | Description | Patterns |
|------|-------------|----------|
| Side panel mode | Slide-out panel view | **Strategy** |
| Full page mode | Dedicated page view | **Strategy** |
| Keyboard shortcuts | Navigate with keys | **Command** |
| Quick actions | Status change shortcuts | **Command** |
| Related issues | Show linked/children | **Composite** |

### P0.6.4 - Search

| Task | Description | Patterns |
|------|-------------|----------|
| Search index | PostgreSQL full-text search | **Strategy** |
| Global search | Across all projects | **Strategy** |
| Project search | Within project | **Strategy** |
| Search API | GET /api/v1/search | **Strategy** |
| Search UI | Header search bar | — |
| Recent searches | Search history | **Memento** |
| Search results page | Paginated results | **Iterator** |

**Deliverables for P0.6:**
- [ ] List view with sorting/filtering works
- [ ] Kanban board with drag-drop works
- [ ] Search returns relevant results
- [ ] Multiple view modes available
- [ ] 80%+ test coverage

---

## P0.7 - Notifications & Email

> **Priority**: MEDIUM — Important for collaboration
>
> **Depends On**: P0.4, P0.5
>
> **Estimated Effort**: 1 week
>
> **Parallelization**: Email infra vs Notification logic can be parallel

### P0.7.1 - Email Infrastructure

| Task | Description | Patterns |
|------|-------------|----------|
| Email service | SMTP sending abstraction | **Strategy** |
| Email templates | Base Jinja2 templates | **Template Method** |
| Email queue | Async sending (sync for now) | **Command** |
| Template rendering | Context-aware rendering | **Template Method** |

### P0.7.2 - Notification System

| Task | Description | Patterns |
|------|-------------|----------|
| Notification model | Persisted notifications | — |
| NotificationService | Trigger + delivery | **Observer** |
| Event subscribers | Issue events → notifications | **Observer** |
| Notification types | Assignment, mention, comment, etc. | **Strategy** |

### P0.7.3 - Notification Triggers

| Task | Description | Patterns |
|------|-------------|----------|
| Assignment trigger | On assignee change | **Observer** |
| Mention trigger | @mention detection | **Observer** |
| Comment trigger | New comment notification | **Observer** |
| Status trigger | On status change | **Observer** |
| Watch system | Subscribe to issues | **Observer** |

### P0.7.4 - Notification Preferences

| Task | Description | Patterns |
|------|-------------|----------|
| Preference model | User notification settings | — |
| Preference UI | Settings page section | — |
| Auto-watch config | Default watch behavior | **Strategy** |

### P0.7.5 - Notification API & UI

| Task | Description | Patterns |
|------|-------------|----------|
| List notifications | GET /api/v1/notifications | **Iterator** |
| Mark read | PATCH /api/v1/notifications/{id} | **Command** |
| Mark all read | POST /api/v1/notifications/read-all | **Command** |
| Notification dropdown | Header bell icon | **Observer** |
| Notification page | Full notification list | — |

**Deliverables for P0.7:**
- [ ] Email notifications send on triggers
- [ ] In-app notifications work
- [ ] Users can configure preferences
- [ ] Watch/unwatch issues works
- [ ] 80%+ test coverage

---

## P0.8 - API & Documentation

> **Priority**: MEDIUM — Essential for integrations
>
> **Depends On**: P0.2-P0.7
>
> **Estimated Effort**: 1 week
>
> **Parallelization**: API tokens vs Docs can be parallel

### P0.8.1 - API Polish

| Task | Description | Patterns |
|------|-------------|----------|
| Response envelope | Standard response format | **Template Method** |
| Error responses | Consistent error format | **Template Method** |
| Pagination standard | Cursor/offset pagination | **Iterator** |
| API versioning | /api/v1/ prefix enforcement | **Strategy** |
| Rate limiting (basic) | Simple rate limits | **Decorator** |

### P0.8.2 - API Tokens

| Task | Description | Patterns |
|------|-------------|----------|
| APIToken model | Long-lived tokens | — |
| Token generation | Secure token creation | **Factory Method** |
| Token scopes | Read, write, admin | **Strategy** |
| Token API | CRUD for user tokens | — |
| Token UI | Token management page | — |

### P0.8.3 - Documentation

| Task | Description | Patterns |
|------|-------------|----------|
| OpenAPI customization | Enhanced schema docs | — |
| Swagger UI | Interactive explorer | — |
| ReDoc | Alternative docs | — |
| User documentation | MkDocs site | — |
| Deployment guide | Installation instructions | — |

**Deliverables for P0.8:**
- [ ] API documentation complete
- [ ] API tokens work for authentication
- [ ] User documentation published
- [ ] Rate limiting prevents abuse
- [ ] Deployment guide available

---

## P0.9 - MVP Deployment & Release

> **Priority**: CRITICAL — Makes P0 deliverable
>
> **Depends On**: P0.1-P0.8
>
> **Estimated Effort**: 1 week

### P0.9.1 - Production Readiness

| Task | Description | Patterns |
|------|-------------|----------|
| Security audit | OWASP checklist | — |
| Performance testing | Load testing basics | — |
| Error monitoring | Sentry or similar | — |
| Backup strategy | Database backup docs | — |

### P0.9.2 - Docker Compose (Production)

| Task | Description | Patterns |
|------|-------------|----------|
| Production compose | docker-compose.prod.yml | — |
| Environment template | .env.example for prod | — |
| Nginx configuration | Reverse proxy setup | — |
| SSL/TLS setup | Let's Encrypt integration | — |

### P0.9.3 - Release

| Task | Description | Patterns |
|------|-------------|----------|
| Changelog | Complete P0 changelog | — |
| Release notes | User-facing release notes | — |
| Version tag | v0.1.0 tag | — |
| Docker image | Published to registry | — |
| Announcement | Release announcement | — |

**MVP Release Checklist:**
- [ ] All P0 features complete and tested
- [ ] Security audit passed
- [ ] Performance acceptable under load
- [ ] Documentation complete
- [ ] Docker images published
- [ ] v0.1.0 released

---

# P1 - Essential Features

> **Goal**: Sprint management, time tracking, and team collaboration features.
>
> **Timeline**: 6-8 weeks after MVP
>
> **Milestone**: v0.2.0 release

---

## P1.0 - P1 Infrastructure

> **Priority**: Required before P1 features
>
> **Depends On**: P0 Complete
>
> **Estimated Effort**: 3 days

### P1.0.1 - Redis Setup

| Task | Description | Patterns |
|------|-------------|----------|
| Redis service | Docker Compose addition | — |
| Redis client | Connection configuration | **Singleton** |
| Cache utilities | Cache decorator helpers | **Decorator**, **Proxy** |
| Session store | Redis session backend | **Flyweight** |

### P1.0.2 - Background Tasks (Basic)

| Task | Description | Patterns |
|------|-------------|----------|
| Task queue setup | Simple async tasks | **Command** |
| Task scheduling | Basic scheduled tasks | **Command** |

---

## P1.1 - Sprint/Cycle Management

> **Priority**: HIGH
>
> **Depends On**: P0.4 (Issues)
>
> **Estimated Effort**: 1.5 weeks
>
> **Parallelization**: Can develop alongside P1.2, P1.3

### P1.1.1 - Sprint Data Layer

| Task | Description | Patterns |
|------|-------------|----------|
| Sprint model | Name, dates, goal, state | **State** |
| Sprint states | Planning, Active, Completed | **State** |
| Sprint-Issue relation | Issue assignment to sprint | — |
| Sprint repository | CRUD + queries | **Repository** |

### P1.1.2 - Sprint Service Layer

| Task | Description | Patterns |
|------|-------------|----------|
| SprintService | Business logic | **Facade** |
| Create sprint | With validation | **Factory Method** |
| Start sprint | State transition | **State**, **Command** |
| Complete sprint | Handle incomplete issues | **State**, **Command** |
| Scope tracking | Track additions/removals | **Observer**, **Memento** |

### P1.1.3 - Sprint API

| Task | Description | Patterns |
|------|-------------|----------|
| List sprints | GET /api/v1/projects/{key}/sprints | **Iterator** |
| Create sprint | POST /api/v1/projects/{key}/sprints | **Factory Method** |
| Get sprint | GET /api/v1/sprints/{id} | — |
| Update sprint | PATCH /api/v1/sprints/{id} | **Command** |
| Start sprint | POST /api/v1/sprints/{id}/start | **Command** |
| Complete sprint | POST /api/v1/sprints/{id}/complete | **Command** |
| Add issues | POST /api/v1/sprints/{id}/issues | **Command** |
| Remove issues | DELETE /api/v1/sprints/{id}/issues | **Command** |

### P1.1.4 - Sprint UI

| Task | Description | Patterns |
|------|-------------|----------|
| Sprint list | Active + upcoming sprints | — |
| Sprint board | Filtered Kanban view | **Strategy** |
| Sprint progress | Progress bar/stats | **Visitor** |
| Complete sprint modal | Handle incomplete issues | — |

### P1.1.5 - Sprint Reporting

| Task | Description | Patterns |
|------|-------------|----------|
| Burndown chart | Daily remaining work | **Builder** |
| Velocity chart | Points per sprint | **Builder** |
| Sprint report | Summary statistics | **Visitor** |

### P1.1.6 - Testing (Sprints)

| Task | Description | Patterns |
|------|-------------|----------|
| Sprint factory | Factory Boy sprint factory | **Factory Method** |
| Sprint unit tests | State transition tests | — |
| Sprint API tests | Full workflow tests | — |

**Deliverables for P1.1:**
- [ ] Sprints can be created and managed
- [ ] Sprint state transitions work correctly
- [ ] Burndown/velocity charts render
- [ ] Sprint board view works
- [ ] 80%+ test coverage

---

## P1.2 - Backlog Management

> **Priority**: HIGH
>
> **Depends On**: P1.1 (Sprints)
>
> **Estimated Effort**: 1 week
>
> **Parallelization**: Can develop alongside P1.3, P1.4

### P1.2.1 - Backlog Features

| Task | Description | Patterns |
|------|-------------|----------|
| Backlog view | Unassigned issues list | **Iterator** |
| Rank field | Issue ordering field | **Strategy** |
| Drag-drop ordering | Reorder backlog | **Command** |
| Story points field | Effort estimation | — |
| Velocity calculation | Average points per sprint | **Strategy** |

### P1.2.2 - Sprint Planning

| Task | Description | Patterns |
|------|-------------|----------|
| Planning view | Backlog + Sprint side-by-side | **Composite** |
| Drag to sprint | Move issues to sprint | **Command** |
| Capacity indicator | Points vs. capacity | **Visitor** |
| Bulk move | Select multiple issues | **Command** |

### P1.2.3 - Backlog API

| Task | Description | Patterns |
|------|-------------|----------|
| Get backlog | GET /api/v1/projects/{key}/backlog | **Iterator** |
| Reorder backlog | PATCH /api/v1/projects/{key}/backlog/order | **Command** |
| Set story points | PATCH /api/v1/issues/{key} (points field) | **Command** |

**Deliverables for P1.2:**
- [ ] Backlog view shows unassigned issues
- [ ] Drag-drop reordering works
- [ ] Sprint planning view works
- [ ] Story points tracked
- [ ] 80%+ test coverage

---

## P1.3 - Time Tracking

> **Priority**: HIGH
>
> **Depends On**: P0.4 (Issues)
>
> **Estimated Effort**: 2 weeks
>
> **Parallelization**: Timer vs Manual Entry can be parallel

### P1.3.1 - Time Entry Core

| Task | Description | Patterns |
|------|-------------|----------|
| TimeEntry model | Duration, date, description | — |
| Activity type model | Dev, Testing, Review, etc. | **Flyweight** |
| TimeEntry repository | CRUD operations | **Repository** |
| TimeTrackingService | Business logic | **Facade** |

### P1.3.2 - Timer Functionality

| Task | Description | Patterns |
|------|-------------|----------|
| ActiveTimer model | Running timer state | **State** |
| Start timer | Create active timer | **Command**, **State** |
| Stop timer | Log elapsed time | **Command**, **State** |
| Pause/Resume | Timer state management | **State** |
| Auto-pause | Inactivity detection | **Observer** |
| Timer switching | Switch between issues | **Mediator** |

### P1.3.3 - Manual Time Entry

| Task | Description | Patterns |
|------|-------------|----------|
| Log time form | Manual entry UI | — |
| Bulk time entry | Multiple issues at once | **Command** |
| Edit time entry | Modify logged time | **Command**, **Memento** |
| Delete time entry | Remove entry | **Command** |

### P1.3.4 - Estimates

| Task | Description | Patterns |
|------|-------------|----------|
| Original estimate | Initial estimate field | — |
| Remaining estimate | Remaining work | **Observer** |
| Auto-update remaining | Reduce on log | **Observer** |
| Progress indicator | Spent vs. estimate | **Strategy** |

### P1.3.5 - Time Tracking API

| Task | Description | Patterns |
|------|-------------|----------|
| List time entries | GET /api/v1/issues/{key}/time-entries | **Iterator** |
| Log time | POST /api/v1/issues/{key}/time-entries | **Factory Method** |
| Update entry | PATCH /api/v1/time-entries/{id} | **Command** |
| Delete entry | DELETE /api/v1/time-entries/{id} | **Command** |
| Start timer | POST /api/v1/issues/{key}/timer/start | **Command** |
| Stop timer | POST /api/v1/issues/{key}/timer/stop | **Command** |
| Pause timer | POST /api/v1/timer/pause | **Command** |
| Get active timer | GET /api/v1/timer/active | — |

### P1.3.6 - Time Tracking UI

| Task | Description | Patterns |
|------|-------------|----------|
| Timer widget | Header timer display | **Observer** |
| Time log section | Issue detail section | — |
| Log time modal | Quick time entry | — |
| Personal timesheet | Daily/weekly view | **Builder** |

### P1.3.7 - Testing (Time Tracking)

| Task | Description | Patterns |
|------|-------------|----------|
| TimeEntry factory | Factory Boy factory | **Factory Method** |
| Timer state tests | State transition tests | — |
| Time tracking API tests | Full workflow tests | — |

**Deliverables for P1.3:**
- [ ] Timer start/stop/pause works
- [ ] Manual time entry works
- [ ] Estimates and remaining calculate correctly
- [ ] Personal timesheet view works
- [ ] 80%+ test coverage

---

## P1.4 - Custom Fields

> **Priority**: MEDIUM
>
> **Depends On**: P0.4 (Issues)
>
> **Estimated Effort**: 1.5 weeks
>
> **Parallelization**: Can develop alongside P1.5

### P1.4.1 - Field Definition

| Task | Description | Patterns |
|------|-------------|----------|
| CustomField model | Field definition | **Abstract Factory** |
| Field types | Text, number, date, select, etc. | **Factory Method** |
| FieldOption model | Options for select fields | — |
| Field context | Per project/issue type | **Strategy** |

### P1.4.2 - Field Value Storage

| Task | Description | Patterns |
|------|-------------|----------|
| CustomFieldValue model | Issue field values | — |
| Value validation | Type-specific validation | **Chain of Responsibility** |
| Default values | Field default handling | **Prototype** |

### P1.4.3 - Custom Fields API

| Task | Description | Patterns |
|------|-------------|----------|
| List fields | GET /api/v1/projects/{key}/fields | **Iterator** |
| Create field | POST /api/v1/projects/{key}/fields | **Factory Method** |
| Update field | PATCH /api/v1/fields/{id} | **Command** |
| Delete field | DELETE /api/v1/fields/{id} | **Command** |
| Set field value | Via issue update | **Command** |

### P1.4.4 - Custom Fields UI

| Task | Description | Patterns |
|------|-------------|----------|
| Field manager | Admin field configuration | — |
| Field rendering | Dynamic form fields | **Strategy** |
| Field in issue view | Display custom fields | — |

**Deliverables for P1.4:**
- [ ] Custom fields can be created
- [ ] All field types work
- [ ] Fields appear in issue forms
- [ ] Field contexts work
- [ ] 80%+ test coverage

---

## P1.5 - Workflow Engine

> **Priority**: MEDIUM
>
> **Depends On**: P0.4 (Issues)
>
> **Estimated Effort**: 1.5 weeks
>
> **Parallelization**: Can develop alongside P1.4

### P1.5.1 - Workflow Definition

| Task | Description | Patterns |
|------|-------------|----------|
| Workflow model | Named workflow definition | **Builder** |
| Transition model | Allowed status changes | **State** |
| Workflow-Status relation | Statuses in workflow | — |

### P1.5.2 - Workflow Service

| Task | Description | Patterns |
|------|-------------|----------|
| WorkflowService | Business logic | **Facade** |
| Transition validation | Check allowed transitions | **State** |
| Initial status | Set on issue creation | **State** |
| Done detection | Check if status is "done" | **State** |

### P1.5.3 - Workflow Assignment

| Task | Description | Patterns |
|------|-------------|----------|
| Project workflow | Default project workflow | **Strategy** |
| Issue type workflow | Per-type workflow | **Strategy** |
| Workflow cloning | Copy workflow | **Prototype** |

### P1.5.4 - Workflow API

| Task | Description | Patterns |
|------|-------------|----------|
| List workflows | GET /api/v1/workflows | **Iterator** |
| Create workflow | POST /api/v1/workflows | **Builder** |
| Get workflow | GET /api/v1/workflows/{id} | — |
| Update workflow | PATCH /api/v1/workflows/{id} | **Command** |
| Add transition | POST /api/v1/workflows/{id}/transitions | **Command** |

### P1.5.5 - Workflow UI

| Task | Description | Patterns |
|------|-------------|----------|
| Workflow editor | Visual workflow builder | **Builder** |
| Status manager | Create/edit statuses | — |
| Workflow assignment | Assign to project/type | — |

**Deliverables for P1.5:**
- [ ] Custom workflows can be created
- [ ] Transitions are enforced
- [ ] Workflows can be assigned
- [ ] Visual workflow editor works
- [ ] 80%+ test coverage

---

## P1.6 - Roles & Permissions

> **Priority**: MEDIUM
>
> **Depends On**: P0.2 (Auth), P0.3 (Projects)
>
> **Estimated Effort**: 1 week

### P1.6.1 - Permission System

| Task | Description | Patterns |
|------|-------------|----------|
| Permission model | Granular permissions | **Strategy** |
| Role-Permission mapping | Permissions per role | **Strategy** |
| Permission checker | Check user permissions | **Decorator**, **Chain of Responsibility** |

### P1.6.2 - Permission Enforcement

| Task | Description | Patterns |
|------|-------------|----------|
| API permission checks | Endpoint protection | **Decorator** |
| UI permission checks | Conditional UI elements | **Strategy** |
| Service layer checks | Business logic protection | **Decorator** |

### P1.6.3 - Permission API

| Task | Description | Patterns |
|------|-------------|----------|
| Get permissions | GET /api/v1/projects/{key}/permissions | — |
| Check permission | GET /api/v1/permissions/check | — |

**Deliverables for P1.6:**
- [ ] Granular permissions work
- [ ] All endpoints check permissions
- [ ] UI respects permissions
- [ ] 80%+ test coverage

---

## P1.7 - Enhanced Notifications

> **Priority**: MEDIUM
>
> **Depends On**: P0.7 (Notifications)
>
> **Estimated Effort**: 1 week

### P1.7.1 - In-App Notifications

| Task | Description | Patterns |
|------|-------------|----------|
| Real-time updates | WebSocket or polling | **Observer** |
| Notification grouping | Group related notifications | **Composite** |
| Read/unread tracking | Track read state | — |

### P1.7.2 - @Mentions

| Task | Description | Patterns |
|------|-------------|----------|
| Mention detection | Parse @username | **Interpreter** |
| Mention autocomplete | User suggestions | **Iterator** |
| Mention highlighting | Visual highlighting | **Decorator** |

**Deliverables for P1.7:**
- [ ] In-app notifications work in real-time
- [ ] @mentions work in comments/descriptions
- [ ] Autocomplete suggests users
- [ ] 80%+ test coverage

---

## P1.8 - Modules & Components

> **Priority**: LOW
>
> **Depends On**: P0.4 (Issues)
>
> **Estimated Effort**: 1 week

### P1.8.1 - Modules

| Task | Description | Patterns |
|------|-------------|----------|
| Module model | Name, dates, lead | — |
| Module-Issue relation | Issues in module | — |
| Module progress | Completion tracking | **Visitor** |
| Module API & UI | CRUD + views | **Factory Method**, **Iterator** |

### P1.8.2 - Components

| Task | Description | Patterns |
|------|-------------|----------|
| Component model | Name, lead, default assignee | — |
| Component-Issue relation | Issue component | — |
| Auto-assignment | Assign based on component | **Strategy** |
| Component API & UI | CRUD + views | **Factory Method**, **Iterator** |

**Deliverables for P1.8:**
- [ ] Modules can be created and managed
- [ ] Components work with auto-assignment
- [ ] 80%+ test coverage

---

## P1.9 - P1 Deployment & Release

> **Priority**: CRITICAL
>
> **Depends On**: P1.1-P1.8
>
> **Estimated Effort**: 3 days

### P1.9.1 - Release Tasks

| Task | Description |
|------|-------------|
| Integration testing | Full P1 integration tests |
| Performance testing | Load testing with new features |
| Migration testing | Test upgrade from P0 |
| Documentation update | User docs for P1 features |
| Changelog | P1 changelog |
| Release | v0.2.0 tag and publish |

**P1 Release Checklist:**
- [ ] All P1 features complete and tested
- [ ] Upgrade path from v0.1.x works
- [ ] Performance acceptable
- [ ] Documentation updated
- [ ] v0.2.0 released

---

# P2 - Enhanced Functionality

> **Goal**: Reports, integrations, and advanced views for mature teams.
>
> **Timeline**: 6-8 weeks after P1
>
> **Milestone**: v0.3.0 release

---

## P2.0 - P2 Infrastructure

> **Priority**: Required before P2 features
>
> **Depends On**: P1 Complete
>
> **Estimated Effort**: 1 week

### P2.0.1 - Celery Setup

| Task | Description | Patterns |
|------|-------------|----------|
| Celery configuration | Worker setup | — |
| Task routing | Queue configuration | **Strategy** |
| Task monitoring | Flower or similar | **Observer** |
| Scheduled tasks | Celery Beat setup | **Command** |

### P2.0.2 - Background Processing

| Task | Description | Patterns |
|------|-------------|----------|
| Async email sending | Move email to queue | **Command** |
| Async webhooks | Webhook delivery queue | **Command** |
| Bulk operation queue | Large operations async | **Command** |
| Failed task handling | Retry logic | **Chain of Responsibility** |

---

## P2.1 - Billable Time & Cost Tracking

> **Priority**: HIGH
>
> **Depends On**: P1.3 (Time Tracking)
>
> **Estimated Effort**: 1.5 weeks

### P2.1.1 - Billable Time

| Task | Description | Patterns |
|------|-------------|----------|
| Billable flag | Time entry billable field | — |
| Billable rules | Per activity/project defaults | **Strategy** |
| Billable summary | Aggregated billable time | **Visitor** |

### P2.1.2 - Cost Tracking

| Task | Description | Patterns |
|------|-------------|----------|
| Hourly rates | User/role/project rates | **Strategy** |
| Cost calculation | Auto-calculate from time | **Visitor** |
| Currency settings | Multi-currency support | **Strategy** |
| Cost per issue/project | Aggregated costs | **Visitor** |

### P2.1.3 - Timesheets

| Task | Description | Patterns |
|------|-------------|----------|
| Weekly timesheet | Grid entry view | **Builder** |
| Timesheet export | CSV/Excel export | **Strategy** |
| Copy previous week | Clone entries | **Prototype** |

### P2.1.4 - Time Approval

| Task | Description | Patterns |
|------|-------------|----------|
| Approval workflow | Submit/approve/reject | **State**, **Chain of Responsibility** |
| Approval status | Pending/Approved/Rejected | **State** |
| Lock approved | Prevent edits | **State** |
| Approval notifications | Notify on state change | **Observer** |

**Deliverables for P2.1:**
- [ ] Billable time tracking works
- [ ] Cost calculation works
- [ ] Timesheets can be submitted for approval
- [ ] 80%+ test coverage

---

## P2.2 - Reports & Analytics

> **Priority**: HIGH
>
> **Depends On**: P1.1 (Sprints), P1.3 (Time Tracking)
>
> **Estimated Effort**: 2 weeks

### P2.2.1 - Report Framework

| Task | Description | Patterns |
|------|-------------|----------|
| Report builder base | Report generation framework | **Builder**, **Template Method** |
| Data aggregation | Metric calculation | **Visitor** |
| Chart rendering | Chart.js integration | **Builder** |
| Export framework | PDF/Excel/CSV export | **Strategy** |

### P2.2.2 - Built-in Reports

| Task | Description | Patterns |
|------|-------------|----------|
| Created vs. resolved | Issue creation chart | **Builder** |
| Cumulative flow | Work flow over time | **Builder** |
| Cycle/lead time | Time metrics | **Visitor** |
| Workload report | Per-assignee metrics | **Visitor** |

### P2.2.3 - Time & Cost Reports

| Task | Description | Patterns |
|------|-------------|----------|
| Time by project/user | Time aggregation | **Visitor** |
| Cost by project/user | Cost aggregation | **Visitor** |
| Budget vs. actual | Comparison report | **Strategy** |
| Estimate accuracy | Estimate vs. actual | **Visitor** |

### P2.2.4 - Custom Reports

| Task | Description | Patterns |
|------|-------------|----------|
| Report builder UI | Custom report creation | **Builder** |
| Save reports | Persist configurations | **Memento** |
| Share reports | Team sharing | **Command** |
| Scheduled reports | Auto-email reports | **Command**, **Observer** |

### P2.2.5 - Dashboards

| Task | Description | Patterns |
|------|-------------|----------|
| Dashboard builder | Widget-based dashboards | **Builder**, **Composite** |
| Widget library | Available widgets | **Factory Method** |
| Dashboard sharing | Team/personal dashboards | **Command** |
| Real-time refresh | Auto-refresh widgets | **Observer** |

**Deliverables for P2.2:**
- [ ] Built-in reports work
- [ ] Custom reports can be created
- [ ] Dashboards can be built
- [ ] Reports can be exported
- [ ] 80%+ test coverage

---

## P2.3 - Roadmap & Timeline

> **Priority**: MEDIUM
>
> **Depends On**: P0.4 (Issues), P1.1 (Sprints)
>
> **Estimated Effort**: 1.5 weeks

### P2.3.1 - Gantt Chart

| Task | Description | Patterns |
|------|-------------|----------|
| Gantt view | Timeline visualization | **Builder** |
| Date bars | Visual date ranges | **Composite** |
| Drag to reschedule | Date change via drag | **Command** |
| Zoom levels | Day/week/month/quarter | **Strategy** |

### P2.3.2 - Dependencies

| Task | Description | Patterns |
|------|-------------|----------|
| Dependency model | Issue dependencies | **Strategy** |
| Dependency lines | Visual connections | **Composite** |
| Critical path | Path calculation | **Visitor** |
| Dependency warnings | Blocked item alerts | **Observer** |

### P2.3.3 - Milestones

| Task | Description | Patterns |
|------|-------------|----------|
| Milestone model | Name, date | — |
| Milestone-Issue relation | Link issues | — |
| Milestone progress | Completion tracking | **Visitor** |
| Milestone on Gantt | Diamond marker | **Composite** |

### P2.3.4 - Roadmap View

| Task | Description | Patterns |
|------|-------------|----------|
| Epic roadmap | High-level timeline | **Builder** |
| Swimlanes | Grouping options | **Strategy** |
| Roadmap export | Image/PDF export | **Strategy** |

**Deliverables for P2.3:**
- [ ] Gantt chart renders correctly
- [ ] Dependencies can be created
- [ ] Milestones work
- [ ] Roadmap view works
- [ ] 80%+ test coverage

---

## P2.4 - Wiki/Documentation

> **Priority**: MEDIUM
>
> **Depends On**: P0.3 (Projects)
>
> **Estimated Effort**: 1.5 weeks

### P2.4.1 - Wiki Core

| Task | Description | Patterns |
|------|-------------|----------|
| WikiPage model | Title, content, hierarchy | **Composite** |
| Page versioning | Version history | **Memento** |
| Rich text editor | WYSIWYG + markdown | **Strategy** |

### P2.4.2 - Wiki Features

| Task | Description | Patterns |
|------|-------------|----------|
| Page hierarchy | Parent/child pages | **Composite** |
| Version comparison | Diff view | **Strategy** |
| Page templates | Pre-built templates | **Prototype** |
| Issue linking | Reference issues | — |
| Wiki search | Full-text search | **Strategy** |

### P2.4.3 - Wiki API & UI

| Task | Description | Patterns |
|------|-------------|----------|
| Wiki API | CRUD endpoints | **Factory Method**, **Command** |
| Wiki UI | Page view/edit | — |
| TOC generation | Auto-generate TOC | **Visitor** |

**Deliverables for P2.4:**
- [ ] Wiki pages can be created
- [ ] Page versioning works
- [ ] Hierarchy works
- [ ] 80%+ test coverage

---

## P2.5 - Integrations

> **Priority**: MEDIUM
>
> **Depends On**: P2.0 (Background Processing)
>
> **Estimated Effort**: 1.5 weeks

### P2.5.1 - Webhooks

| Task | Description | Patterns |
|------|-------------|----------|
| Webhook model | URL, events, secret | — |
| Webhook delivery | Async delivery | **Command** |
| Webhook logs | Delivery history | **Iterator** |
| Retry logic | Failed delivery retry | **Chain of Responsibility** |

### P2.5.2 - Chat Integrations

| Task | Description | Patterns |
|------|-------------|----------|
| Integration framework | Base integration class | **Abstract Factory** |
| Slack integration | Slack notifications | **Adapter** |
| Discord integration | Discord notifications | **Adapter** |
| Message templates | Customizable messages | **Template Method** |

### P2.5.3 - Email Integration

| Task | Description | Patterns |
|------|-------------|----------|
| Email to issue | Create issue from email | **Factory Method**, **Adapter** |
| Email parsing | Extract fields | **Interpreter** |
| Reply handling | Comment via reply | **Adapter** |

### P2.5.4 - Calendar

| Task | Description | Patterns |
|------|-------------|----------|
| iCal export | Due date export | **Adapter** |
| Calendar view | Built-in calendar | **Builder** |

**Deliverables for P2.5:**
- [ ] Webhooks can be configured
- [ ] Slack/Discord integrations work
- [ ] Email-to-issue works
- [ ] 80%+ test coverage

---

## P2.6 - Advanced Views

> **Priority**: LOW
>
> **Depends On**: P0.6 (Views)
>
> **Estimated Effort**: 1 week

### P2.6.1 - Saved Views

| Task | Description | Patterns |
|------|-------------|----------|
| SavedView model | Filter/sort configuration | **Memento** |
| View sharing | Team views | **Command** |
| Default views | Per-project defaults | **Strategy** |

### P2.6.2 - Board Customization

| Task | Description | Patterns |
|------|-------------|----------|
| Swimlanes | Grouping options | **Strategy** |
| WIP limits | Column limits | **Observer** |
| Card layout | Customizable cards | **Template Method** |

### P2.6.3 - Table View

| Task | Description | Patterns |
|------|-------------|----------|
| Spreadsheet view | Excel-like editing | **Composite** |
| Inline editing | Direct cell editing | **Command** |
| Bulk editing | Multi-row edit | **Command** |

**Deliverables for P2.6:**
- [ ] Saved views work
- [ ] Board customization works
- [ ] Table view works
- [ ] 80%+ test coverage

---

## P2.7 - Subprojects & Hierarchy

> **Priority**: LOW
>
> **Depends On**: P0.3 (Projects)
>
> **Estimated Effort**: 1 week

### P2.7.1 - Subprojects

| Task | Description | Patterns |
|------|-------------|----------|
| Subproject relation | Parent/child projects | **Composite** |
| Setting inheritance | Inherit from parent | **Prototype**, **Strategy** |
| Cross-project view | Aggregate views | **Composite**, **Iterator** |

### P2.7.2 - Issue Hierarchy

| Task | Description | Patterns |
|------|-------------|----------|
| Hierarchy view | Tree view of issues | **Composite** |
| Roll-up calculations | Points/time roll-up | **Composite**, **Visitor** |

**Deliverables for P2.7:**
- [ ] Subprojects work
- [ ] Issue hierarchy view works
- [ ] Roll-ups calculate correctly
- [ ] 80%+ test coverage

---

## P2.8 - Task-Level Analytics

> **Priority**: LOW
>
> **Depends On**: P1.3 (Time Tracking), P2.2 (Reports)
>
> **Estimated Effort**: 1 week

### P2.8.1 - Issue Metrics

| Task | Description | Patterns |
|------|-------------|----------|
| Time in status | Status duration tracking | **Visitor** |
| Resolution time | Creation to done | **Visitor** |
| Reopen count | Reopened tracking | **Visitor** |
| Flow efficiency | Active vs. total time | **Visitor** |

### P2.8.2 - Issue Analytics UI

| Task | Description | Patterns |
|------|-------------|----------|
| Analytics tab | Issue detail section | **Composite** |
| Mini charts | Inline visualizations | **Builder** |
| Metric tooltips | Quick metric display | — |

**Deliverables for P2.8:**
- [ ] Issue metrics calculate correctly
- [ ] Analytics tab shows useful data
- [ ] 80%+ test coverage

---

## P2.9 - File Management

> **Priority**: LOW
>
> **Depends On**: P0.5 (Attachments)
>
> **Estimated Effort**: 1 week

### P2.9.1 - Document Library

| Task | Description | Patterns |
|------|-------------|----------|
| Project files | File repository | **Composite** |
| Folder structure | Folder organization | **Composite** |
| File versioning | Upload new versions | **Memento** |

### P2.9.2 - Storage Backends

| Task | Description | Patterns |
|------|-------------|----------|
| Storage abstraction | Backend interface | **Abstract Factory** |
| S3 compatible | AWS S3/MinIO support | **Strategy**, **Adapter** |
| Storage migration | Move between backends | **Strategy** |

**Deliverables for P2.9:**
- [ ] Document library works
- [ ] S3 storage backend works
- [ ] 80%+ test coverage

---

## P2.10 - Import/Export

> **Priority**: LOW
>
> **Depends On**: P2.0 (Background Processing)
>
> **Estimated Effort**: 1 week

### P2.10.1 - Import

| Task | Description | Patterns |
|------|-------------|----------|
| CSV import | Import from CSV | **Adapter**, **Factory Method** |
| JSON import | Import from JSON | **Adapter** |
| Import validation | Validate before import | **Chain of Responsibility** |
| Import queue | Background processing | **Command** |

### P2.10.2 - Export

| Task | Description | Patterns |
|------|-------------|----------|
| CSV export | Export to CSV | **Strategy** |
| JSON export | Full project export | **Strategy** |
| Project backup | Complete backup | **Memento** |
| Scheduled export | Auto-export | **Command** |

**Deliverables for P2.10:**
- [ ] CSV import/export works
- [ ] JSON export works
- [ ] Project backup works
- [ ] 80%+ test coverage

---

## P2.11 - P2 Deployment & Release

> **Priority**: CRITICAL
>
> **Depends On**: P2.1-P2.10
>
> **Estimated Effort**: 3 days

### P2.11.1 - Release Tasks

| Task | Description |
|------|-------------|
| Integration testing | Full P2 integration tests |
| Performance testing | Load testing with reports |
| Migration testing | Test upgrade from P1 |
| Documentation update | User docs for P2 features |
| Changelog | P2 changelog |
| Release | v0.3.0 tag and publish |

**P2 Release Checklist:**
- [ ] All P2 features complete and tested
- [ ] Upgrade path from v0.2.x works
- [ ] Performance acceptable
- [ ] Documentation updated
- [ ] v0.3.0 released

---

# P3 - Advanced Features

> **Goal**: Automation, advanced queries, and power-user features.
>
> **Timeline**: 6-8 weeks after P2
>
> **Milestone**: v0.4.0 release

---

## P3.1 - Automation Rules

> **Priority**: HIGH
>
> **Depends On**: P2.0 (Background Processing)
>
> **Estimated Effort**: 2 weeks

### P3.1.1 - Automation Engine

| Task | Description | Patterns |
|------|-------------|----------|
| Rule model | Trigger + conditions + actions | **Chain of Responsibility** |
| Trigger types | Create, update, schedule | **Observer**, **Strategy** |
| Condition builder | IF logic | **Interpreter**, **Builder** |
| Action types | Field updates, notifications | **Command** |

### P3.1.2 - Automation Actions

| Task | Description | Patterns |
|------|-------------|----------|
| Auto-assign | Rule-based assignment | **Strategy**, **Command** |
| Auto-transition | Status automation | **State**, **Command** |
| Field updates | Automatic field values | **Command** |
| Create issues | Auto-create related | **Factory Method**, **Command** |
| Send notifications | Custom notifications | **Observer**, **Command** |

### P3.1.3 - Automation UI

| Task | Description | Patterns |
|------|-------------|----------|
| Rule builder UI | Visual rule creation | **Builder** |
| Rule management | Enable/disable/order | **State** |
| Audit log | Execution history | **Observer** |

**Deliverables for P3.1:**
- [ ] Automation rules can be created
- [ ] All action types work
- [ ] Audit log tracks executions
- [ ] 80%+ test coverage

---

## P3.2 - Advanced Query Language (LQL)

> **Priority**: MEDIUM
>
> **Depends On**: P0.6 (Search)
>
> **Estimated Effort**: 2 weeks

### P3.2.1 - Query Parser

| Task | Description | Patterns |
|------|-------------|----------|
| LQL grammar | Query language definition | **Interpreter** |
| Lexer | Token parsing | **Interpreter** |
| Parser | AST generation | **Interpreter** |
| Query executor | SQL generation | **Interpreter**, **Builder** |

### P3.2.2 - Query Features

| Task | Description | Patterns |
|------|-------------|----------|
| Field queries | status = "Done" | **Interpreter** |
| Operators | =, !=, >, <, IN, CONTAINS | **Interpreter** |
| Boolean logic | AND, OR, NOT | **Interpreter** |
| Functions | currentUser(), now() | **Interpreter** |

### P3.2.3 - Query UI

| Task | Description | Patterns |
|------|-------------|----------|
| Query input | Text input with autocomplete | **Strategy** |
| Visual builder | Graphical query builder | **Builder** |
| Syntax highlighting | Code highlighting | **Strategy** |
| Query validation | Real-time validation | **Chain of Responsibility** |
| Save/share queries | Query management | **Memento**, **Command** |

**Deliverables for P3.2:**
- [ ] LQL queries work
- [ ] All operators supported
- [ ] Query UI works
- [ ] 80%+ test coverage

---

## P3.3 - SCM Integration

> **Priority**: MEDIUM
>
> **Depends On**: P2.5 (Integrations)
>
> **Estimated Effort**: 1.5 weeks

### P3.3.1 - Git Integration

| Task | Description | Patterns |
|------|-------------|----------|
| Commit linking | Link commits to issues | **Observer** |
| Branch tracking | Track branches per issue | **Observer** |
| PR/MR status | Show PR status | **Observer**, **Adapter** |

### P3.3.2 - Webhook Handlers

| Task | Description | Patterns |
|------|-------------|----------|
| GitHub webhooks | Handle GitHub events | **Adapter**, **Chain of Responsibility** |
| GitLab webhooks | Handle GitLab events | **Adapter** |
| Smart commits | Parse commit messages | **Interpreter** |

**Deliverables for P3.3:**
- [ ] GitHub integration works
- [ ] Commits link to issues
- [ ] Smart commits work
- [ ] 80%+ test coverage

---

## P3.4 - Version/Release Management

> **Priority**: MEDIUM
>
> **Depends On**: P0.4 (Issues)
>
> **Estimated Effort**: 1 week

### P3.4.1 - Versions

| Task | Description | Patterns |
|------|-------------|----------|
| Version model | Name, dates, state | **State** |
| Version states | Unreleased, Released, Archived | **State** |
| Fix version field | Issue version assignment | — |

### P3.4.2 - Release Management

| Task | Description | Patterns |
|------|-------------|----------|
| Release workflow | Mark as released | **State**, **Command** |
| Release notes | Auto-generate notes | **Template Method**, **Visitor** |
| Version roadmap | Timeline view | **Builder** |

**Deliverables for P3.4:**
- [ ] Versions can be managed
- [ ] Release notes generate correctly
- [ ] 80%+ test coverage

---

## P3.5 - Intake/Request Management

> **Priority**: LOW
>
> **Depends On**: P1.4 (Custom Fields)
>
> **Estimated Effort**: 1 week

### P3.5.1 - Intake Forms

| Task | Description | Patterns |
|------|-------------|----------|
| Form builder | Create intake forms | **Builder** |
| Form submission | Guest submissions | **Proxy** |
| Triage workflow | Accept/reject flow | **State** |
| Convert to issue | Create from request | **Factory Method** |

**Deliverables for P3.5:**
- [ ] Intake forms work
- [ ] Guest submissions work
- [ ] Triage workflow works
- [ ] 80%+ test coverage

---

## P3.6 - Templates

> **Priority**: LOW
>
> **Depends On**: P0.4 (Issues), P0.3 (Projects)
>
> **Estimated Effort**: 1 week

### P3.6.1 - Issue Templates

| Task | Description | Patterns |
|------|-------------|----------|
| Issue templates | Pre-filled templates | **Prototype** |
| Template per type | Type-specific templates | **Strategy** |

### P3.6.2 - Project Templates

| Task | Description | Patterns |
|------|-------------|----------|
| Project templates | Full project structure | **Prototype** |
| Template cloning | Clone from template | **Prototype** |

**Deliverables for P3.6:**
- [ ] Issue templates work
- [ ] Project templates work
- [ ] 80%+ test coverage

---

## P3.7 - Goals & OKRs

> **Priority**: LOW
>
> **Depends On**: P0.4 (Issues)
>
> **Estimated Effort**: 1 week

### P3.7.1 - Goal Tracking

| Task | Description | Patterns |
|------|-------------|----------|
| Goal model | Name, timeline, metrics | — |
| Goal-Issue linking | Connect work to goals | **Command** |
| Goal progress | Track completion | **Visitor** |

### P3.7.2 - OKRs

| Task | Description | Patterns |
|------|-------------|----------|
| Objective model | High-level objectives | **Composite** |
| Key Results | Measurable outcomes | **Composite** |
| OKR scoring | Score completion | **Visitor** |

**Deliverables for P3.7:**
- [ ] Goals can be created and tracked
- [ ] OKRs work
- [ ] 80%+ test coverage

---

## P3.8 - Collaboration Features

> **Priority**: LOW
>
> **Depends On**: P0.5 (Collaboration)
>
> **Estimated Effort**: 1 week

### P3.8.1 - Forums

| Task | Description | Patterns |
|------|-------------|----------|
| Forum model | Discussion boards | **Composite** |
| Topics/replies | Threaded discussions | **Composite** |

### P3.8.2 - Retrospectives

| Task | Description | Patterns |
|------|-------------|----------|
| Retro boards | What went well, improve | **Builder** |
| Action items | Track follow-ups | — |

**Deliverables for P3.8:**
- [ ] Forums work
- [ ] Retrospectives work
- [ ] 80%+ test coverage

---

## P3.9 - Client Portal

> **Priority**: LOW
>
> **Depends On**: P1.6 (Permissions)
>
> **Estimated Effort**: 1 week

### P3.9.1 - Client Access

| Task | Description | Patterns |
|------|-------------|----------|
| Client role | Limited access role | **Strategy**, **Decorator** |
| Client dashboard | Simplified view | **Facade** |
| Client branding | Custom branding | **Strategy** |

### P3.9.2 - Client Collaboration

| Task | Description | Patterns |
|------|-------------|----------|
| Client comments | Limited commenting | **Decorator** |
| Approval workflow | Client approval | **State** |
| Progress reports | Client-facing reports | **Builder** |

**Deliverables for P3.9:**
- [ ] Client portal works
- [ ] Client approval works
- [ ] 80%+ test coverage

---

## P3.10 - P3 Deployment & Release

> **Priority**: CRITICAL
>
> **Depends On**: P3.1-P3.9
>
> **Estimated Effort**: 3 days

### P3.10.1 - Release Tasks

| Task | Description |
|------|-------------|
| Integration testing | Full P3 integration tests |
| Automation testing | Rule engine testing |
| Migration testing | Test upgrade from P2 |
| Documentation update | User docs for P3 features |
| Changelog | P3 changelog |
| Release | v0.4.0 tag and publish |

**P3 Release Checklist:**
- [ ] All P3 features complete and tested
- [ ] Upgrade path from v0.3.x works
- [ ] Automation rules tested extensively
- [ ] Documentation updated
- [ ] v0.4.0 released

---

# P4 - Enterprise Features

> **Goal**: Enterprise-grade security, scalability, and compliance.
>
> **Timeline**: 8-10 weeks after P3
>
> **Milestone**: v1.0.0 release (Enterprise-ready)

---

## P4.0 - P4 Infrastructure

> **Priority**: Required before P4 features
>
> **Depends On**: P3 Complete
>
> **Estimated Effort**: 1 week

### P4.0.1 - Enterprise Infrastructure

| Task | Description | Patterns |
|------|-------------|----------|
| Kubernetes manifests | K8s deployment | — |
| Helm chart | Helm deployment | — |
| Database HA | Read replicas, failover | **Proxy** |
| Redis cluster | Clustered cache | **Flyweight** |
| Horizontal scaling | Multi-pod deployment | — |

---

## P4.1 - Enterprise Authentication

> **Priority**: HIGH
>
> **Depends On**: P0.2 (Auth)
>
> **Estimated Effort**: 2 weeks

### P4.1.1 - SSO (Standalone)

| Task | Description | Patterns |
|------|-------------|----------|
| SAML 2.0 | SAML integration | **Adapter**, **Strategy** |
| OIDC | OpenID Connect | **Adapter**, **Strategy** |
| Multiple IdPs | Multi-provider support | **Abstract Factory** |

### P4.1.2 - Directory Integration

| Task | Description | Patterns |
|------|-------------|----------|
| LDAP | LDAP authentication | **Adapter** |
| Active Directory | AD integration | **Adapter** |
| Group sync | Directory group sync | **Observer** |

### P4.1.3 - Security Enhancements

| Task | Description | Patterns |
|------|-------------|----------|
| Two-factor auth | TOTP-based 2FA | **Decorator** |
| 2FA enforcement | Require 2FA | **Decorator** |
| Session limits | Concurrent sessions | **Strategy** |
| IP whitelisting | IP-based access | **Chain of Responsibility** |
| Password policies | Complexity rules | **Chain of Responsibility** |

**Deliverables for P4.1:**
- [ ] SAML/OIDC SSO works
- [ ] LDAP/AD integration works
- [ ] 2FA works
- [ ] 80%+ test coverage

---

## P4.2 - Keycloak Integration (Optional IAM Mode)

> **Priority**: HIGH
>
> **Depends On**: P4.1
>
> **Estimated Effort**: 2 weeks

### P4.2.0 - Keycloak Theme Integration

| Task | Description | Patterns |
|------|-------------|----------|
| Keycloak theme export | Export Catppuccin theme for Keycloak | **Adapter** |
| Login theme | Keycloak login pages match Groundwork theme | **Template Method** |
| Account theme | Keycloak account console theming | **Template Method** |
| Theme sync | Pass theme preference to Keycloak | **Strategy** |

### P4.2.1 - Keycloak OIDC

| Task | Description | Patterns |
|------|-------------|----------|
| OIDC client setup | Register with Keycloak | **Adapter** |
| Login redirect | Keycloak login flow | **Strategy** |
| Token validation | Validate KC tokens | **Chain of Responsibility** |
| Logout integration | SSO logout | **Command** |

### P4.2.2 - User Synchronization

| Task | Description | Patterns |
|------|-------------|----------|
| JIT provisioning | Create on first login | **Factory Method** |
| Attribute mapping | Map KC attributes | **Adapter** |
| Group sync | Sync KC groups | **Observer** |
| Role mapping | Map KC roles | **Adapter** |

### P4.2.3 - Keycloak Authorization

| Task | Description | Patterns |
|------|-------------|----------|
| Resource registration | Register resources | **Adapter** |
| Policy evaluation | KC policy checks | **Chain of Responsibility** |
| Fine-grained permissions | KC-based permissions | **Proxy**, **Decorator** |

**Deliverables for P4.2:**
- [ ] Keycloak login works
- [ ] User sync works
- [ ] KC-based authorization works
- [ ] 80%+ test coverage

---

## P4.3 - Audit & Compliance

> **Priority**: HIGH
>
> **Depends On**: P0.5 (Activity)
>
> **Estimated Effort**: 1.5 weeks

### P4.3.1 - Audit Logging

| Task | Description | Patterns |
|------|-------------|----------|
| Comprehensive audit | Log all actions | **Observer**, **Decorator** |
| Audit search | Search/filter logs | **Strategy** |
| Audit export | Export audit data | **Strategy** |
| Audit retention | Retention policies | **Strategy** |

### P4.3.2 - Compliance

| Task | Description | Patterns |
|------|-------------|----------|
| GDPR tools | Data export, deletion | **Command**, **Visitor** |
| Access reports | Who accessed what | **Visitor** |
| Consent management | Track consent | **State** |

**Deliverables for P4.3:**
- [ ] Comprehensive audit logging works
- [ ] GDPR tools work
- [ ] 80%+ test coverage

---

## P4.4 - Multi-Tenancy

> **Priority**: MEDIUM
>
> **Depends On**: P0.3 (Projects)
>
> **Estimated Effort**: 1.5 weeks

### P4.4.1 - Organizations

| Task | Description | Patterns |
|------|-------------|----------|
| Organization model | Multi-workspace | **Factory Method** |
| Org settings | Org-level config | **Strategy** |
| Org admin | Org admin role | **Strategy** |

### P4.4.2 - Tenant Isolation

| Task | Description | Patterns |
|------|-------------|----------|
| Data isolation | Complete separation | **Strategy** |
| Schema isolation | Optional schema per tenant | **Abstract Factory** |
| Tenant switching | Switch between orgs | **Strategy** |

**Deliverables for P4.4:**
- [ ] Organizations work
- [ ] Data isolation works
- [ ] 80%+ test coverage

---

## P4.5 - Advanced Permissions

> **Priority**: MEDIUM
>
> **Depends On**: P1.6 (Permissions)
>
> **Estimated Effort**: 1 week

### P4.5.1 - Permission Schemes

| Task | Description | Patterns |
|------|-------------|----------|
| Global schemes | Org-wide schemes | **Strategy** |
| Scheme inheritance | Inherit from parent | **Prototype**, **Composite** |

### P4.5.2 - Fine-Grained Access

| Task | Description | Patterns |
|------|-------------|----------|
| Field-level security | Hide fields by role | **Decorator**, **Proxy** |
| Issue-level security | Restrict visibility | **Proxy** |

**Deliverables for P4.5:**
- [ ] Permission schemes work
- [ ] Field-level security works
- [ ] 80%+ test coverage

---

## P4.6 - White Labeling

> **Priority**: LOW
>
> **Depends On**: P0.1 (Infrastructure, Theming)
>
> **Estimated Effort**: 1 week

### P4.6.1 - Branding

| Task | Description | Patterns |
|------|-------------|----------|
| Custom logo | Replace logo | **Strategy** |
| Custom colors | Brand color overrides (extends Catppuccin) | **Strategy** |
| Custom theme | Create org-specific theme variant | **Strategy** |
| Login customization | Custom login page | **Template Method** |
| Favicon | Custom favicon per org | **Strategy** |

### P4.6.2 - Custom Domain

| Task | Description | Patterns |
|------|-------------|----------|
| Custom domains | Per-org domains | **Strategy** |
| SSL management | Auto SSL | **Command** |

### P4.6.3 - Theme Restrictions

| Task | Description | Patterns |
|------|-------------|----------|
| Restrict themes | Limit available themes per org | **Strategy** |
| Force theme | Enforce specific theme for org | **Strategy** |
| Custom palette | Allow custom Catppuccin overrides | **Strategy** |

**Deliverables for P4.6:**
- [ ] White labeling works
- [ ] Custom domains work
- [ ] Custom themes extend Catppuccin properly
- [ ] 80%+ test coverage

---

## P4.7 - Portfolio Management

> **Priority**: LOW
>
> **Depends On**: P2.7 (Hierarchy)
>
> **Estimated Effort**: 1 week

### P4.7.1 - Initiatives

| Task | Description | Patterns |
|------|-------------|----------|
| Initiative model | Group projects | **Composite** |
| Initiative progress | Roll-up progress | **Composite**, **Visitor** |
| Initiative roadmap | Cross-project view | **Builder** |

### P4.7.2 - Resource Management

| Task | Description | Patterns |
|------|-------------|----------|
| Capacity planning | Team capacity | **Strategy** |
| Resource allocation | Allocate to projects | **Strategy** |
| Utilization reports | Resource metrics | **Visitor** |

**Deliverables for P4.7:**
- [ ] Initiatives work
- [ ] Resource management works
- [ ] 80%+ test coverage

---

## P4.8 - Advanced API

> **Priority**: LOW
>
> **Depends On**: P0.8 (API)
>
> **Estimated Effort**: 1 week

### P4.8.1 - API Extensions

| Task | Description | Patterns |
|------|-------------|----------|
| GraphQL API | GraphQL endpoint | **Facade** |
| API rate limiting | Per-user/org limits | **Decorator** |
| API analytics | Usage tracking | **Observer** |

### P4.8.2 - OAuth Provider

| Task | Description | Patterns |
|------|-------------|----------|
| OAuth2 provider | Third-party apps | **Strategy** |
| App registration | OAuth app management | **Factory Method** |

**Deliverables for P4.8:**
- [ ] GraphQL works
- [ ] OAuth provider works
- [ ] 80%+ test coverage

---

## P4.9 - Platform Administration

> **Priority**: MEDIUM
>
> **Depends On**: P4.0 (Infrastructure)
>
> **Estimated Effort**: 1 week

### P4.9.1 - System Admin

| Task | Description | Patterns |
|------|-------------|----------|
| System settings | Global configuration | **Singleton** |
| System health | Health monitoring | **Observer** |
| Maintenance mode | Enable maintenance | **State** |

### P4.9.2 - Support Tools

| Task | Description | Patterns |
|------|-------------|----------|
| Impersonation | Admin impersonate | **Proxy** |
| Debug logging | Enhanced logging | **Decorator** |
| Support bundles | Diagnostic data | **Builder** |

**Deliverables for P4.9:**
- [ ] System admin tools work
- [ ] Support tools work
- [ ] 80%+ test coverage

---

## P4.10 - P4 Deployment & Release

> **Priority**: CRITICAL
>
> **Depends On**: P4.1-P4.9
>
> **Estimated Effort**: 1 week

### P4.10.1 - Enterprise Deployment

| Task | Description |
|------|-------------|
| Kubernetes tested | Full K8s deployment tested |
| Helm chart published | Helm chart available |
| HA documentation | High availability guide |
| Security hardening | Security best practices guide |

### P4.10.2 - Release Tasks

| Task | Description |
|------|-------------|
| Integration testing | Full P4 integration tests |
| Security audit | Professional security audit |
| Performance testing | Enterprise load testing |
| Migration testing | Test upgrade from P3 |
| Documentation | Complete enterprise docs |
| Changelog | P4 changelog |
| Release | v1.0.0 tag and publish |

**v1.0.0 Release Checklist:**
- [ ] All P4 features complete and tested
- [ ] Security audit passed
- [ ] Enterprise deployment tested
- [ ] Full documentation complete
- [ ] Upgrade paths tested
- [ ] v1.0.0 released (Enterprise-ready)

---

## Appendix: Design Pattern Reference

### Creational Patterns

| Pattern | Intent | Common Usage |
|---------|--------|--------------|
| **Factory Method** | Define interface for creating objects, let subclasses decide | Issue types, Notifications, Reports |
| **Abstract Factory** | Create families of related objects | Auth providers, Storage backends |
| **Builder** | Construct complex objects step-by-step | Queries, Reports, Workflows |
| **Prototype** | Create objects by cloning | Templates, Configuration cloning |
| **Singleton** | Single instance with global access | Config, Connection pools |

### Structural Patterns

| Pattern | Intent | Common Usage |
|---------|--------|--------------|
| **Adapter** | Convert interface to expected interface | External integrations, IdP adapters |
| **Bridge** | Decouple abstraction from implementation | Storage, Notifications |
| **Composite** | Tree structures for part-whole hierarchies | Issue hierarchy, UI components |
| **Decorator** | Add responsibilities dynamically | Permissions, Caching, Logging |
| **Facade** | Unified interface to subsystem | Service layer, API integrations |
| **Flyweight** | Share common state efficiently | Labels, Statuses, Icons |
| **Proxy** | Placeholder for another object | Lazy loading, Caching, Access control |

### Behavioral Patterns

| Pattern | Intent | Common Usage |
|---------|--------|--------------|
| **Chain of Responsibility** | Pass request along handler chain | Validation, Permissions, Webhooks |
| **Command** | Encapsulate request as object | CRUD operations, Bulk ops, Undo |
| **Interpreter** | Define grammar and interpret | LQL queries, Smart commits |
| **Iterator** | Sequential access without exposing structure | Pagination, Streams |
| **Mediator** | Encapsulate object interaction | Event bus, Timer coordination |
| **Memento** | Capture and restore state | History, Drafts, Undo |
| **Observer** | Notify dependents of changes | Notifications, Webhooks, Events |
| **State** | Alter behavior based on internal state | Issue status, Sprints, Workflows |
| **Strategy** | Interchangeable algorithms | Sorting, Filtering, Auth methods |
| **Template Method** | Define algorithm skeleton | Reports, Emails, Exports |
| **Visitor** | Operations on elements without changing them | Analytics, Roll-ups, Export |

---

## Summary

| Phase | Duration | Milestone | Focus |
|-------|----------|-----------|-------|
| **P0** | 8-12 weeks | v0.1.0 (MVP) | Infrastructure, Auth, Projects, Issues, Views |
| **P1** | 6-8 weeks | v0.2.0 | Sprints, Backlog, Time Tracking, Workflows |
| **P2** | 6-8 weeks | v0.3.0 | Reports, Integrations, Advanced Views |
| **P3** | 6-8 weeks | v0.4.0 | Automation, LQL, SCM, Templates |
| **P4** | 8-10 weeks | v1.0.0 | Enterprise: SSO, Keycloak, Audit, Multi-tenancy |

**Total estimated timeline**: 34-46 weeks to v1.0.0

**Parallel Development Guidelines:**
- P0 must be sequential (foundational)
- P1 features can be parallelized after P1.0 infrastructure
- P2/P3/P4 features within each phase can largely be parallelized
- Always maintain test coverage and CI/CD integrity

---

*Document Version: 5.0*
*License: GPL 3.0*
*Last Updated: January 2026*
