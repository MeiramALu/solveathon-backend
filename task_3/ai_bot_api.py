import tensorflow as tf
from typing import Literal
from datetime import date, timedelta
from numpy import argmax
from sklearn.preprocessing import MinMaxScaler
from google import genai
from dotenv import dotenv_values

from model_training import get_data
from model_selection import BEST_LSTM_MODEL, BEST_BLSTM_MODEL


env = dotenv_values(".env")


def get_recent_data(days):
    start_date = (date.today() - timedelta(days=days)).strftime("%Y-%m-%d")
    end_date = date.today()

    df_usd = get_data("USD", start_date, end_date)
    df_kzt = get_data("KZT", start_date, end_date)
    df = df_usd.merge(df_kzt, on="Date", suffixes=("_usd", "_kzt"))
    data = (df["Rate_usd"] / df["Rate_kzt"]).to_numpy()

    return data


def get_forecast(days=7): # NOTE: The models are decent in predicting 7 days at most
    days += 4 # NOTE: Is's specific of the dataset API. It's latest data is 4 days behing

    data = get_recent_data(days).reshape(-1, 1)

    scaler = MinMaxScaler(feature_range=(0, 1))
    data_scaled = scaler.fit_transform(data)

    lstm = tf.keras.models.load_model(f"./models/lstm_{BEST_LSTM_MODEL}.keras")
    blstm = tf.keras.models.load_model(f"./models/blstm_{BEST_BLSTM_MODEL}.keras")

    lstm_pred = lstm.predict(data_scaled)
    blstm_pred = blstm.predict(data_scaled)

    forecast_scaled = (lstm_pred + blstm_pred) / 2
    forecast = scaler.inverse_transform(forecast_scaled) * 10

    return forecast.reshape(-1)

def what_to_do(forecast) -> Literal["sell", "wait"]:
    decision = "idk"

    peak_day = argmax(forecast)

    if peak_day == 0:
        decision = "sell"
    else:
        decision = "wait"

    return decision

def get_ai_bot_recomendations(forecast, decision: Literal["sell", "wait"]):
    client = genai.Client(api_key=env["GEMINI_API_KEY"])
    model = "gemini-2.5-flash"
    prompt = f'Can you explain the reason behind this decision "{decision}", considering this {len(forecast)} days forecast: {forecast}'

    recomendations = client.models.generate_content(model=model, contents=prompt)

    print(recomendations.text)


if __name__ == "__main__":
    forecast = get_forecast()
    decision = what_to_do(forecast)

    get_ai_bot_recomendations(forecast, decision)
