import yfinance as yf
import requests
import datetime

WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbxs78L44fctQ1aarbq5iY17dFmKS0St2Dh7ykgoJr7hr4douTRV_ntvvmzKDlh15bQM/exec"

def get_last_close(ticker):
    try:
        hist = yf.Ticker(ticker).history(period="5d")
        if hist.empty or "Close" not in hist.columns:
            return None
        return float(hist["Close"].dropna().iloc[-1])
    except Exception:
        return None

gold = get_last_close("4GLD.DE")
miners = get_last_close("G2X.DE")
oil = get_last_close("OD7F.DE")
usd = get_last_close("DX-Y.NYB")
us10y = get_last_close("^TNX")

if gold is None or miners is None:
    raise ValueError("Não foi possível obter dados de 4GLD.DE ou G2X.DE")

ratio = miners / gold if gold else None

# Regra macro simples
macro_signal = "NEUTRAL"
if usd is not None and us10y is not None:
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
    "macro_signal": macro_signal
}

response = requests.post(WEBHOOK_URL, json=payload, timeout=30)

print("Status:", response.status_code)
print("Resposta:", response.text)
