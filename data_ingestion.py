# ============================================================
# data_ingestion.py
# Unified data ingestion for UIDAI datasets
# ============================================================

import pandas as pd
from pathlib import Path

# ------------------------------------------------------------
# 1. CONFIGURATION
# ------------------------------------------------------------

RAW_DATA_DIR = "Datasets"
OUTPUT_DIR = "processed_data"

ENROLMENT_DIR = f"{RAW_DATA_DIR}/aadhar_enrolment"
DEMOGRAPHIC_DIR = f"{RAW_DATA_DIR}/aadhar_demographic"
BIOMETRIC_DIR = f"{RAW_DATA_DIR}/aadhar_biometric"

CHUNKSIZE = 200_000

# Ensure output directory exists
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------
# 2. GENERIC INGESTION FUNCTION
# ------------------------------------------------------------

def ingest_folder(folder_path: str, chunksize: int = CHUNKSIZE) -> pd.DataFrame:
    """
    Reads all CSV files from a folder in chunks and concatenates them
    into a single DataFrame.

    Parameters
    ----------
    folder_path : str
        Path to folder containing CSV files
    chunksize : int
        Number of rows per chunk

    Returns
    -------
    pd.DataFrame
        Concatenated DataFrame
    """

    frames = []

    for file in Path(folder_path).glob("*.csv"):
        print(f"Ingesting: {file.name}")

        for chunk in pd.read_csv(file, chunksize=chunksize):
            frames.append(chunk)

    if not frames:
        raise ValueError(f"No CSV files found in {folder_path}")

    return pd.concat(frames, ignore_index=True)

# ------------------------------------------------------------
# 3. INGEST UIDAI DATASETS
# ------------------------------------------------------------

def ingest_uidai_data():
    """
    Ingest enrolment, demographic, and biometric datasets
    """

    enrolment_df = ingest_folder(ENROLMENT_DIR)
    demographic_df = ingest_folder(DEMOGRAPHIC_DIR)
    biometric_df = ingest_folder(BIOMETRIC_DIR)

    return enrolment_df, demographic_df, biometric_df

# ------------------------------------------------------------
# 4. SAVE RAW INGESTED DATA
# ------------------------------------------------------------

def save_raw_outputs(enrolment_df, demographic_df, biometric_df):
    """
    Saves raw ingested datasets for auditing/debugging
    """

    enrolment_df.to_csv(
        f"{OUTPUT_DIR}/raw_enrolment.csv", index=False
    )
    demographic_df.to_csv(
        f"{OUTPUT_DIR}/raw_demographic.csv", index=False
    )
    biometric_df.to_csv(
        f"{OUTPUT_DIR}/raw_biometric.csv", index=False
    )

    print("✅ Raw UIDAI datasets saved successfully")

# ------------------------------------------------------------
# 5. MAIN EXECUTION
# ------------------------------------------------------------

if __name__ == "__main__":

    print("🚀 Starting UIDAI data ingestion...")

    enrolment_df, demographic_df, biometric_df = ingest_uidai_data()

    print("📊 Ingestion Summary")
    print("Enrolment:", enrolment_df.shape)
    print("Demographic:", demographic_df.shape)
    print("Biometric:", biometric_df.shape)

    save_raw_outputs(enrolment_df, demographic_df, biometric_df)

    print("✅ UIDAI data ingestion completed")

