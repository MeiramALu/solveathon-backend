import requests
import pandas as pd
import pmdarima as pm
import numpy as np
from datetime import datetime, date, timedelta
from bs4 import BeautifulSoup
from statsmodels.tsa.arima.model import ARIMA
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import r2_score
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.layers import Bidirectional, LSTM, Dense, Input, LayerNormalization, MultiHeadAttention, Dropout, Flatten


def get_data(iso, start_date, end_date):
    api_url = 'http://api.cba.am/exchangerates.asmx'
    iso_codes = iso
    start_date = start_date
    end_date = end_date

    request_body = f"""<?xml version="1.0" encoding="utf-8"?>
    <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
      <soap:Body>
        <ExchangeRatesByDateRangeByISO xmlns="http://www.cba.am/">
          <ISOCodes>{iso_codes}</ISOCodes>
          <DateFrom>{start_date}</DateFrom>
          <DateTo>{end_date}</DateTo>
        </ExchangeRatesByDateRangeByISO>
      </soap:Body>
    </soap:Envelope>
    """
    request_headers = {'Content-Type': 'text/xml; charset=utf-8', 'SOAPAction': 'http://www.cba.am/ExchangeRatesByDateRangeByISO'}
    response = requests.post(api_url, data=request_body, headers=request_headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'xml')
        data = []

        for entry in soup.find_all('ExchangeRatesByRange'):
            rate_date = datetime.strptime(entry.find('RateDate').text, "%Y-%m-%dT%H:%M:%S%z").date()

            rate = float(entry.find('Rate').text)
            data.append([rate_date, rate])

        # Create a DataFrame
        df = pd.DataFrame(data, columns=['Date', 'Rate']).iloc[:-1]
        return df

    else:
        print(f"HTTP Error: {response.status_code}")
        return None

def lregression_predict_single_echange_rate(iso, start_date, end_date):
    df = get_data(iso, start_date, end_date)

    min_date = min(df['Date'])
    df['Date'] = [(d - min_date).days for d in df['Date']]

    n = len(df['Date'])
    sum_x = df['Date'].sum()
    sum_y = df['Rate'].sum()
    sum_xy = (df['Date'] * df['Rate']).sum()
    sum_x_squared = (df['Date']**2).sum()

    w1 = (n * sum_xy - sum_x * sum_y) / (n * sum_x_squared - sum_x**2)
    w0 = (sum_y - w1 * sum_x) / n

    last_day = df['Date'].max()
    forecast = w0 + w1 * last_day
    last_rate = df[df['Date'] == last_day]['Rate'].values[0]

    return last_rate, forecast

def lregression_predict(start_date, end_date=date.today().strftime("%Y-%m-%d")):
    usd_real, usd_pred = lregression_predict_single_echange_rate("USD", start_date, end_date)
    kzt_real, kzt_pred = lregression_predict_single_echange_rate("KZT", start_date, end_date)

    last_rate = usd_real / kzt_real * 10
    forecast = usd_pred / kzt_pred * 10

    return last_rate, forecast

def arima_predict(start_date, end_date=date.today().strftime("%Y-%m-%d"), forecast_days=1):
    df_usd = get_data("USD", start_date, end_date)
    df_kzt = get_data("KZT", start_date, end_date)

    df = df_usd.merge(df_kzt, on="Date", suffixes=("_usd", "_kzt"))
    data = (df["Rate_usd"] / df["Rate_kzt"]).to_numpy()

    model = ARIMA(data, order=(5,1,0))
    model_fit = model.fit()

    forecast = model_fit.forecast(steps=forecast_days)
    last_rates = data[-forecast_days:]

    mae = mean_absolute_error(last_rates, forecast)
    rmse = float(np.sqrt(mean_squared_error(last_rates, forecast)))
    mape = float(np.mean(np.abs((last_rates - forecast) / last_rates)) * 100)
    r2 = float(r2_score(last_rates, forecast))

    with open("results.txt", "w") as file:
        file.write(f"arima: mae={mae:.5f} rmse={rmse:.5f} mape={mape:.5f} r2={r2:.5f}\n")

    last_rates *= 10
    forecast *= 10

    return last_rates, forecast

def auto_arima_predict(start_date, end_date=date.today().strftime("%Y-%m-%d"), forecast_days=1):
    df_usd = get_data("USD", start_date, end_date)
    df_kzt = get_data("KZT", start_date, end_date)

    df = df_usd.merge(df_kzt, on="Date", suffixes=("_usd", "_kzt"))
    data = (df["Rate_usd"] / df["Rate_kzt"]).to_numpy()

    model = pm.auto_arima(data, seasonal=False, stepwise=True)

    forecast = model.predict(n_periods=forecast_days)
    last_rates = data[-forecast_days:]

    mae = mean_absolute_error(last_rates, forecast)
    rmse = float(np.sqrt(mean_squared_error(last_rates, forecast)))
    mape = float(np.mean(np.abs((last_rates - forecast) / last_rates)) * 100)
    r2 = float(r2_score(last_rates, forecast))

    with open("results.txt", "a") as file:
        file.write(f"auto_arima: mae={mae:.5f} rmse={rmse:.5f} mape={mape:.5f} r2={r2:.5f}\n")

    last_rates *= 10
    forecast *= 10

    return last_rates, forecast

def lstm_predict(start_date, end_date=date.today().strftime("%Y-%m-%d"), forecast_days=1, model_name="lstm", n_input=7, epochs=50, batch_size=32):
    df_usd = get_data("USD", start_date, end_date)
    df_kzt = get_data("KZT", start_date, end_date)
    df = df_usd.merge(df_kzt, on="Date", suffixes=("_usd", "_kzt"))
    data = (df["Rate_usd"] / df["Rate_kzt"]).to_numpy().reshape(-1, 1)

    scaler = MinMaxScaler(feature_range=(0, 1))
    data_scaled = scaler.fit_transform(data)

    X, y = [], []
    for i in range(n_input, len(data_scaled)):
        X.append(data_scaled[i-n_input:i, 0])
        y.append(data_scaled[i, 0])
    X, y = np.array(X), np.array(y)
    X = X.reshape((X.shape[0], X.shape[1], 1))

    model = Sequential()
    model.add(Input(shape=(n_input, 1)))
    model.add(LSTM(50, activation='relu'))
    model.add(Dense(1))
    model.compile(optimizer='adam', loss='mse')

    model.fit(X, y, epochs=epochs, batch_size=batch_size, verbose=0)

    forecast_scaled = []
    input_seq = data_scaled[-n_input:].reshape(1, n_input, 1)
    for _ in range(forecast_days):
        pred = model.predict(input_seq, verbose=0)
        forecast_scaled.append(pred[0,0])

        pred_reshaped = pred.reshape((1,1,1))
        input_seq = np.concatenate((input_seq[:,1:,:], pred_reshaped), axis=1)

    forecast = scaler.inverse_transform(np.array(forecast_scaled).reshape(-1,1)).flatten()
    last_rates = data[-forecast_days:]

    mae = mean_absolute_error(last_rates, forecast)
    rmse = float(np.sqrt(mean_squared_error(last_rates, forecast)))
    mape = float(np.mean(np.abs((last_rates - forecast) / last_rates)) * 100)
    r2 = float(r2_score(last_rates, forecast))

    with open("results.txt", "a") as file:
        file.write(f"lstm: mae={mae:.5f} rmse={rmse:.5f} mape={mape:.5f} r2={r2:.5f}\n")

    model.save(model_name + ".keras")

    last_rates *= 10
    forecast *= 10

    return last_rates, forecast

def blstm_predict(start_date, end_date=date.today().strftime("%Y-%m-%d"), forecast_days=1, model_name="blstm", n_input=7, epochs=50, batch_size=32):
    df_usd = get_data("USD", start_date, end_date)
    df_kzt = get_data("KZT", start_date, end_date)
    df = df_usd.merge(df_kzt, on="Date", suffixes=("_usd", "_kzt"))
    data = (df["Rate_usd"] / df["Rate_kzt"]).to_numpy().reshape(-1, 1)

    scaler = MinMaxScaler(feature_range=(0, 1))
    data_scaled = scaler.fit_transform(data)

    X, y = [], []
    for i in range(n_input, len(data_scaled)):
        X.append(data_scaled[i-n_input:i, 0])
        y.append(data_scaled[i, 0])
    X, y = np.array(X), np.array(y)
    X = X.reshape((X.shape[0], X.shape[1], 1))

    model = Sequential()
    model.add(Input(shape=(n_input, 1)))
    model.add(Bidirectional(LSTM(50, activation='relu')))
    model.add(Dense(1))
    model.compile(optimizer='adam', loss='mse')

    model.fit(X, y, epochs=epochs, batch_size=batch_size, verbose=0)

    forecast_scaled = []
    input_seq = data_scaled[-n_input:].reshape(1, n_input, 1)
    for _ in range(forecast_days):
        pred = model.predict(input_seq, verbose=0)
        forecast_scaled.append(pred[0,0])

        pred_reshaped = pred.reshape((1,1,1))
        input_seq = np.concatenate((input_seq[:,1:,:], pred_reshaped), axis=1)

    forecast = scaler.inverse_transform(np.array(forecast_scaled).reshape(-1,1)).flatten()
    last_rates = data[-forecast_days:]

    mae = mean_absolute_error(last_rates, forecast)
    rmse = float(np.sqrt(mean_squared_error(last_rates, forecast)))
    mape = float(np.mean(np.abs((last_rates - forecast) / last_rates)) * 100)
    r2 = float(r2_score(last_rates, forecast))

    with open("results.txt", "a") as file:
        file.write(f"blstm: mae={mae:.5f} rmse={rmse:.5f} mape={mape:.5f} r2={r2:.5f}\n")

    model.save(model_name + ".keras")

    last_rates *= 10
    forecast *= 10

    return last_rates, forecast

def transformer_block(x, num_heads=2, ff_dim=32, dropout_rate=0.1):
    attn_output = MultiHeadAttention(num_heads=num_heads, key_dim=ff_dim)(x, x)
    attn_output = Dropout(dropout_rate)(attn_output)
    out1 = LayerNormalization(epsilon=1e-6)(x + attn_output)

    ffn_output = Dense(ff_dim, activation='relu')(out1)
    ffn_output = Dense(x.shape[-1])(ffn_output)
    ffn_output = Dropout(dropout_rate)(ffn_output)
    out2 = LayerNormalization(epsilon=1e-6)(out1 + ffn_output)

    return out2

def transformer_predict(start_date, end_date=date.today().strftime("%Y-%m-%d"), forecast_days=1, model_name="transformer", n_input=7, epochs=50, batch_size=32):
    df_usd = get_data("USD", start_date, end_date)
    df_kzt = get_data("KZT", start_date, end_date)
    df = df_usd.merge(df_kzt, on="Date", suffixes=("_usd", "_kzt"))
    data = (df["Rate_usd"] / df["Rate_kzt"]).to_numpy().reshape(-1, 1)

    scaler = MinMaxScaler(feature_range=(0, 1))
    data_scaled = scaler.fit_transform(data)

    X, y = [], []
    for i in range(n_input, len(data_scaled)):
        X.append(data_scaled[i-n_input:i, 0])
        y.append(data_scaled[i, 0])
    X, y = np.array(X), np.array(y)
    X = X.reshape((X.shape[0], X.shape[1], 1))

    inputs = Input(shape=(n_input, 1))
    x = transformer_block(inputs)
    x = Flatten()(x)
    outputs = Dense(1)(x)

    model = Model(inputs=inputs, outputs=outputs)
    model.compile(optimizer='adam', loss='mse')

    model.fit(X, y, epochs=epochs, batch_size=batch_size, verbose=0)

    forecast_scaled = []
    input_seq = data_scaled[-n_input:].reshape(1, n_input, 1)
    for _ in range(forecast_days):
        pred = model.predict(input_seq, verbose=0)
        forecast_scaled.append(pred[0,0])
        pred_reshaped = pred.reshape((1,1,1))
        input_seq = np.concatenate((input_seq[:,1:,:], pred_reshaped), axis=1)

    forecast = scaler.inverse_transform(np.array(forecast_scaled).reshape(-1,1)).flatten()
    last_rates = data[-forecast_days:]

    mae = mean_absolute_error(last_rates, forecast)
    rmse = float(np.sqrt(mean_squared_error(last_rates, forecast)))
    mape = float(np.mean(np.abs((last_rates - forecast) / last_rates)) * 100)
    r2 = float(r2_score(last_rates, forecast))

    with open("results.txt", "a") as file:
        file.write(f"transformer: mae={mae:.5f} rmse={rmse:.5f} mape={mape:.5f} r2={r2:.5f}\n")

    model.save(model_name + ".keras")

    last_rates *= 10
    forecast *= 10

    return last_rates, forecast

if __name__ == "__main__":
    start_date = "2022-01-01"
    forecast_days = 7
    end_date = (date.today() - timedelta(days=forecast_days + 1)).strftime("%Y-%m-%d")

    arima_predict(start_date, end_date=end_date, forecast_days=forecast_days)
    auto_arima_predict(start_date, end_date=end_date, forecast_days=forecast_days)
    for i in range(10):
        iter = i + 1

        with open("results.txt", "a") as file:
            file.write(f"--- Iteration #{iter} ---\n")

        lstm_predict(start_date, end_date=end_date, forecast_days=forecast_days, model_name=f"./models/lstm_{iter}")
        blstm_predict(start_date, end_date=end_date, forecast_days=forecast_days, model_name=f"./models/blstm_{iter}")
        transformer_predict(start_date, end_date=end_date, forecast_days=forecast_days, model_name=f"./models/transformer_{iter}")
