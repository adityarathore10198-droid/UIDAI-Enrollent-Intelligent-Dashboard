# ============================================================
# UIDAI Enrollment Intelligence Dashboard
# ============================================================

import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output
from statsmodels.tsa.arima.model import ARIMA

# ------------------------------------------------------------
# 1. LOAD DATA
# ------------------------------------------------------------

df = pd.read_csv("processed_data/master_uidai_table.csv")
df['date'] = pd.to_datetime(df['date'])

# ---------------- SAFE METRICS ----------------
df['total_enrolments'] = df['total_enrolments'].replace(0, 1)

df['child_ratio'] = df.get('age_0_5', 0) / df['total_enrolments']

update_cols = [c for c in df.columns if c.startswith('demo_') or c.startswith('bio_')]
df['update_burden'] = df[update_cols].sum(axis=1) if update_cols else 0

df['policy_alert'] = df['update_burden'] > (0.5 * df['total_enrolments'])

# ------------------------------------------------------------
# 2. KPI VALUES
# ------------------------------------------------------------

TOTAL_ENROLMENTS = int(df['total_enrolments'].sum())
TOTAL_UPDATES = int(df['update_burden'].sum())
ALERT_DISTRICTS = int(df['policy_alert'].sum())
STATES_COUNT = df['state'].nunique()

# ------------------------------------------------------------
# 3. FORECAST (ALL INDIA)
# ------------------------------------------------------------

ts = df.groupby('date')['total_enrolments'].sum().sort_index()

model = ARIMA(ts, order=(1, 1, 1))
forecast = model.fit().forecast(steps=30)

forecast_df = forecast.reset_index()
forecast_df.columns = ['date', 'forecast_enrolments']

# ------------------------------------------------------------
# 4. DASH APP SETUP
# ------------------------------------------------------------

external_stylesheets = [
    "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap"
]

app = Dash(
    __name__,
    external_stylesheets=external_stylesheets,
    suppress_callback_exceptions=True
)

app.title = "UIDAI Enrollment Intelligence Dashboard"

# ------------------------------------------------------------
# 5. UI COMPONENTS
# ------------------------------------------------------------

def kpi_card(title, value):
    return html.Div(
        [
            html.Div(title, style={'fontSize': '13px', 'color': '#6c757d'}),
            html.Div(value, style={'fontSize': '28px', 'fontWeight': '700'})
        ],
        style={
            'padding': '16px',
            'borderRadius': '12px',
            'backgroundColor': '#f8f9fa',
            'boxShadow': '0 2px 6px rgba(0,0,0,0.05)',
            'width': '23%',
            'textAlign': 'center'
        }
    )

# ------------------------------------------------------------
# 6. LAYOUT
# ------------------------------------------------------------

app.layout = html.Div(
    style={
        'fontFamily': 'Inter, sans-serif',
        'padding': '24px',
        'backgroundColor': '#ffffff'
    },
    children=[

        html.H1(
            "UIDAI Enrollment Intelligence Dashboard",
            style={'textAlign': 'center', 'fontWeight': '700'}
        ),

        html.P(
            "Decision-support analytics for Aadhaar enrollment, updates, and policy planning",
            style={'textAlign': 'center', 'color': '#6c757d'}
        ),

        html.Hr(),

        # -------- FILTER --------
        html.Div(
            [
                html.Label("Select State"),
                dcc.Dropdown(
                    options=[{'label': s, 'value': s} for s in sorted(df['state'].unique())],
                    placeholder="All India",
                    id='state_filter',
                    clearable=True
                )
            ],
            style={'width': '30%', 'margin': 'auto'}
        ),

        html.Br(),

        # -------- KPI ROW --------
        html.Div(
            [
                kpi_card("Total Enrolments", f"{TOTAL_ENROLMENTS:,}"),
                kpi_card("Total Updates", f"{TOTAL_UPDATES:,}"),
                kpi_card("Policy Alert Districts", f"{ALERT_DISTRICTS:,}"),
                kpi_card("States Covered", f"{STATES_COUNT}")
            ],
            style={
                'display': 'flex',
                'justifyContent': 'space-between',
                'marginBottom': '32px'
            }
        ),

        # -------- CHARTS --------
        dcc.Graph(id='enrollment_trend'),
        dcc.Graph(id='forecast_chart'),
        dcc.Graph(id='update_scatter'),

        html.Hr(),

        html.P(
            "Source: UIDAI Aggregated Enrollment, Demographic & Biometric Data",
            style={'textAlign': 'center', 'fontSize': '12px', 'color': '#6c757d'}
        )
    ]
)

# ------------------------------------------------------------
# 7. CALLBACKS
# ------------------------------------------------------------

@app.callback(
    Output('enrollment_trend', 'figure'),
    Output('forecast_chart', 'figure'),
    Output('update_scatter', 'figure'),
    Input('state_filter', 'value')
)
def update_dashboard(selected_state):

    data = df if not selected_state else df[df['state'] == selected_state]

    # -------- Enrollment Trend --------
    ts_actual = data.groupby('date')['total_enrolments'].sum().reset_index()
    fig_ts = px.line(
        ts_actual,
        x='date',
        y='total_enrolments',
        title="Aadhaar Enrolment Trend"
    )
    fig_ts.update_layout(template="plotly_white")

    # -------- Forecast --------
    fig_forecast = px.line(
        forecast_df,
        x='date',
        y='forecast_enrolments',
        title="30-Day Aadhaar Enrolment Forecast"
    )
    fig_forecast.update_layout(template="plotly_white")

    # -------- Update Burden & Policy Alerts --------
    fig_scatter = px.scatter(
        data,
        x='total_enrolments',
        y='update_burden',
        size='update_burden',
        color='policy_alert',
        color_discrete_map={
            True: '#d62728',
            False: '#1f77b4'
        },
        hover_data=['state', 'district'],
        title="Enrollment vs Update Burden (Policy Alerts Highlighted)"
    )
    fig_scatter.update_layout(
        template="plotly_white",
        legend_title="Policy Alert"
    )

    return fig_ts, fig_forecast, fig_scatter

# ------------------------------------------------------------
# 8. RUN APP
# ------------------------------------------------------------

if __name__ == "__main__":
    print("Starting UIDAI Enrollment Intelligence Dashboard...")
    app.run(debug=True)
