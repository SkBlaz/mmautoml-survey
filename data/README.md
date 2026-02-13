# Inventory Data

## File

- `platforms.csv` is the canonical inventory used for all generated figures.

## Required schema

- `name`: platform/framework/product name.
- `year`: integer year of first public availability.
- `text`, `image`, `audio`, `tabular`: binary modality indicators (`0`/`1`).
- `availability`: one of `oss`, `proprietary`, `mixed`.
- `reference`: URL, DOI, citation key, or bibliographic pointer.

Optional metadata columns currently included:

- `type`
- `notes`
- `version`
- `date_first_release` (`YYYY-MM` when known)

## Curation policy

- `year` is defined as the first public release/availability year.
- When multiple releases exist in the same year, ties are left as-is and downstream code applies deterministic sort by `year`, then `name`.
- Missing modality evidence should be encoded as `0` unless explicit support is documented.
- `mixed` availability should be used when a platform combines open and closed components in normal usage.

## Licensing note

This dataset is a curated factual inventory assembled from public references. Check each linked source for product-specific licensing terms.
