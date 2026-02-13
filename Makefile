.PHONY: ensure-venv plots test lint zip-contents functionalities functionalitites

INPUT ?= data/platforms.csv
OUTDIR ?= outputs
FORMATS ?= pdf
SEED ?= 0
ZIP_DIR ?= functionalitites
ZIP_NAME ?= mmautoml-survey.zip
ZIP_PATH := $(ZIP_DIR)/$(ZIP_NAME)
ZIP_CONTENTS := README.md Makefile pyproject.toml uv.lock LICENSE CITATION.cff data src docs tests .github/workflows

PLOT_ARGS := --input $(INPUT) --outdir $(OUTDIR) --format $(FORMATS) --seed $(SEED)
ifdef NO_TEX
PLOT_ARGS += --no-tex
endif

ensure-venv:
	@if [ ! -d .venv ]; then \
		echo "Creating .venv via uv sync --locked --dev"; \
		uv sync --locked --dev; \
	fi

plots: ensure-venv
	uv run python src/plots.py $(PLOT_ARGS)

test: ensure-venv
	uv run pytest -q

lint: ensure-venv
	uv run ruff check .

zip-contents:
	@mkdir -p $(ZIP_DIR)
	@rm -f $(ZIP_PATH)
	zip -r $(ZIP_PATH) $(ZIP_CONTENTS) \
		-x '.venv/*' \
		-x 'outputs/*' \
		-x '.pytest_cache/*' \
		-x '.ruff_cache/*' \
		-x '*/__pycache__/*' \
		-x '*.pyc'
	@echo "Created $(ZIP_PATH)"

functionalities: test zip-contents

functionalitites: functionalities
