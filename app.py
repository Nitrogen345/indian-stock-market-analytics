import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Indian Stock Analytics", layout="wide")

st.title("📈 Indian Stock Market Live Analytics System")

# -----------------------------
# Sidebar Controls
# -----------------------------

st.sidebar.header("Stock Controls")

ticker = st.sidebar.text_input("Select Stock", "RELIANCE.NS")

compare_stocks = st.sidebar.multiselect(
    "Compare With",
    ["TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS","SBIN.NS"]
)

start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2022-01-01"))
end_date = st.sidebar.date_input("End Date", pd.to_datetime("today"))

# -----------------------------
# Data Fetching
# -----------------------------

@st.cache_data
def get_data(ticker):
    df = yf.download(ticker,start=start_date,end=end_date)

    if df.empty:
        return df

    df.reset_index(inplace=True)
    return df

df = get_data(ticker)

if df.empty:
    st.error("No stock data found.")
    st.stop()

# -----------------------------
# Indicators
# -----------------------------

df["Daily Return"] = df["Close"].pct_change()

df["SMA20"] = df["Close"].rolling(20).mean()
df["SMA50"] = df["Close"].rolling(50).mean()

# RSI

delta = df["Close"].diff()

gain = delta.clip(lower=0)
loss = -delta.clip(upper=0)

avg_gain = gain.rolling(14).mean()
avg_loss = loss.rolling(14).mean()

rs = avg_gain / avg_loss

df["RSI"] = 100 - (100/(1+rs))

df["Volatility"] = df["Daily Return"].rolling(14).std()

# -----------------------------
# Recommendation Engine
# -----------------------------

def recommendation(data):

    latest = data.iloc[-1]

    sma20 = float(latest["SMA20"])
    sma50 = float(latest["SMA50"])
    rsi = float(latest["RSI"])

    if pd.isna(sma20) or pd.isna(sma50) or pd.isna(rsi):
        return "Not enough data"

    if sma20 > sma50 and rsi < 70:
        return "BUY"

    elif sma20 < sma50 and rsi > 30:
        return "SELL"

    else:
        return "HOLD"

signal = recommendation(df)

# -----------------------------
# Metrics
# -----------------------------

st.subheader("Stock Overview")

col1,col2,col3,col4 = st.columns(4)

latest_price = df["Close"].iloc[-1]
daily_return = df["Daily Return"].iloc[-1]
volatility = df["Volatility"].iloc[-1]
rsi_value = df["RSI"].iloc[-1]

col1.metric("Latest Price",round(latest_price,2))
col2.metric("Daily Return %",round(daily_return*100,2))
col3.metric("Volatility %",round(volatility*100,2))
col4.metric("RSI",round(rsi_value,2))

# -----------------------------
# Recommendation
# -----------------------------

st.subheader("AI Recommendation")

if signal == "BUY":
    st.success("BUY Signal")

elif signal == "SELL":
    st.error("SELL Signal")

else:
    st.warning("HOLD")

# -----------------------------
# Candlestick Chart
# -----------------------------

st.subheader("Candlestick Chart")

fig = go.Figure()

fig.add_trace(go.Candlestick(
    x=df["Date"],
    open=df["Open"],
    high=df["High"],
    low=df["Low"],
    close=df["Close"],
    name="Price"
))

fig.add_trace(go.Scatter(
    x=df["Date"],
    y=df["SMA20"],
    name="SMA20"
))

fig.add_trace(go.Scatter(
    x=df["Date"],
    y=df["SMA50"],
    name="SMA50"
))

st.plotly_chart(fig,use_container_width=True)

# -----------------------------
# RSI Chart
# -----------------------------

st.subheader("RSI Indicator")

fig_rsi = go.Figure()

fig_rsi.add_trace(go.Scatter(
    x=df["Date"],
    y=df["RSI"],
    name="RSI"
))

fig_rsi.add_hline(y=70)
fig_rsi.add_hline(y=30)

st.plotly_chart(fig_rsi,use_container_width=True)

# -----------------------------
# Volume Chart
# -----------------------------

st.subheader("Volume")

fig_vol = go.Figure()

fig_vol.add_trace(go.Bar(
    x=df["Date"],
    y=df["Volume"],
    name="Volume"
))

st.plotly_chart(fig_vol,use_container_width=True)

# -----------------------------
# Stock Comparison
# -----------------------------

if compare_stocks:

    st.subheader("Stock Growth Comparison")

    fig_compare = go.Figure()

    base = df["Close"] / df["Close"].iloc[0]

    fig_compare.add_trace(go.Scatter(
        x=df["Date"],
        y=base,
        name=ticker
    ))

    for stock in compare_stocks:

        comp_df = get_data(stock)

        if comp_df.empty:
            continue

        normalized = comp_df["Close"] / comp_df["Close"].iloc[0]

        fig_compare.add_trace(go.Scatter(
            x=comp_df["Date"],
            y=normalized,
            name=stock
        ))

    st.plotly_chart(fig_compare,use_container_width=True)

# -----------------------------
# Portfolio Simulation
# -----------------------------

st.subheader("Portfolio Simulation")

investment = st.number_input("Investment Amount",1000,1000000,10000)

shares = investment / latest_price

portfolio_value = shares * latest_price

st.write("Estimated Shares:",round(shares,2))
st.write("Current Portfolio Value:",round(portfolio_value,2))
