import yfinance as yf
import requests
from datetime import datetime

# -----------------------------
# CONFIGURAÇÃO
# -----------------------------

WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbxs78L44fctQ1aarbq5iY17dFmKS0St2Dh7ykgoJr7hr4douTRV_ntvvmzKDlh15bQM/exec"

TICKERS = {
    "gold": "GC=F",
    "miners": "GDX",
    "oil": "CL=F",
    "usd": "DX-Y.NYB",
    "us10y": "^TNX"
}

# -----------------------------
# FUNÇÃO PARA OBTER PREÇOS
# -----------------------------

def get_price(ticker):
    try:
        data = yf.Ticker(ticker).history(period="1d", interval="1m")
        return float(data["Close"].iloc[-1])
    except:
        return None


# -----------------------------
# RECOLHA DE DADOS
# -----------------------------

gold_price = get_price(TICKERS["gold"])
miners_price = get_price(TICKERS["miners"])
oil_price = get_price(TICKERS["oil"])
usd_index = get_price(TICKERS["usd"])
us10y_yield = get_price(TICKERS["us10y"])

timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

# -----------------------------
# RATIO MINERS VS GOLD
# -----------------------------

ratio = None
if gold_price and miners_price:
    ratio = miners_price / gold_price


# -----------------------------
# MACRO SIGNAL SIMPLES
# -----------------------------

macro_signal = "NEUTRAL"

if usd_index and us10y_yield:
    
    if usd_index < 102 and us10y_yield < 4.3:
        macro_signal = "BULLISH_GOLD"

    elif usd_index > 104 and us10y_yield > 4.6:
        macro_signal = "BEARISH_GOLD"


# -----------------------------
# PAYLOAD PARA GOOGLE SHEETS
# -----------------------------

payload = {
    "timestamp": timestamp,
    "gold_price": gold_price,
    "miners_price": miners_price,
    "oil_price": oil_price,
    "ratio": ratio,
    "signal": "update",
    "usd_index": usd_index,
    "us10y_yield": us10y_yield,
    "macro_signal": macro_signal,

    # campos futuros
    "rsi_gold": "",
    "rsi_miners": "",
    "momentum_gold_20": "",
    "momentum_miners_20": "",
    "score_tecnico_buy": "",
    "score_tecnico_sell": "",
    "score_total_buy": "",
    "score_total_sell": ""
}

# -----------------------------
# ENVIO PARA GOOGLE SHEETS
# -----------------------------

try:

    r = requests.post(WEBHOOK_URL, json=payload)

    print("Status:", r.status_code)
    print("Resposta:", r.text)

except Exception as e:

    print("Erro envio:", e)
