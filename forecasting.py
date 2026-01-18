# ============================================================
# forecasting.py
# 30-day Aadhaar Enrolment Forecast (ARIMA)
# ============================================================

import pandas as pd
from statsmodels.tsa.arima.model import ARIMA

# ------------------------------------------------------------
# 1. LOAD DATA
# ------------------------------------------------------------

df = pd.read_csv("processed_data/master_uidai_table.csv")
df["date"] = pd.to_datetime(df["date"])

# ------------------------------------------------------------
# 2. BUILD TIME SERIES (ALL INDIA)
# ------------------------------------------------------------

ts = (
    df.groupby("date")["total_enrolments"]
    .sum()
    .sort_index()
)

# Ensure continuous daily frequency
ts = ts.asfreq("D", fill_value=0)

# ------------------------------------------------------------
# 3. TRAIN ARIMA MODEL
# ------------------------------------------------------------

model = ARIMA(
    ts,
    order=(1, 1, 1),
    enforce_stationarity=False,
    enforce_invertibility=False
)

model_fit = model.fit()

# ------------------------------------------------------------
# 4. GENERATE 30-DAY FORECAST
# ------------------------------------------------------------

forecast_steps = 30
forecast_values = model_fit.forecast(steps=forecast_steps)

forecast_df = forecast_values.reset_index()
forecast_df.columns = ["date", "forecast_enrolments"]

# ------------------------------------------------------------
# 5. SAVE OUTPUT
# ------------------------------------------------------------

forecast_df.to_csv(
    "processed_data/30_day_enrolment_forecast.csv",
    index=False
)

print("✅ 30-day enrolment forecast saved to processed_data/")
