from __future__ import annotations

import warnings
from pathlib import Path

import pandas as pd

MODALITIES = ["text", "image", "audio", "tabular"]
REQUIRED_COLUMNS = [
    "name",
    "year",
    *MODALITIES,
    "availability",
    "reference",
]
ALLOWED_AVAILABILITY = {"oss", "proprietary", "mixed"}
YEAR_MIN = 1950
YEAR_MAX = 2100


class InventoryValidationError(ValueError):
    """Raised when the platforms inventory is malformed."""


def load_inventory(path: str | Path) -> pd.DataFrame:
    inventory_path = Path(path)
    if not inventory_path.exists():
        raise FileNotFoundError(f"Inventory file does not exist: {inventory_path}")

    if inventory_path.suffix.lower() == ".csv":
        frame = pd.read_csv(inventory_path)
    elif inventory_path.suffix.lower() == ".json":
        frame = pd.read_json(inventory_path)
    else:
        raise InventoryValidationError(
            f"Unsupported inventory format: {inventory_path.suffix}. Use .csv or .json."
        )

    return validate_inventory(frame, source=inventory_path)


def validate_inventory(frame: pd.DataFrame, *, source: str | Path = "inventory") -> pd.DataFrame:
    missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        raise InventoryValidationError(
            f"Missing required columns in {source}: {', '.join(missing)}"
        )

    data = frame.copy()

    for column in ["name", "availability", "reference"]:
        data[column] = data[column].fillna("").astype(str).str.strip()

    if (data["name"] == "").any():
        raise InventoryValidationError("Column 'name' must not contain empty values.")

    try:
        data["year"] = pd.to_numeric(data["year"], errors="raise").astype(int)
    except (TypeError, ValueError) as error:
        raise InventoryValidationError("Column 'year' must contain integer values.") from error

    invalid_years = data[(data["year"] < YEAR_MIN) | (data["year"] > YEAR_MAX)]
    if not invalid_years.empty:
        names = ", ".join(invalid_years["name"].tolist()[:5])
        raise InventoryValidationError(
            f"Column 'year' must be within [{YEAR_MIN}, {YEAR_MAX}]. Invalid entries: {names}"
        )

    for modality in MODALITIES:
        data[modality] = _normalize_binary_column(data[modality], modality)

    no_modalities = data[data[MODALITIES].sum(axis=1) == 0]
    if not no_modalities.empty:
        examples = ", ".join(no_modalities["name"].tolist()[:5])
        warnings.warn(
            f"Found entries with no enabled modalities: {examples}",
            RuntimeWarning,
            stacklevel=1,
        )

    data["availability"] = data["availability"].str.lower()
    invalid_availability = sorted(set(data["availability"]) - ALLOWED_AVAILABILITY)
    if invalid_availability:
        values = ", ".join(invalid_availability)
        raise InventoryValidationError(
            f"Column 'availability' has invalid values: {values}. "
            f"Allowed values: {', '.join(sorted(ALLOWED_AVAILABILITY))}."
        )

    duplicate_names = data[data.duplicated(subset=["name"], keep=False)]["name"].unique().tolist()
    if duplicate_names:
        raise InventoryValidationError(
            "Duplicate platform names detected: " + ", ".join(sorted(duplicate_names))
        )

    data = data.sort_values(by=["year", "name"], kind="mergesort").reset_index(drop=True)
    return data


def _normalize_binary_column(series: pd.Series, column: str) -> pd.Series:
    normalized: list[int] = []
    for index, value in series.items():
        try:
            normalized.append(_to_binary(value))
        except InventoryValidationError as error:
            raise InventoryValidationError(
                f"Column '{column}' contains invalid value at row {index + 2}: {value!r}. "
                "Expected binary values (0/1, true/false, yes/no, x/-)."
            ) from error

    return pd.Series(normalized, index=series.index, dtype=int)


def _to_binary(value: object) -> int:
    if isinstance(value, bool):
        return int(value)

    if isinstance(value, (int, float)) and not pd.isna(value):
        integer = int(value)
        if float(value) == float(integer) and integer in (0, 1):
            return integer

    if isinstance(value, str):
        token = value.strip().lower()
        mapping = {
            "1": 1,
            "0": 0,
            "x": 1,
            "-": 0,
            "true": 1,
            "false": 0,
            "yes": 1,
            "no": 0,
        }
        if token in mapping:
            return mapping[token]

    raise InventoryValidationError(f"Invalid binary value: {value!r}")
