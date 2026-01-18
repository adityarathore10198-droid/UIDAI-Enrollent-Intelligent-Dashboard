# ============================================================
# UIDAI ENROLLMENT INTELLIGENCE DASHBOARD (FINAL UX VERSION)
# ============================================================

import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output, State
from dash.dash_table import DataTable

# ============================================================
# 1. LOAD DATA (ONCE)
# ============================================================

df = pd.read_csv("processed_data/master_uidai_table.csv", parse_dates=["date"])

df["total_enrolments"] = df["total_enrolments"].clip(lower=1)

update_cols = [c for c in df.columns if c.startswith("demo_") or c.startswith("bio_")]
df["update_burden"] = df[update_cols].sum(axis=1)
df["policy_alert"] = df["update_burden"] > (0.5 * df["total_enrolments"])

# ============================================================
# 2. BASELINE (ALL INDIA – FIXED)
# ============================================================

BASE_TOTAL_ENROL = int(df["total_enrolments"].sum())
BASE_TOTAL_UPD = int(df["update_burden"].sum())
BASE_ALERTS = int(df["policy_alert"].sum())
BASE_STATES = df["state"].nunique()

# ============================================================
# 3. PRECOMPUTED AGGREGATES (FAST)
# ============================================================

national_ts = df.groupby("date", as_index=False)["total_enrolments"].sum()

district_rank = (
    df.groupby(["state", "district"])["total_enrolments"]
    .sum()
    .reset_index()
    .sort_values("total_enrolments", ascending=False)
)

forecast_df = pd.read_csv(
    "processed_data/30_day_enrolment_forecast.csv",
    parse_dates=["date"]
)

state_totals = df.groupby("state")["total_enrolments"].sum().sort_values(ascending=False)
alert_states = df[df["policy_alert"]].groupby("state").size().sort_values(ascending=False)

# ============================================================
# 4. DASH APP
# ============================================================

app = Dash(__name__)
app.title = "UIDAI Enrollment Intelligence Dashboard"

# ============================================================
# 5. UI HELPERS
# ============================================================

def kpi_card(title, id):
    return html.Div(
        [
            html.Div(title, style={"fontSize": "13px", "color": "#6c757d"}),
            html.Div(id=id, style={"fontSize": "26px", "fontWeight": "700"}),
        ],
        style={
            "padding": "14px",
            "borderRadius": "10px",
            "backgroundColor": "#f8f9fa",
            "textAlign": "center",
        },
    )

def delta(val):
    arrow = "🔺" if val > 0 else "🔻"
    return html.Small(f"{arrow} {abs(val):,}", style={"display": "block"})

# ============================================================
# 6. LAYOUT
# ============================================================

app.layout = html.Div(
    style={"maxWidth": "1350px", "margin": "auto", "padding": "20px"},
    children=[

        html.H1("UIDAI Enrollment Intelligence Dashboard", style={"textAlign": "center"}),
        html.P(
            "Fast, guided analytics for Aadhaar governance",
            style={"textAlign": "center", "color": "#6c757d"},
        ),

        dcc.Dropdown(
            options=[{"label": s, "value": s} for s in sorted(df["state"].unique())],
            placeholder="All India",
            id="state_filter",
            style={"width": "320px", "margin": "16px auto"},
        ),

        html.Div(
            [
                kpi_card("Total Enrolments (India)", "kpi_enrol"),
                kpi_card("Total Updates (India)", "kpi_upd"),
                kpi_card("Policy Alert Districts", "kpi_alert"),
                kpi_card("States Covered", "kpi_states"),
            ],
            style={
                "display": "grid",
                "gridTemplateColumns": "repeat(4, 1fr)",
                "gap": "16px",
                "marginBottom": "20px",
            },
        ),

        html.Div(id="context_bar", style={
            "padding": "12px",
            "backgroundColor": "#f1f3f5",
            "borderRadius": "8px",
            "marginBottom": "20px",
            "fontSize": "14px",
        }),

        dcc.RangeSlider(
            id="date_slider",
            min=0,
            max=len(national_ts) - 1,
            value=[0, len(national_ts) - 1],
            tooltip={"placement": "bottom"},
        ),

        html.H3("📈 Enrolment Trend"),
        html.P("Tracks temporal changes in Aadhaar enrolments",
               style={"fontSize": "13px", "color": "#6c757d"}),
        dcc.Loading(dcc.Graph(id="trend"), type="circle"),

        html.Div(id="auto_insight", style={
            "padding": "12px",
            "backgroundColor": "#eef6ff",
            "borderRadius": "8px",
            "marginBottom": "12px",
        }),

        html.Div(id="state_insight", style={
            "padding": "12px",
            "backgroundColor": "#f8f9fa",
            "borderLeft": "5px solid #0d6efd",
            "borderRadius": "6px",
            "marginBottom": "20px",
        }),

        html.H3("🔮 30-Day Forecast"),
        html.P("Short-term enrolment projection for planning",
               style={"fontSize": "13px", "color": "#6c757d"}),
        dcc.Loading(dcc.Graph(id="forecast"), type="circle"),

        html.H3("⚠️ Enrolment vs Update Burden"),
        html.P("Identifies districts with high update pressure",
               style={"fontSize": "13px", "color": "#6c757d"}),
        dcc.Loading(dcc.Graph(id="scatter"), type="circle"),

        html.Button(
            "⬇ Download State Report",
            id="download_btn",
            style={
                "backgroundColor": "#0d6efd",
                "color": "white",
                "border": "none",
                "padding": "10px 16px",
                "borderRadius": "6px",
                "marginBottom": "20px",
            },
        ),
        dcc.Download(id="download_csv"),

        html.H3("🏙️ Top Districts by Enrolment"),
        dcc.Loading(
            DataTable(
                id="district_table",
                page_size=10,
                style_header={"backgroundColor": "#f1f3f5", "fontWeight": "bold"},
                style_cell={"padding": "8px"},
            ),
            type="circle",
        ),

        html.Hr(),

        html.H3("💬 Ask UIDAI Data Assistant"),
        html.P(
            "Try asking: top states · policy alerts · enrolments in Bihar",
            style={"fontSize": "13px", "color": "#6c757d"},
        ),
        dcc.Textarea(id="chat_input", style={"width": "100%", "height": "70px"}),
        html.Button("Ask", id="ask_btn", style={"marginTop": "6px"}),
        html.Div(id="chat_output", style={"marginTop": "10px"}),
    ],
)

# ============================================================
# 7. KPI CALLBACK
# ============================================================

@app.callback(
    Output("kpi_enrol", "children"),
    Output("kpi_upd", "children"),
    Output("kpi_alert", "children"),
    Output("kpi_states", "children"),
    Output("context_bar", "children"),
    Input("state_filter", "value"),
)
def update_kpis(state):

    if not state:
        return (
            f"{BASE_TOTAL_ENROL:,}",
            f"{BASE_TOTAL_UPD:,}",
            BASE_ALERTS,
            BASE_STATES,
            "Showing national Aadhaar overview. Select a state to see its relative impact.",
        )

    data = df[df["state"] == state]

    return (
        html.Div([f"{BASE_TOTAL_ENROL:,}", delta(int(data["total_enrolments"].sum()) - BASE_TOTAL_ENROL)]),
        html.Div([f"{BASE_TOTAL_UPD:,}", delta(int(data["update_burden"].sum()) - BASE_TOTAL_UPD)]),
        html.Div([BASE_ALERTS, delta(int(data["policy_alert"].sum()) - BASE_ALERTS)]),
        BASE_STATES,
        f"Showing Aadhaar analytics for {state}. KPIs show national totals with state-level deltas.",
    )

# ============================================================
# 8. MAIN DASHBOARD CALLBACK
# ============================================================

@app.callback(
    Output("trend", "figure"),
    Output("forecast", "figure"),
    Output("scatter", "figure"),
    Output("auto_insight", "children"),
    Output("state_insight", "children"),
    Output("district_table", "data"),
    Output("district_table", "columns"),
    Input("state_filter", "value"),
    Input("date_slider", "value"),
)
def update_dashboard(state, dr):

    data = df if not state else df[df["state"] == state]

    ts = (
        data.groupby("date", as_index=False)["total_enrolments"]
        .sum()
        .iloc[dr[0]: dr[1]]
    )

    fig_ts = px.line(ts, x="date", y="total_enrolments", markers=True)
    fig_ts.update_layout(transition_duration=400, hovermode="x unified", height=320)

    fig_fc = px.line(forecast_df, x="date", y="forecast_enrolments")
    fig_fc.update_traces(line=dict(dash="dot", color="orange"))
    fig_fc.update_layout(height=260)

    fig_sc = px.scatter(
        data,
        x="total_enrolments",
        y="update_burden",
        color="policy_alert",
        hover_data=["state", "district"],
    )
    fig_sc.update_layout(height=320)

    auto = f"📌 Average daily enrolments: {int(ts['total_enrolments'].mean()):,}. Peak: {int(ts['total_enrolments'].max()):,}."

    if state:
        sd = data
        state_insight = html.Div([
            html.H5(f"📍 {state} – Key Insights"),
            html.Ul([
                html.Li(f"Avg daily enrolments: {int(sd['total_enrolments'].mean()):,}"),
                html.Li(f"Update burden ratio: {(sd['update_burden'].sum()/sd['total_enrolments'].sum())*100:.1f}%"),
                html.Li(f"Policy alert districts: {int(sd['policy_alert'].sum())}"),
                html.Li(f"National contribution: {(sd['total_enrolments'].sum()/BASE_TOTAL_ENROL)*100:.2f}%"),
            ])
        ])
    else:
        state_insight = "Select a state to view localized insights."

    table = district_rank if not state else district_rank[district_rank["state"] == state]
    table = table.head(10)

    return (
        fig_ts,
        fig_fc,
        fig_sc,
        auto,
        state_insight,
        table.to_dict("records"),
        [{"name": c, "id": c} for c in table.columns],
    )

# ============================================================
# 9. DOWNLOAD CALLBACK
# ============================================================

@app.callback(
    Output("download_csv", "data"),
    Input("download_btn", "n_clicks"),
    State("state_filter", "value"),
    prevent_initial_call=True,
)
def download_report(_, state):
    d = df if not state else df[df["state"] == state]
    return dcc.send_data_frame(d.to_csv, "uidai_report.csv", index=False)

# ============================================================
# 10. CHATBOT CALLBACK
# ============================================================

@app.callback(
    Output("chat_output", "children"),
    Input("ask_btn", "n_clicks"),
    State("chat_input", "value"),
)
def chatbot(_, q):

    if not q:
        return "Ask about top states, alerts, or a state name."

    q = q.lower()

    if "top" in q:
        return html.Ul([html.Li(f"{k}: {v:,}") for k, v in state_totals.head(5).items()])

    if "alert" in q:
        return alert_states.to_string()

    for s in state_totals.index:
        if s.lower() in q:
            return f"Total enrolments in {s}: {int(state_totals[s]):,}"

    return "Try: top states · alerts · enrolments in Bihar"

# ============================================================
# 11. RUN
# ============================================================

if __name__ == "__main__":
    app.run(debug=False)
