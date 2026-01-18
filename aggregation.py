# ============================================================
# aggregation.py
# Scalable aggregation + data cleaning for UIDAI datasets
# ============================================================

import pandas as pd
from pathlib import Path
import re
import unicodedata

# ------------------------------------------------------------
# 1. TEXT NORMALIZATION UTILITIES
# ------------------------------------------------------------

def normalize_text(series: pd.Series) -> pd.Series:
    """
    Normalize text by:
    - removing hidden unicode characters
    - lowercasing
    - removing punctuation
    - collapsing multiple spaces
    """
    return (
        series
        .astype(str)
        .apply(lambda x: unicodedata.normalize("NFKD", x))
        .str.lower()
        .str.replace(r"[^\w\s]", " ", regex=True)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )

# ------------------------------------------------------------
# 2. CANONICAL STATE MASTER (INDIA)
# ------------------------------------------------------------

STATE_MASTER = {
    # States
    "andhra pradesh": "Andhra Pradesh",
    "arunachal pradesh": "Arunachal Pradesh",
    "assam": "Assam",
    "bihar": "Bihar",
    "chhattisgarh": "Chhattisgarh",
    "goa": "Goa",
    "gujarat": "Gujarat",
    "haryana": "Haryana",
    "himachal pradesh": "Himachal Pradesh",
    "jharkhand": "Jharkhand",
    "karnataka": "Karnataka",
    "kerala": "Kerala",
    "madhya pradesh": "Madhya Pradesh",
    "maharashtra": "Maharashtra",
    "manipur": "Manipur",
    "meghalaya": "Meghalaya",
    "mizoram": "Mizoram",
    "nagaland": "Nagaland",
    "odisha": "Odisha",
    "punjab": "Punjab",
    "rajasthan": "Rajasthan",
    "sikkim": "Sikkim",
    "tamil nadu": "Tamil Nadu",
    "telangana": "Telangana",
    "tripura": "Tripura",
    "uttar pradesh": "Uttar Pradesh",
    "uttarakhand": "Uttarakhand",
    "west bengal": "West Bengal",

    # Union Territories
    "andaman and nicobar islands": "Andaman and Nicobar Islands",
    "chandigarh": "Chandigarh",
    "dadra and nagar haveli and daman and diu":
        "Dadra and Nagar Haveli and Daman and Diu",
    "delhi": "Delhi",
    "jammu and kashmir": "Jammu and Kashmir",
    "ladakh": "Ladakh",
    "lakshadweep": "Lakshadweep",
    "puducherry": "Puducherry",
}

# ------------------------------------------------------------
# 3. MAIN AGGREGATION FUNCTION
# ------------------------------------------------------------

def aggregate_folder(
    folder_path: str,
    group_cols: list,
    sum_cols: list,
    chunksize: int = 200_000
) -> pd.DataFrame:
    """
    Reads large CSV files in chunks, cleans data, normalizes
    state/district names, and aggregates numerics.

    Parameters
    ----------
    folder_path : str
        Path to folder containing CSV shards
    group_cols : list
        Columns to group by (e.g. date, state, district)
    sum_cols : list
        Numeric columns to sum
    chunksize : int
        Chunk size for large file processing
    """

    aggregated_chunks = []

    for file in Path(folder_path).glob("*.csv"):
        print(f"Processing: {file.name}")

        for chunk in pd.read_csv(file, chunksize=chunksize):

            # -----------------------------
            # DATE CLEANING (MIXED FORMATS)
            # -----------------------------
            chunk['date'] = pd.to_datetime(
                chunk['date'],
                dayfirst=True,
                errors='coerce'
            )
            chunk = chunk.dropna(subset=['date'])

            # -----------------------------
            # STATE CLEANING (CANONICAL)
            # -----------------------------
            chunk['state'] = normalize_text(chunk['state'])
            chunk['state'] = chunk['state'].map(STATE_MASTER)
            chunk = chunk.dropna(subset=['state'])

            # -----------------------------
            # DISTRICT CLEANING
            # -----------------------------
            chunk['district'] = (
                normalize_text(chunk['district'])
                .str.title()
            )

            # -----------------------------
            # SAFE NUMERIC CONVERSION
            # -----------------------------
            for col in sum_cols:
                chunk[col] = pd.to_numeric(
                    chunk[col],
                    errors='coerce'
                ).fillna(0)

            # -----------------------------
            # AGGREGATION
            # -----------------------------
            agg = (
                chunk
                .groupby(group_cols, as_index=False)[sum_cols]
                .sum()
            )

            aggregated_chunks.append(agg)

    # -----------------------------
    # FINAL COMBINE
    # -----------------------------
    final_df = (
        pd.concat(aggregated_chunks, ignore_index=True)
        .groupby(group_cols, as_index=False)
        .sum()
    )

    return final_df

# ============================================================
# END OF FILE
# ============================================================
