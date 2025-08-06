.PHONY: help list migrate


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

##--------------------------------------------------------
## Project setup
##--------------------------------------------------------

requirements: ## Instalar dependencias
	pip install -r requirements.txt

run: ## Ejecutar proyecto
	flet run src/main.py

web: ## Iniciar servidor web
	flet run ./src/main.py --web

init_db: ## Inicializar base de datos
	PYTHONPATH=src python src/scripts/init_db.py create_db

reset_db: ## Eliminar y volver a crear todas las tablas (pierdes datos)
	PYTHONPATH=src python src/scripts/init_db.py reset_db

update_schema: ## Actualizar esquema de la base de datos
	PYTHONPATH=src python src/scripts/init_db.py update_schema


##--------------------------------------------------------
## Utilidades genéricas
##--------------------------------------------------------

list: ## Listar todos los archivos del proyecto
	@find . -maxdepth 2 -print

