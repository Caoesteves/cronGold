import datetime
import math
import requests
import yfinance as yf
import pandas as pd

WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbxs78L44fctQ1aarbq5iY17dFmKS0St2Dh7ykgoJr7hr4douTRV_ntvvmzKDlh15bQM/exec"

def get_series(ticker: str, period: str = "1d", interval: str = "5m") -> pd.Series | None:
    """Devolve a série de fechos do ticker."""
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


def get_series_with_fallback(tickers: list[str], period: str = "1d", interval: str = "5m") -> tuple[pd.Series | None, str | None]:
    """Tenta vários tickers e devolve a primeira série válida."""
    for ticker in tickers:
        series = get_series(ticker, period=period, interval=interval)
        if series is not None and not series.empty:
            return series, ticker
    return None, None


def last_value(series: pd.Series | None) -> float | None:
    if series is None or series.empty:
        return None
    try:
        return float(series.iloc[-1])
    except Exception:
        return None


def prev_value(series: pd.Series | None) -> float | None:
    if series is None or len(series) < 2:
        return None
    try:
        return float(series.iloc[-2])
    except Exception:
        return None


def calculate_rsi(series: pd.Series | None, period: int = 14) -> float | None:
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


def calculate_momentum_20(series: pd.Series | None) -> float | None:
    """
    Momentum em % comparando o último valor com o valor de 20 períodos atrás.
    Em 5m, 20 períodos ≈ 100 minutos.
    """
    if series is None or len(series) < 21:
        return None
    base = float(series.iloc[-21])
    last = float(series.iloc[-1])
    if base == 0:
        return None
    return ((last / base) - 1) * 100.0


def safe_round(value: float | None, digits: int = 4) -> float | None:
    if value is None:
        return None
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    return round(value, digits)


# =========================
# 1) Séries principais
# =========================

gold_series, gold_ticker = get_series_with_fallback(["4GLD.DE"])
miners_series, miners_ticker = get_series_with_fallback(["G2X.DE"])

# OD7F.DE falha frequentemente no Yahoo; deixo fallback para Brent/WTI
oil_series, oil_ticker = get_series_with_fallback(["OD7F.DE", "BZ=F", "CL=F"])

usd_series, usd_ticker = get_series_with_fallback(["DX=F", "DX-Y.NYB"])
us10y_series, us10y_ticker = get_series_with_fallback(["^TNX"])

gold = last_value(gold_series)
miners = last_value(miners_series)
oil = last_value(oil_series)
usd = last_value(usd_series)
us10y = last_value(us10y_series)

usd_prev = prev_value(usd_series)
us10y_prev = prev_value(us10y_series)

if gold is None or miners is None:
    raise ValueError("Não foi possível obter dados de 4GLD.DE ou G2X.DE")

ratio = (miners / gold) if gold else None

# =========================
# 2) Indicadores técnicos
# =========================

rsi_gold = calculate_rsi(gold_series, period=14)
rsi_miners = calculate_rsi(miners_series, period=14)

momentum_gold_20 = calculate_momentum_20(gold_series)
momentum_miners_20 = calculate_momentum_20(miners_series)

# =========================
# 3) Macro signal
# =========================

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

# =========================
# 4) Score técnico
# =========================

score_tecnico_buy = 0
score_tecnico_sell = 0

# RSI Gold
if rsi_gold is not None:
    if rsi_gold >= 55:
        score_tecnico_buy += 2
    elif rsi_gold <= 45:
        score_tecnico_sell += 2

# RSI Miners
if rsi_miners is not None:
    if rsi_miners >= 55:
        score_tecnico_buy += 2
    elif rsi_miners <= 45:
        score_tecnico_sell += 2

# Momentum Gold
if momentum_gold_20 is not None:
    if momentum_gold_20 > 0:
        score_tecnico_buy += 1
    elif momentum_gold_20 < 0:
        score_tecnico_sell += 1

# Momentum Miners
if momentum_miners_20 is not None:
    if momentum_miners_20 > 0:
        score_tecnico_buy += 2
    elif momentum_miners_20 < 0:
        score_tecnico_sell += 2

# Liderança relativa: miners com melhor momentum que ouro
if momentum_gold_20 is not None and momentum_miners_20 is not None:
    if momentum_miners_20 > momentum_gold_20:
        score_tecnico_buy += 1
    elif momentum_miners_20 < momentum_gold_20:
        score_tecnico_sell += 1

# Bónus macro simples
macro_bonus_buy = 0
macro_bonus_sell = 0

if macro_signal == "BULLISH_GOLD":
    macro_bonus_buy = 2
elif macro_signal == "BEARISH_GOLD":
    macro_bonus_sell = 2

score_total_buy = score_tecnico_buy + macro_bonus_buy
score_total_sell = score_tecnico_sell + macro_bonus_sell

# =========================
# 5) Payload
# =========================

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
    "score_total_sell": score_total_sell,
    "debug_gold_ticker": gold_ticker,
    "debug_miners_ticker": miners_ticker,
    "debug_oil_ticker": oil_ticker,
    "debug_usd_ticker": usd_ticker,
    "debug_us10y_ticker": us10y_ticker,
}

response = requests.post(WEBHOOK_URL, json=payload, timeout=30)

print("Status:", response.status_code)
print("Resposta:", response.text)
print("Payload enviado:", payload)
