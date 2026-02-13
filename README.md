# Multimodal AutoML Survey Assets

This repository contains the figure-generation pipeline and curated platform inventory for a multimodal AutoML survey.

## Layout

- `data/platforms.csv`: curated inventory used for plots.
- `data/README.md`: schema and curation policy.
- `src/data.py`: inventory loader + schema validation.
- `src/plots.py`: deterministic plotting pipeline.
- `outputs/`: generated plots and run trace artifacts.

## Reproduce Figures

Prerequisites:

- Python `>=3.9`
- `uv` installed: <https://docs.astral.sh/uv/>

Commands:

```bash
uv sync --locked --dev
make plots
ls outputs
```

Primary outputs:

- `outputs/jointplot.pdf`
- `outputs/dendrogram.pdf`
- `outputs/inventory_used.csv`
- `outputs/modality_matrix.csv`
- `outputs/linkage.csv`
- `outputs/run_metadata.txt`

## CLI

```bash
uv run python src/plots.py \
  --input data/platforms.csv \
  --outdir outputs \
  --format pdf,png \
  --seed 0
```

Flags:

- `--no-tex`: disable LaTeX rendering.
- `--format`: comma-separated formats (`pdf`, `png`).

## Troubleshooting

- If LaTeX is unavailable, run with `--no-tex` or `make plots NO_TEX=1`.
- If TeX rendering fails at runtime, the script automatically falls back to non-TeX text rendering.
- If fonts differ across operating systems, compare the CSV/metadata artifacts (`inventory_used.csv`, `run_metadata.txt`) to verify identical inputs and settings.
