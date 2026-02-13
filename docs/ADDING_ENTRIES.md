# Adding Inventory Entries

1. Add a row to `data/platforms.csv`.
2. Fill required fields: `name`, `year`, modality flags, `availability`, `reference`.
3. Use modality flags as binary values (`0`/`1`).
4. Use `year` as first public availability year.
5. Use `availability=mixed` if both open and closed components are required for normal use.
6. Run validation and plots:

```bash
make test
make plots NO_TEX=1
```

If validation fails, `src/data.py` reports the exact column/row issue.
