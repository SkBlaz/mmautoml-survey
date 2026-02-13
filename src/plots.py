from __future__ import annotations

import argparse
import random
import shutil
import subprocess
import sys
import warnings
from datetime import datetime, timezone
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.patches import Rectangle
from scipy.cluster.hierarchy import dendrogram, linkage

from data import MODALITIES, load_inventory

MODAL_COLORS = {
    "text": "#4C78A8",
    "image": "#F58518",
    "audio": "#54A24B",
    "tabular": "#E45756",
}
SUPPORTED_FORMATS = {"pdf", "png"}
CLUSTER_METHOD = "ward"
CLUSTER_METRIC = "euclidean"


def configure_plot_style(use_tex: bool) -> None:
    plt.rcParams.update(
        {
            "text.usetex": use_tex,
            "font.family": "sans-serif",
            "font.size": 18,
            "font.sans-serif": "Helvetica",
        }
    )
    sns.set_style("whitegrid")
    sns.set_context("paper", font_scale=1.3)


def generate_jointplot(data: pd.DataFrame, output_path: Path) -> None:
    subframe = data[["name", "year"]].sort_values(by=["year", "name"], kind="mergesort")
    plot = sns.jointplot(
        x=subframe["year"],
        y=subframe["name"],
        marker="+",
        s=800,
        color="black",
        height=8.27,
    )
    plot.ax_marg_y.set_visible(False)
    plot.ax_joint.set_ylabel("")
    plot.ax_joint.set_xlabel("Year")
    plot.figure.tight_layout()
    plot.figure.savefig(output_path, dpi=300)
    plt.close(plot.figure)


def generate_dendrogram(
    data: pd.DataFrame,
    matrix: np.ndarray,
    linkage_matrix: np.ndarray,
    output_path: Path,
    *,
    legend_title: str | None,
    highlight_open_source: bool,
) -> None:
    labels = data["name"].tolist()

    fig, ax = plt.subplots(figsize=(11, 13))
    dendro = dendrogram(
        linkage_matrix,
        labels=labels,
        orientation="left",
        ax=ax,
        leaf_font_size=16,
        link_color_func=lambda _: "black",
    )

    gutter = 0.44
    left, right = ax.get_xlim()
    ax.set_xlim(left, right - gutter)

    for line in ax.get_lines():
        line.set_linewidth(2.2)
        line.set_color("black")

    availability = dict(zip(data["name"], data["availability"]))
    for tick in ax.get_yticklabels():
        tick.set_color("black")
        if highlight_open_source and availability[tick.get_text()] == "oss":
            tick.set_bbox(
                {
                    "boxstyle": "round,pad=0.15",
                    "facecolor": "gray",
                    "alpha": 0.1,
                    "edgecolor": "none",
                }
            )

    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xticks([])
    ax.set_xlabel("")
    ax.grid(False)

    leaf_order = dendro["leaves"]
    y_ticks = ax.get_yticks()
    chip_height = 2.6
    x_start = -0.10
    x_step = -0.11

    for plot_idx, row_idx in enumerate(leaf_order):
        y_value = y_ticks[plot_idx]
        binary_row = matrix[row_idx]
        for modality_index, present in enumerate(binary_row):
            if present:
                ax.add_patch(
                    Rectangle(
                        (x_start + modality_index * x_step, y_value - chip_height / 2),
                        width=0.095,
                        height=chip_height,
                        color=MODAL_COLORS[MODALITIES[modality_index]],
                        transform=ax.transData,
                        clip_on=False,
                    )
                )

    handles = [Rectangle((0, 0), 1, 1, color=MODAL_COLORS[key]) for key in MODALITIES]
    legend_kwargs = {
        "fontsize": 18,
        "loc": "upper left",
        "bbox_to_anchor": (0.02, 1.03),
        "frameon": False,
    }
    if legend_title:
        legend_kwargs["title"] = legend_title
    ax.legend(handles, MODALITIES, **legend_kwargs)

    fig.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)


def compute_linkage_matrix(data: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    matrix = data[MODALITIES].astype(int).to_numpy()
    linkage_matrix = linkage(
        matrix,
        method=CLUSTER_METHOD,
        metric=CLUSTER_METRIC,
        optimal_ordering=True,
    )
    return matrix, linkage_matrix


def parse_formats(value: str) -> list[str]:
    formats = [token.strip().lower() for token in value.split(",") if token.strip()]
    if not formats:
        raise ValueError("At least one output format is required.")

    unsupported = sorted(set(formats) - SUPPORTED_FORMATS)
    if unsupported:
        supported = ", ".join(sorted(SUPPORTED_FORMATS))
        invalid = ", ".join(unsupported)
        raise ValueError(f"Unsupported output formats: {invalid}. Supported formats: {supported}.")

    return formats


def write_run_metadata(
    output_dir: Path,
    *,
    input_path: Path,
    data: pd.DataFrame,
    formats: list[str],
    seed: int,
    use_tex: bool,
) -> None:
    modality_counts = {modality: int(data[modality].sum()) for modality in MODALITIES}
    availability_counts = data["availability"].value_counts().sort_index().to_dict()

    metadata_lines = [
        f"timestamp_utc={datetime.now(timezone.utc).isoformat()}",
        f"git_commit={resolve_git_commit()}",
        f"python_version={sys.version.split()[0]}",
        f"inventory_source={input_path.as_posix()}",
        f"inventory_rows={len(data)}",
        f"output_formats={','.join(formats)}",
        f"seed={seed}",
        f"tex_enabled={use_tex}",
        f"cluster_method={CLUSTER_METHOD}",
        f"cluster_metric={CLUSTER_METRIC}",
        "cluster_optimal_ordering=True",
    ]

    for modality, count in modality_counts.items():
        metadata_lines.append(f"count_{modality}={count}")
    for availability, count in availability_counts.items():
        metadata_lines.append(f"count_availability_{availability}={count}")

    (output_dir / "run_metadata.txt").write_text("\n".join(metadata_lines) + "\n")


def resolve_git_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"

    return result.stdout.strip() or "unknown"


def run_all(
    *,
    input_path: Path,
    output_dir: Path,
    use_tex: bool,
    formats: list[str],
    seed: int,
) -> None:
    random.seed(seed)
    np.random.seed(seed)

    output_dir.mkdir(parents=True, exist_ok=True)
    configure_plot_style(use_tex=use_tex)
    data = load_inventory(input_path)

    # Cleanup legacy output names to keep one canonical dendrogram artifact.
    for legacy_name in ("dendrogram_moda.pdf", "dendrogram_modalities.pdf"):
        (output_dir / legacy_name).unlink(missing_ok=True)

    data.to_csv(output_dir / "inventory_used.csv", index=False)

    matrix, linkage_matrix = compute_linkage_matrix(data)
    pd.DataFrame(matrix, columns=MODALITIES, index=data["name"]).to_csv(
        output_dir / "modality_matrix.csv",
        index_label="name",
    )
    pd.DataFrame(
        linkage_matrix,
        columns=["cluster_a", "cluster_b", "distance", "sample_count"],
    ).to_csv(output_dir / "linkage.csv", index=False)

    for fmt in formats:
        generate_jointplot(data, output_dir / f"jointplot.{fmt}")
        generate_dendrogram(
            data,
            matrix,
            linkage_matrix,
            output_dir / f"dendrogram.{fmt}",
            legend_title="Modalities",
            highlight_open_source=True,
        )

    write_run_metadata(
        output_dir,
        input_path=input_path,
        data=data,
        formats=formats,
        seed=seed,
        use_tex=use_tex,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate survey plots.")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/platforms.csv"),
        help="Path to the platforms inventory (.csv or .json).",
    )
    parser.add_argument(
        "--outdir",
        "--output-dir",
        dest="outdir",
        type=Path,
        default=Path("outputs"),
        help="Directory where outputs are written.",
    )
    parser.add_argument(
        "--format",
        default="pdf",
        help="Comma-separated output formats (supported: pdf,png).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Deterministic seed value recorded in metadata.",
    )
    parser.add_argument(
        "--no-tex",
        action="store_true",
        help="Disable LaTeX text rendering in matplotlib.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    formats = parse_formats(args.format)
    latex_found = shutil.which("latex") is not None
    use_tex = not args.no_tex and latex_found

    if not latex_found and not args.no_tex:
        warnings.warn(
            "LaTeX was not found on PATH. Falling back to text.usetex=False.",
            RuntimeWarning,
            stacklevel=1,
        )

    if not use_tex:
        run_all(
            input_path=args.input,
            output_dir=args.outdir,
            use_tex=False,
            formats=formats,
            seed=args.seed,
        )
        return

    try:
        run_all(
            input_path=args.input,
            output_dir=args.outdir,
            use_tex=True,
            formats=formats,
            seed=args.seed,
        )
    except RuntimeError as error:
        if "latex was not able to process" not in str(error):
            raise
        warnings.warn(
            "LaTeX rendering failed. Retrying with text.usetex=False.",
            RuntimeWarning,
            stacklevel=1,
        )
        run_all(
            input_path=args.input,
            output_dir=args.outdir,
            use_tex=False,
            formats=formats,
            seed=args.seed,
        )


if __name__ == "__main__":
    main()
