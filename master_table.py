# ============================================================
# master_table.py
# Build unified UIDAI master analytics table
# ============================================================

import pandas as pd
from pathlib import Path

from aggregation import aggregate_folder

# ------------------------------------------------------------
# 1. PATH CONFIGURATION
# ------------------------------------------------------------

RAW_DATA_DIR = "Datasets"
OUTPUT_DIR = "processed_data"

ENROLMENT_DIR = f"{RAW_DATA_DIR}/aadhar_enrolment"
DEMOGRAPHIC_DIR = f"{RAW_DATA_DIR}/aadhar_demographic"
BIOMETRIC_DIR = f"{RAW_DATA_DIR}/aadhar_biometric"

Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------
# 2. AGGREGATE EACH DATASET
# ------------------------------------------------------------

print("🚀 Aggregating UIDAI datasets...")

# ================= ENROLMENT =================
print("➡️ Processing Aadhaar Enrolment data")

enrolment_df = aggregate_folder(
    folder_path=ENROLMENT_DIR,
    group_cols=["date", "state", "district"],
    sum_cols=["age_0_5", "age_5_17", "age_18_greater"]
)

# Total enrolments
enrolment_df["total_enrolments"] = (
    enrolment_df["age_0_5"]
    + enrolment_df["age_5_17"]
    + enrolment_df["age_18_greater"]
)

# ================= DEMOGRAPHIC UPDATES =================
print("➡️ Processing Demographic Update data")

demographic_df = aggregate_folder(
    folder_path=DEMOGRAPHIC_DIR,
    group_cols=["date", "state", "district"],
    sum_cols=["demo_age_5_17", "demo_age_17_"]
)

# Rename for clarity
demographic_df.rename(
    columns={
        "demo_age_5_17": "demo_5_17",
        "demo_age_17_": "demo_18_plus",
    },
    inplace=True,
)

# ================= BIOMETRIC UPDATES =================
print("➡️ Processing Biometric Update data")

biometric_df = aggregate_folder(
    folder_path=BIOMETRIC_DIR,
    group_cols=["date", "state", "district"],
    sum_cols=["bio_age_5_17", "bio_age_17_"]
)

# Rename for clarity
biometric_df.rename(
    columns={
        "bio_age_5_17": "bio_5_17",
        "bio_age_17_": "bio_18_plus",
    },
    inplace=True,
)

# ------------------------------------------------------------
# 3. MERGE INTO MASTER TABLE
# ------------------------------------------------------------

print("🔗 Merging datasets into master table")

master_df = (
    enrolment_df
    .merge(demographic_df, on=["date", "state", "district"], how="left")
    .merge(biometric_df, on=["date", "state", "district"], how="left")
)

master_df.fillna(0, inplace=True)

# ------------------------------------------------------------
# 4. DERIVED ANALYTICS FEATURES
# ------------------------------------------------------------

print("🧠 Creating derived metrics")

# Prevent divide-by-zero
master_df["total_enrolments"] = master_df["total_enrolments"].replace(0, 1)

# Update burden index
update_cols = [
    "demo_5_17",
    "demo_18_plus",
    "bio_5_17",
    "bio_18_plus",
]

master_df["update_burden"] = master_df[update_cols].sum(axis=1)

# Child enrolment ratio
master_df["child_ratio"] = master_df["age_0_5"] / master_df["total_enrolments"]

# Policy alert flag (configurable threshold)
master_df["policy_alert"] = (
    master_df["update_burden"] > (0.5 * master_df["total_enrolments"])
)

# ------------------------------------------------------------
# 5. FINAL SANITY CHECKS
# ------------------------------------------------------------

print("📊 Master table summary")
print("Rows:", master_df.shape[0])
print("Columns:", master_df.shape[1])
print("States:", master_df["state"].nunique())
print("Date range:", master_df["date"].min(), "to", master_df["date"].max())

# ------------------------------------------------------------
# 6. SAVE OUTPUT
# ------------------------------------------------------------

output_path = f"{OUTPUT_DIR}/master_uidai_table.csv"
master_df.to_csv(output_path, index=False)

print(f"✅ Master UIDAI table saved to {output_path}")
print("🏁 Master table generation completed successfully")
