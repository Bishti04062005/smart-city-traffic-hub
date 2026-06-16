import numpy as np
import pandas as pd
import holidays
import gradio as gr
import matplotlib.pyplot as plt
from datetime import datetime
from xgboost import XGBRegressor

# 1. Load pre-saved dataset and model assets
history_df = pd.read_csv("traffic_history.csv")
history_df["DateTime"] = pd.to_datetime(history_df["DateTime"])
junction_values = sorted(history_df["Junction"].unique().tolist())

model = XGBRegressor()
model.load_model("xgb_traffic_model.json")

india_holidays = holidays.India()

feature_cols = [
    "Junction", "year", "month", "day", "hour", "dayofweek", "weekofyear",
    "is_weekend", "is_holiday", "morning_peak", "evening_peak", "night",
    "hour_sin", "hour_cos", "dow_sin", "dow_cos",
    "lag_1", "lag_2", "lag_3", "lag_24", "lag_168",
    "rolling_mean_3", "rolling_mean_6", "rolling_mean_24"
]

# 2. Pipeline Core Functions
def traffic_label(pred):
    if pred < 100: return "Low"
    elif pred < 300: return "Medium"
    elif pred < 500: return "High"
    return "Severe"

def traffic_color(pred):
    if pred < 100: return "#15803d"
    elif pred < 300: return "#ca8a04"
    elif pred < 500: return "#ea580c"
    return "#dc2626"

def build_feature_row(junction, dt_obj, holiday_override):
    junction_df = history_df[history_df["Junction"] == junction].sort_values("DateTime")
    past = junction_df[junction_df["DateTime"] < dt_obj]

    if len(past) == 0:
        return None

    dayofweek = dt_obj.weekday()
    hour = dt_obj.hour

    row = pd.DataFrame([{
        "Junction": junction,
        "year": dt_obj.year,
        "month": dt_obj.month,
        "day": dt_obj.day,
        "hour": hour,
        "dayofweek": dayofweek,
        "weekofyear": int(dt_obj.isocalendar().week),
        "is_weekend": int(dayofweek >= 5),
        "is_holiday": int(holiday_override),
        "morning_peak": int(7 <= hour <= 10),
        "evening_peak": int(16 <= hour <= 19),
        "night": int(0 <= hour <= 5),
        "hour_sin": np.sin(2 * np.pi * hour / 24),
        "hour_cos": np.cos(2 * np.pi * hour / 24),
        "dow_sin": np.sin(2 * np.pi * dayofweek / 7),
        "dow_cos": np.cos(2 * np.pi * dayofweek / 7),
        "lag_1": past["Vehicles"].iloc[-1] if len(past) >= 1 else past["Vehicles"].median(),
        "lag_2": past["Vehicles"].iloc[-2] if len(past) >= 2 else past["Vehicles"].median(),
        "lag_3": past["Vehicles"].iloc[-3] if len(past) >= 3 else past["Vehicles"].median(),
        "lag_24": past["Vehicles"].iloc[-24] if len(past) >= 24 else past["Vehicles"].median(),
        "lag_168": past["Vehicles"].iloc[-168] if len(past) >= 168 else past["Vehicles"].median(),
        "rolling_mean_3": past["Vehicles"].tail(3).mean(),
        "rolling_mean_6": past["Vehicles"].tail(6).mean(),
        "rolling_mean_24": past["Vehicles"].tail(24).mean()
    }])

    return row[feature_cols]

def make_plot(junction):
    temp = history_df[history_df["Junction"] == junction].sort_values("DateTime").tail(200)
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(temp["DateTime"], temp["Vehicles"], color="teal", linewidth=2)
    ax.set_title(f"Traffic History for Junction {junction}")
    ax.set_xlabel("DateTime")
    ax.set_ylabel("Vehicles")
    plt.xticks(rotation=45)
    plt.tight_layout()
    return fig

def predict(junction, date_str, hour, is_holiday):
    try:
        dt_obj = pd.to_datetime(f"{date_str} {int(hour):02d}:00:00")
    except:
        return "<h3 style='color:red;'>Invalid date format</h3>", pd.DataFrame(), None

    feature_row = build_feature_row(junction, dt_obj, is_holiday)
    if feature_row is None:
        return "<h3 style='color:red;'>No past data available for that input</h3>", pd.DataFrame(), None

    pred = float(np.maximum(model.predict(feature_row)[0], 0))
    label = traffic_label(pred)
    color = traffic_color(pred)

    card = f"""
    <div style="padding:20px;border-radius:16px;background:{color};color:white;">
      <h2>Predicted Traffic: {pred:.2f}</h2>
      <h3>Status: {label}</h3>
      <p>Junction: {junction}</p>
      <p>Forecast time: {dt_obj}</p>
    </div>
    """

    summary = pd.DataFrame({
        "Metric": ["Predicted Vehicles", "Traffic Level", "Holiday"],
        "Value": [round(pred, 2), label, "Yes" if is_holiday else "No"]
    })

    fig = make_plot(junction)
    return card, summary, fig

# 3. Gradio Interface Definition
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("# Smart City Traffic Forecasting Dashboard")

    with gr.Row():
        junction_input = gr.Dropdown(junction_values, value=junction_values[0], label="Junction")
        date_input = gr.Textbox(value="2017-07-01", label="Date (YYYY-MM-DD)")
        hour_input = gr.Slider(0, 23, value=8, step=1, label="Hour")
        holiday_input = gr.Checkbox(label="Holiday")

    predict_btn = gr.Button("Predict Traffic")

    output_card = gr.HTML()
    output_table = gr.Dataframe()
    output_plot = gr.Plot()

    predict_btn.click(
        fn=predict,
        inputs=[junction_input, date_input, hour_input, holiday_input],
        outputs=[output_card, output_table, output_plot]
    )

# Standard launch for deployment environments
demo.launch()