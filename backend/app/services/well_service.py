from typing import List, Dict, Any


def parse_wells_excel(file_path: str) -> List[Dict[str, Any]]:
    """Parse Excel file with well data. Expects columns: name, lon, lat (or 经度/纬度/名称)."""
    import pandas as pd

    df = pd.read_excel(file_path, engine="openpyxl")
    df.columns = [str(c).strip().lower() for c in df.columns]
    # Handle duplicate column names after normalization
    seen = {}
    new_cols = []
    for col in df.columns:
        if col in seen:
            seen[col] += 1
            new_cols.append(f"{col}_{seen[col]}")
        else:
            seen[col] = 0
            new_cols.append(col)
    df.columns = new_cols

    col_map = {}
    for col in df.columns:
        if col in ("lon", "longitude", "经度", "x"):
            col_map["lon"] = col
        elif col in ("lat", "latitude", "纬度", "y"):
            col_map["lat"] = col
        elif col in ("name", "名称", "井名", "well_name", "矿井名称"):
            col_map["name"] = col

    missing = [k for k in ("lon", "lat", "name") if k not in col_map]
    if missing:
        raise ValueError(f"Excel file missing required columns: {missing}. Found columns: {list(df.columns)}")

    records = []
    for _, row in df.iterrows():
        try:
            lon = float(row[col_map["lon"]])
            lat = float(row[col_map["lat"]])
            name = str(row[col_map["name"]])
            extra = {c: row[c] for c in df.columns if c not in col_map.values()}
            records.append({"name": name, "lon": lon, "lat": lat, **extra})
        except (ValueError, TypeError):
            continue

    return records
