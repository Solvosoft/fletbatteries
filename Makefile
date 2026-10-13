.PHONY: help setup sync run build-linux run-build web api init_db reset_db update_schema test screenshots lint doctor requirements clean list

UV ?= uv
PYTHON_VERSION ?= 3.13
PORT ?= 8550
API_PORT ?= 8000
ROUTES ?=
PYTEST_ARGS ?=
# Cliente de escritorio de Flet en Linux: light (sin Rive/mapas) o full (necesita libmpv2)
FLAVOR ?= light

RUN := $(UV) run
SRC_ENV := PYTHONPATH=demo

##--------------------------------------------------------
## Help
##--------------------------------------------------------
help: ## Mostrar esta ayuda
	@echo
	@echo "Usage: make [target]"
	@echo
	@echo "Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) \
		| sort \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
	@echo
	@echo "Variables: PORT=$(PORT) API_PORT=$(API_PORT) ROUTES=\"/calendar /charts\" PYTEST_ARGS=\"-k calendar\""
	@echo

##--------------------------------------------------------
## Project setup
##--------------------------------------------------------

setup: ## Configuración inicial: recrea .venv, instala dependencias, crea la BD y el navegador de capturas
	@command -v $(UV) >/dev/null || { echo "Se requiere uv: https://docs.astral.sh/uv/getting-started/installation/"; exit 1; }
	rm -rf .venv
	$(UV) sync --python $(PYTHON_VERSION)
	$(MAKE) init_db
	@if command -v chromium >/dev/null || command -v chromium-browser >/dev/null || command -v google-chrome >/dev/null; then \
		echo "Usando el Chromium del sistema para las capturas"; \
	else \
		$(RUN) playwright install chromium; \
	fi
	@$(RUN) python -c "import flet; print('Flet', flet.__version__, 'listo')"

sync: ## Sincronizar .venv con uv.lock
	$(UV) sync

run: ## Ejecutar la app de escritorio (FLAVOR=full para el cliente con Rive/mapas, requiere libmpv2)
	FLET_DESKTOP_FLAVOR=$(FLAVOR) $(RUN) flet run demo/main.py

build-linux: ## Compilar la app de escritorio para Linux (incluye Rive, charts y mapas; requiere clang)
	$(RUN) flet build linux --yes --no-rich-output

run-build: ## Ejecutar la app compilada con build-linux (usa template.db del repo)
	# GDK_GL=gles: GTK usa EGL; con GLX, rive_native no tiene EGLImage y no dibuja (o rompe el contexto GL)
	GDK_GL=gles FLETBATTERIES_DB_URL=sqlite:///$(CURDIR)/template.db ./build/linux/fletbatteries

web: ## Ejecutar la app en el navegador (PORT=8550)
	$(RUN) flet run --web --port $(PORT) demo/main.py

api: ## Iniciar la API (FastAPI) usada por las vistas de autocompletes (API_PORT=8000)
	$(RUN) uvicorn scripts.api:app --reload --app-dir demo --port $(API_PORT)

init_db: ## Crear las tablas que falten en la base de datos
	$(SRC_ENV) $(RUN) python demo/scripts/init_db.py create_db

reset_db: ## Eliminar y volver a crear todas las tablas (pierdes datos)
	$(SRC_ENV) $(RUN) python demo/scripts/init_db.py reset_db

update_schema: ## Actualizar esquema de la base de datos
	$(SRC_ENV) $(RUN) python demo/scripts/init_db.py update_schema

##--------------------------------------------------------
## Calidad
##--------------------------------------------------------

test: ## Pruebas automáticas headless (sin display ni Flutter)
	$(RUN) pytest $(PYTEST_ARGS)

screenshots: ## Capturas PNG de cada ruta en screenshots/ (ROUTES="/calendar /charts")
	$(RUN) python tools/screenshots.py $(ROUTES)

lint: ## Revisar errores con ruff
	$(RUN) ruff check src demo tests tools

doctor: ## Diagnóstico del entorno de Flet
	$(RUN) flet doctor

requirements: ## Regenerar requirements.txt (paquete + demo) desde uv.lock (para quien use pip)
	$(UV) export --no-dev --group demo --all-extras --no-hashes --no-emit-project --format requirements-txt -o requirements.txt

##--------------------------------------------------------
## Utilidades genéricas
##--------------------------------------------------------

clean: ## Borrar cachés y artefactos generados
	find . -path ./.venv -prune -o -type d -name __pycache__ -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache screenshots build

list: ## Listar todos los archivos del proyecto
	@find . -maxdepth 2 -not -path './.venv*' -not -path './.git*' -print
