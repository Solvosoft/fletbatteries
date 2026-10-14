# FletBatteries

FletBatteries is a set of framework-like tools designed to simplify 
the development of applications with Flet. This project provides a 
user-friendly and highly customizable environment, ideal for developers 
looking to create applications efficiently and quickly

---

## 📋 Table of Contents

1. [Features](#-features)
2. [Requirements](#-requirements)
3. [Installation](#-installation)
4. [Usage](#-usage)
5. [Project Structure](#-project-structure)
6. [Useful Links](#-useful-links)

---

## 🚀 Features

* App shell: routing with parameters, login and permission guards, menu with badges, breadcrumbs, theme and per-session language.
* Declarative forms and model forms (30 field types), fieldsets as tabs/sections/collapsible panels and multi-step wizards.
* Widgets inspired by django-gentelella-widgets: selects with search, masks, dates, files, color, Markdown, maps, calendar, charts.
* Server-side `DataTable` and `CRUDView`: search, filters, bulk actions, CSV export and import, clone, undo delete.
* Auth: users, groups and permissions, login lockout, session expiry, password change and reset by email code.
* FastAPI integration: `crud_router` with token authentication and per-endpoint permissions.
* Contrib apps: settings (with admin UI), notifications, help, history (audit log), trash (soft delete), email.
* Database migrations with Alembic through the `fletbatteries` CLI.

---

## 🛠️ Requirements

* [uv](https://docs.astral.sh/uv/) (installs Python 3.13 automatically if needed)
* Flet 1.0.4 (installed by `make setup`)
* Chromium (optional, only for `make screenshots`; if it is not installed system-wide, `make setup` downloads it with Playwright)

---

## ⚙️ Installation

1. Clone this repository:

   ```bash
   git clone https://github.com/Solvosoft/fletbatteries.git
   cd fletbatteries
   ```

2. First-time setup (recreates `.venv`, installs dependencies, creates the database tables):

   ```bash
   make setup
   ```

   Use `make sync` afterwards to update `.venv` after pulling changes.
   For pip users, `requirements.txt` is generated from `uv.lock` with `make requirements`.

---

## 📦 Usage

| Command | Description |
|---|---|
| `make run` | Desktop app |
| `make web` | App in the browser (`PORT=8550`) |
| `make api` | FastAPI server used by the *Autocomplete* views (`API_PORT=8000`) |
| `make init_db` / `make update_schema` / `make reset_db` | Database management |
| `make makemigrations MSG="..."` / `make migrate` | Create / apply Alembic migrations (`fletbatteries` CLI) |
| `make help` | All targets |

Configuration (environment variables or a `.env` file at the repo root):

| Variable | Default | Description |
|---|---|---|
| `FLETBATTERIES_DB_URL` | `sqlite:///<repo>/template.db` | SQLAlchemy database URL |
| `FLETBATTERIES_API_URL` | `http://127.0.0.1:8000` | API used by the autocomplete views |
| `FLETBATTERIES_SKIP_LOGIN` | unset | If `1`, opening `/` does not redirect to `/login` |

---

## 🧪 Testing

```bash
make test                          # headless pytest suite (no display, no Flutter SDK)
make test PYTEST_ARGS="-k calendar"
make screenshots                   # PNG per route in screenshots/ + report.json
make screenshots ROUTES="/calendar /charts"
make lint
```

* `make test` runs the real app (`src/main.py`) against Flet's own `Session` in-process
  (`tests/harness.py`): it navigates routes, clicks buttons, fills fields and asserts on the
  control tree, the database and the API. It uses a temporary SQLite database.
* `make screenshots` starts the app in web mode plus the API (with a copy of `template.db`), opens each
  route in headless Chromium and saves `screenshots/<route>.png`. The exit code is non-zero
  if a route is blank, redirects unexpectedly, logs browser errors or the server logs a traceback.

See [AGENTS.md](AGENTS.md) for the workflow intended for coding agents.

---

## 📂 Project Structure

```text
fletbatteries/
├── .venv/                   # Virtual environment (uv)
├── src/                     # Main source code
│   ├── main.py              # App entry point (main(page))
│   ├── settings.py          # Paths and configuration (env vars / .env)
│   ├── assets/              # Static assets (served at the web root)
│   │   ├── image/           # Images used in the app
│   │   ├── fonts/           # Fonts used in the app
│   │   ├── animations/      # Rive animations
│   │   ├── icons/friconix/  # Friconix icons
│   │   └── fontawesome/     # Icons used in the app
│   ├── components/          # Reusable components
│   │   ├── layout/          # General layout and design
│   │   └── shared/          # Shared components (forms, datatable, calendar, color picker...)
│   ├── controls/            # Control logic and validation
│   │   ├── handler/         # Logic for view handling
│   │   └── router/          # Custom routing logic
│   ├── data/                # Data handling
│   │   ├── models/          # SQLAlchemy models
│   │   └── manager/         # CRUD operations
│   ├── views/               # Visual logic and UI views
│   └── scripts/             # DB management and FastAPI app
├── tests/                   # pytest suite + in-process Flet harness
├── tools/screenshots.py     # Visual review tool
├── Makefile                 # Automation tasks
├── pyproject.toml / uv.lock # Dependencies
└── requirements.txt         # Generated from uv.lock (pip users)
```

---

## 🔗 Useful Links

* **Flet (documentation)**: [https://flet.dev/docs/](https://flet.dev/docs/)
