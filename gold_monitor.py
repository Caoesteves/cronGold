import yfinance as yf
import requests
import datetime
import gspread
from google.oauth2.service_account import Credentials

WEBHOOK_URL = "COLE_AQUI_O_SEU_WEBHOOK"

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

if gold is None or miners is None:
    raise ValueError("Não foi possível obter dados de 4GLD.DE ou G2X.DE")

ratio = miners / gold if gold else None

# Para já estes cálculos serão feitos na Sheet, por isso enviamos só placeholders
payload = {
    "timestamp": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    "gold_price": gold,
    "miners_price": miners,
    "oil_price": oil,
    "ratio": ratio,
    "signal": "update"
}

response = requests.post(WEBHOOK_URL, json=payload, timeout=30)

print("Status:", response.status_code)
print("Resposta:", response.text)
