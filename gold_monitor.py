import yfinance as yf
import requests
import datetime

WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbxs78L44fctQ1aarbq5iY17dFmKS0St2Dh7ykgoJr7hr4douTRV_ntvvmzKDIh15bQM/exec"

gold = yf.Ticker("4GLD.DE").history(period="1d")["Close"].iloc[-1]
miners = yf.Ticker("G2X.DE").history(period="1d")["Close"].iloc[-1]
oil = yf.Ticker("OD7F.DE").history(period="1d")["Close"].iloc[-1]

ratio = miners / gold

payload = {
    "timestamp": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    "gold_price": float(gold),
    "miners_price": float(miners),
    "oil_price": float(oil),
    "ratio": float(ratio),
    "signal": "update"
}

requests.post(WEBHOOK_URL, json=payload)

print("Dados enviados para Google Sheet")
