# Atajos del workspace CV. En Windows usa `python scripts/cv.py <comando>`.
PYTHON ?= python3
CV := $(PYTHON) scripts/cv.py

.DEFAULT_GOAL := help
.PHONY: help bootstrap setup init new render check list status doctor skills clean-outputs

help: ## Muestra esta ayuda
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

bootstrap: ## Deja el workspace listo (NAME="Tu Nombre" crea main/cv.yaml)
	$(CV) bootstrap $(if $(NAME),--name "$(NAME)",)

setup: ## Crea .venv, instala RenderCV y enlaza skills
	$(CV) setup

init: ## Crea main/cv.yaml desde el ejemplo (NAME="Tu Nombre")
	$(CV) init $(if $(NAME),--name "$(NAME)",)

new: ## Crea postulación: make new COMPANY="X" ROLE="Y" [URL=...] [JOB_FILE=...]
	@test -n "$(COMPANY)" || (echo "Falta COMPANY" >&2; exit 2)
	@test -n "$(ROLE)" || (echo "Falta ROLE" >&2; exit 2)
	$(CV) new "$(COMPANY)" "$(ROLE)" \
		$(if $(URL),--url "$(URL)",) \
		$(if $(JOB_FILE),--job-file "$(JOB_FILE)",)

render: ## Renderiza: make render [APP=carpeta] (default: main)
	$(CV) render $(or $(APP),main)

check: ## Valida todos los cv.yaml
	$(CV) check

list: ## Lista postulaciones
	$(CV) list

status: ## Resumen del workspace
	$(CV) status

doctor: ## Diagnostica el entorno
	$(CV) doctor

skills: ## Enlaza .agents/skills a los directorios de agentes
	$(CV) sync-skills

clean-outputs: ## Borra salidas generadas (PDF/HTML/MD)
	rm -rf main/outputs
	find applications -mindepth 2 -maxdepth 2 -type d -name outputs -exec rm -rf {} +
