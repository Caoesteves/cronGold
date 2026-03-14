import datetime
import math
import requests
import yfinance as yf
import pandas as pd

WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbxs78L44fctQ1aarbq5iY17dFmKS0St2Dh7ykgoJr7hr4douTRV_ntvvmzKDlh15bQM/exec"

def get_series(ticker: str, period: str = "1d", interval: str = "5m"):
    try:
        hist = yf.Ticker(ticker).history(period=period, interval=interval, auto_adjust=False)
        if hist.empty or "Close" not in hist.columns:
            return None
        closes = hist["Close"].dropna()
        if closes.empty:
            return None
        return closes
    except Exception:
        return None

def last_value(series):
    if series is None or series.empty:
        return None
    try:
        return float(series.iloc[-1])
    except Exception:
        return None

def prev_value(series):
    if series is None or len(series) < 2:
        return None
    try:
        return float(series.iloc[-2])
    except Exception:
        return None

def calculate_rsi(series, period=14):
    if series is None or len(series) < period + 1:
        return None

    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss.replace(0, pd.NA)
    rsi = 100 - (100 / (1 + rs))

    value = rsi.iloc[-1]
    if pd.isna(value):
        return None
    return float(value)

def calculate_momentum_20(series):
    if series is None or len(series) < 21:
        return None
    base = float(series.iloc[-21])
    last = float(series.iloc[-1])
    if base == 0:
        return None
    return ((last / base) - 1) * 100.0

def safe_round(value, digits=4):
    if value is None:
        return None
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    return round(value, digits)

# -----------------------------
# ATIVOS CONSISTENTES COM A SHEET
# -----------------------------
gold_series = get_series("4GLD.DE", period="1d", interval="5m")
miners_series = get_series("G2X.DE", period="1d", interval="5m")

# petróleo / macro
oil_series = get_series("BZ=F", period="1d", interval="5m") or get_series("CL=F", period="1d", interval="5m")
usd_series = get_series("DX=F", period="1d", interval="5m")
us10y_series = get_series("^TNX", period="1d", interval="5m")

gold = last_value(gold_series)
miners = last_value(miners_series)
oil = last_value(oil_series)
usd = last_value(usd_series)
us10y = last_value(us10y_series)

usd_prev = prev_value(usd_series)
us10y_prev = prev_value(us10y_series)

if gold is None or miners is None:
    raise ValueError("Não foi possível obter dados de 4GLD.DE ou G2X.DE")

ratio = miners / gold if gold else None

rsi_gold = calculate_rsi(gold_series, period=14)
rsi_miners = calculate_rsi(miners_series, period=14)

momentum_gold_20 = calculate_momentum_20(gold_series)
momentum_miners_20 = calculate_momentum_20(miners_series)

macro_signal = "NEUTRAL"
if usd is not None and usd_prev is not None and us10y is not None and us10y_prev is not None:
    usd_change = usd - usd_prev
    us10y_change = us10y - us10y_prev

    if usd_change < 0 and us10y_change < 0:
        macro_signal = "BULLISH_GOLD"
    elif usd_change > 0 and us10y_change > 0:
        macro_signal = "BEARISH_GOLD"
    else:
        macro_signal = "NEUTRAL"

score_tecnico_buy = 0
score_tecnico_sell = 0

if rsi_gold is not None:
    if rsi_gold >= 55:
        score_tecnico_buy += 2
    elif rsi_gold <= 45:
        score_tecnico_sell += 2

if rsi_miners is not None:
    if rsi_miners >= 55:
        score_tecnico_buy += 2
    elif rsi_miners <= 45:
        score_tecnico_sell += 2

if momentum_gold_20 is not None:
    if momentum_gold_20 > 0:
        score_tecnico_buy += 1
    elif momentum_gold_20 < 0:
        score_tecnico_sell += 1

if momentum_miners_20 is not None:
    if momentum_miners_20 > 0:
        score_tecnico_buy += 2
    elif momentum_miners_20 < 0:
        score_tecnico_sell += 2

if momentum_gold_20 is not None and momentum_miners_20 is not None:
    if momentum_miners_20 > momentum_gold_20:
        score_tecnico_buy += 1
    elif momentum_miners_20 < momentum_gold_20:
        score_tecnico_sell += 1

macro_bonus_buy = 0
macro_bonus_sell = 0

if macro_signal == "BULLISH_GOLD":
    macro_bonus_buy = 2
elif macro_signal == "BEARISH_GOLD":
    macro_bonus_sell = 2

score_total_buy = score_tecnico_buy + macro_bonus_buy
score_total_sell = score_tecnico_sell + macro_bonus_sell

payload = {
    "timestamp": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    "gold_price": safe_round(gold, 6),
    "miners_price": safe_round(miners, 6),
    "oil_price": safe_round(oil, 6),
    "ratio": safe_round(ratio, 10),
    "signal": "update",
    "usd_index": safe_round(usd, 6),
    "us10y_yield": safe_round(us10y, 6),
    "macro_signal": macro_signal,
    "rsi_gold": safe_round(rsi_gold, 2),
    "rsi_miners": safe_round(rsi_miners, 2),
    "momentum_gold_20": safe_round(momentum_gold_20, 2),
    "momentum_miners_20": safe_round(momentum_miners_20, 2),
    "score_tecnico_buy": score_tecnico_buy,
    "score_tecnico_sell": score_tecnico_sell,
    "score_total_buy": score_total_buy,
    "score_total_sell": score_total_sell
}

response = requests.post(WEBHOOK_URL, json=payload, timeout=30)

print("Status:", response.status_code)
print("Resposta:", response.text)
print("Payload:", payload)
