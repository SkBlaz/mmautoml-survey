from __future__ import annotations

from pathlib import Path

from plots import run_all


def test_plot_pipeline_smoke(tmp_path: Path) -> None:
    input_path = Path("tests/data/toy_platforms.csv")
    output_dir = tmp_path / "outputs"

    run_all(
        input_path=input_path,
        output_dir=output_dir,
        use_tex=False,
        formats=["pdf"],
        seed=7,
    )

    expected = [
        "jointplot.pdf",
        "dendrogram.pdf",
        "inventory_used.csv",
        "modality_matrix.csv",
        "linkage.csv",
        "run_metadata.txt",
    ]
    for name in expected:
        assert (output_dir / name).exists(), f"Expected output missing: {name}"
