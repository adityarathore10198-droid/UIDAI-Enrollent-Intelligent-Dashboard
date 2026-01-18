# ============================================================
# 01_eda.py
# Exploratory Data Analysis for UIDAI Master Dataset
# ============================================================

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# ------------------------------------------------------------
# 1. CONFIGURATION
# ------------------------------------------------------------

DATA_PATH = "processed_data/master_uidai_table.csv"
OUTPUT_DIR = "outputs/eda"

Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

plt.style.use("seaborn-v0_8")

# ------------------------------------------------------------
# 2. LOAD DATA
# ------------------------------------------------------------

df = pd.read_csv(DATA_PATH)
df["date"] = pd.to_datetime(df["date"])

print("✅ Data Loaded Successfully")
print("Shape:", df.shape)
print("Date Range:", df["date"].min(), "to", df["date"].max())
print("States:", df["state"].nunique())
print("Districts:", df["district"].nunique())

# ------------------------------------------------------------
# 3. NATIONAL ENROLMENT TREND
# ------------------------------------------------------------

national_ts = (
    df.groupby("date")["total_enrolments"]
    .sum()
    .reset_index()
)

plt.figure(figsize=(12, 5))
plt.plot(national_ts["date"], national_ts["total_enrolments"])
plt.title("National Aadhaar Enrolment Trend")
plt.xlabel("Date")
plt.ylabel("Total Enrolments")
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/national_enrolment_trend.png")
plt.close()

print("📈 Saved national enrolment trend")

# ------------------------------------------------------------
# 4. TOP STATES BY ENROLMENT
# ------------------------------------------------------------

top_states = (
    df.groupby("state")["total_enrolments"]
    .sum()
    .sort_values(ascending=False)
    .head(10)
)

plt.figure(figsize=(8, 5))
top_states.plot(kind="barh")
plt.gca().invert_yaxis()
plt.title("Top 10 States by Aadhaar Enrolment")
plt.xlabel("Total Enrolments")
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/top_states_enrolment.png")
plt.close()

print("🏙️ Saved top states enrolment plot")

# ------------------------------------------------------------
# 5. AGE-WISE ENROLMENT DISTRIBUTION
# ------------------------------------------------------------

age_dist = df[["age_0_5", "age_5_17", "age_18_greater"]].sum()

plt.figure(figsize=(6, 6))
age_dist.plot(
    kind="pie",
    autopct="%1.1f%%",
    title="Age-wise Aadhaar Enrolment Distribution"
)
plt.ylabel("")
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/age_wise_distribution.png")
plt.close()

print("👶 Saved age-wise distribution plot")

# ------------------------------------------------------------
# 6. ENROLMENT VS UPDATE BURDEN
# ------------------------------------------------------------

plt.figure(figsize=(8, 5))
plt.scatter(
    df["total_enrolments"],
    df["update_burden"],
    alpha=0.4
)
plt.xlabel("Total Enrolments")
plt.ylabel("Update Burden")
plt.title("Enrolment vs Update Burden")
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/enrolment_vs_update_burden.png")
plt.close()

print("⚠️ Saved enrolment vs update burden plot")

# ------------------------------------------------------------
# 7. POLICY ALERT DISTRIBUTION
# ------------------------------------------------------------

alert_counts = df["policy_alert"].value_counts()

plt.figure(figsize=(6, 4))
alert_counts.plot(kind="bar", color=["green", "red"])
plt.title("Policy Alert Distribution")
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/policy_alert_distribution.png")
plt.close()

print("🚨 Saved policy alert distribution plot")

# ------------------------------------------------------------
# 8. TOP HIGH-RISK DISTRICTS
# ------------------------------------------------------------

high_risk = (
    df[df["policy_alert"]]
    .groupby(["state", "district"])["update_burden"]
    .sum()
    .sort_values(ascending=False)
    .head(10)
)

high_risk.to_csv(f"{OUTPUT_DIR}/top_high_risk_districts.csv")

print("📄 Saved top high-risk districts table")

# ------------------------------------------------------------
# 9. CHILD ENROLMENT RATIO DISTRIBUTION
# ------------------------------------------------------------

plt.figure(figsize=(8, 5))
plt.hist(df["child_ratio"], bins=30)
plt.title("Distribution of Child Enrolment Ratio")
plt.xlabel("Child Ratio (0–5 / Total)")
plt.ylabel("Number of District Records")
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/child_enrolment_ratio.png")
plt.close()

print("📊 Saved child enrolment ratio distribution")

# ------------------------------------------------------------
# 10. FINAL SUMMARY
# ------------------------------------------------------------

print("\n🔍 EDA COMPLETED SUCCESSFULLY")
print("Key Outputs saved to:", OUTPUT_DIR)
