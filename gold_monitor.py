import datetime
import requests
import yfinance as yf


WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbxs78L44fctQ1aarbq5iY17dFmKS0St2Dh7ykgoJr7hr4douTRV_ntvvmzKDlh15bQM/exec"


def get_last_close(ticker: str):
    """Devolve o último preço de fecho disponível."""
    try:
        hist = yf.Ticker(ticker).history(period="1d", interval="5m")
        if hist.empty or "Close" not in hist.columns:
            return None
        closes = hist["Close"].dropna()
        if closes.empty:
            return None
        return float(closes.iloc[-1])
    except Exception:
        return None


def get_prev_close(ticker: str):
    """Devolve o fecho anterior disponível para comparar direção."""
    try:
        hist = yf.Ticker(ticker).history(period="10d")
        if hist.empty or "Close" not in hist.columns:
            return None
        closes = hist["Close"].dropna()
        if len(closes) < 2:
            return None
        return float(closes.iloc[-2])
    except Exception:
        return None


# Ativos principais
gold = get_last_close("4GLD.DE")
miners = get_last_close("G2X.DE")
oil = get_last_close("OD7F.DE")

# Macro
usd = get_last_close("DX=F")
us10y = get_last_close("^TNX")

usd_prev = get_prev_close("DX=F")
us10y_prev = get_prev_close("^TNX")

if gold is None or miners is None:
    raise ValueError("Não foi possível obter dados de 4GLD.DE ou G2X.DE")

ratio = miners / gold if gold else None

# Lógica macro simples
macro_signal = "NEUTRAL"

if usd is not None and us10y is not None and usd_prev is not None and us10y_prev is not None:
    usd_change = usd - usd_prev
    us10y_change = us10y - us10y_prev

    if usd_change < 0 and us10y_change < 0:
        macro_signal = "BULLISH_GOLD"
    elif usd_change > 0 and us10y_change > 0:
        macro_signal = "BEARISH_GOLD"
    else:
        macro_signal = "NEUTRAL"

payload = {
    "timestamp": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    "gold_price": gold,
    "miners_price": miners,
    "oil_price": oil,
    "ratio": ratio,
    "signal": "update",
    "usd_index": usd,
    "us10y_yield": us10y,
    "macro_signal": macro_signal,
}

response = requests.post(WEBHOOK_URL, json=payload, timeout=30)

print("Status:", response.status_code)
print("Resposta:", response.text)
print("Payload enviado:", payload)
