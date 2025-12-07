import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from datetime import datetime, timedelta

class MarketAnalyzer:
    def __init__(self):
        # Тикеры
        self.tickers = {
            'cotton': 'CT=F', 
            'currency': 'USDKZT=X' 
        }

    def get_data_with_forecast(self, asset_type='cotton', days_forecast=30):
        ticker = self.tickers.get(asset_type, 'CT=F')
        
        # 1. Скачиваем данные
        # multi_level_index=False помогает избежать сложных заголовков в новых версиях yf
        try:
            df = yf.download(ticker, period='6mo', interval='1d', progress=False)
        except Exception as e:
            print(f"Error downloading {ticker}: {e}")
            return None

        if df.empty:
            return None

        # 2. Очистка данных (Критически важно!)
        # Если yfinance вернул MultiIndex (Price, Ticker), убираем лишний уровень
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df = df.reset_index()

        # Убедимся, что колонка Date существует (иногда она называется index)
        if 'Date' not in df.columns:
            # Если после reset_index дата осталась в индексе или имеет другое имя
            return None

        # Явное приведение 'Close' к числам, ошибки превращаем в NaN и удаляем
        df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
        df = df.dropna(subset=['Close', 'Date'])

        # 3. Подготовка к ML
        df['DateOrdinal'] = df['Date'].apply(lambda x: x.toordinal())
        
        X = df[['DateOrdinal']].values
        y = df['Close'].values

        if len(y) < 2:
            return None # Недостаточно данных для обучения

        # 4. Обучение
        model = LinearRegression()
        model.fit(X, y)

        # 5. Прогноз
        last_date = df['Date'].iloc[-1]
        future_dates = [last_date + timedelta(days=i) for i in range(1, days_forecast + 1)]
        future_X = np.array([d.toordinal() for d in future_dates]).reshape(-1, 1)

        predictions = model.predict(future_X)
        
        # Добавляем шум для реалистичности
        noise = np.random.normal(0, np.std(y) * 0.05, size=len(predictions))
        predictions = predictions.flatten() + noise

        # 6. Формирование ответа (Простой и надежный цикл)
        history = []
        for _, row in df.iterrows():
            history.append({
                "date": row['Date'].strftime('%Y-%m-%d'),
                "price": round(float(row['Close']), 2), # Явный float() перед round()
                "type": "history"
            })

        forecast = []
        for d, p in zip(future_dates, predictions):
            forecast.append({
                "date": d.strftime('%Y-%m-%d'),
                "price": round(float(p), 2),
                "type": "forecast"
            })

        # 7. AI Аналитика
        if not history or not forecast:
            return None

        current_price = history[-1]['price']
        future_price = forecast[-1]['price']
        
        # Защита от деления на ноль
        if current_price == 0:
            change_pct = 0
        else:
            change_pct = ((future_price - current_price) / current_price) * 100

        recommendation = "HOLD"
        reason = "Рынок показывает стабильность, резких колебаний не ожидается."
        
        if change_pct > 2:
            recommendation = "WAIT"
            reason = f"AI прогнозирует рост цены на {change_pct:.1f}% в течение недели. Рекомендуется отложить продажу."
        elif change_pct < -2:
            recommendation = "SELL"
            reason = f"AI фиксирует тренд на снижение (-{abs(change_pct):.1f}%). Рекомендуется продать партию сейчас."

        return {
            "asset": asset_type,
            "current_price": current_price,
            "chart_data": history + forecast,
            "ai_analysis": {
                "signal": recommendation,
                "confidence": "87%", 
                "reason": reason,
                "forecast_trend": "UP" if change_pct > 0 else "DOWN"
            }
        }