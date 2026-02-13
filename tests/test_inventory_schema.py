from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from data import MODALITIES, InventoryValidationError, load_inventory, validate_inventory


def test_inventory_schema_is_valid() -> None:
    frame = load_inventory(Path("data/platforms.csv"))

    required = {"name", "year", *MODALITIES, "availability", "reference"}
    assert required.issubset(set(frame.columns))
    assert pd.api.types.is_integer_dtype(frame["year"])

    for modality in MODALITIES:
        assert set(frame[modality].unique()) <= {0, 1}

    assert set(frame["availability"].unique()) <= {"oss", "proprietary", "mixed"}
    assert not frame["name"].duplicated().any()


def test_invalid_modality_value_raises() -> None:
    frame = pd.DataFrame(
        {
            "name": ["Example"],
            "year": [2024],
            "text": [2],
            "image": [1],
            "audio": [0],
            "tabular": [1],
            "availability": ["oss"],
            "reference": ["ref"],
        }
    )

    with pytest.raises(InventoryValidationError):
        validate_inventory(frame)


def test_invalid_year_raises() -> None:
    frame = pd.DataFrame(
        {
            "name": ["FuturePlatform"],
            "year": [9999],
            "text": [1],
            "image": [1],
            "audio": [0],
            "tabular": [0],
            "availability": ["oss"],
            "reference": ["ref"],
        }
    )

    with pytest.raises(InventoryValidationError):
        validate_inventory(frame)
