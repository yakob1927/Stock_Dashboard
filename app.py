import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Live Stock Dashboard", layout="wide")

st.title("📈 Live Stock Market Dashboard")

# Popular Symbols
popular_symbols = {
    "Apple": "AAPL",
    "Microsoft": "MSFT",
    "Google": "GOOGL",
    "Amazon": "AMZN",
    "Tesla": "TSLA",
    "NVIDIA": "NVDA",
    "Meta": "META",
    "Reliance": "RELIANCE.NS",
    "TCS": "TCS.NS",
    "Infosys": "INFY.NS",
    "HDFC Bank": "HDFCBANK.NS",
    "ICICI Bank": "ICICIBANK.NS"
}

selected_company = st.selectbox(
    "Select Stock",
    list(popular_symbols.keys())
)

symbol = popular_symbols[selected_company]

period = st.selectbox(
    "Select Period",
    ["1d", "5d", "1mo", "3mo", "6mo", "1y"]
)

try:
    # Download stock data
    data = yf.download(
        symbol,
        period=period,
        interval="1m" if period == "1d" else "1d",
        progress=False,
        auto_adjust=True
    )

    if data.empty:
        st.error("No data available.")
        st.stop()

    # Handle MultiIndex columns
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    st.subheader(f"Stock Data: {symbol}")

    # Current Price
    current_price = float(data["Close"].iloc[-1])

    # Previous Close
    if len(data) > 1:
        previous_price = float(data["Close"].iloc[-2])
    else:
        previous_price = current_price

    change = current_price - previous_price
    percent_change = (change / previous_price) * 100 if previous_price != 0 else 0

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Current Price",
            f"₹{current_price:.2f}"
        )

    with col2:
        st.metric(
            "Change",
            f"{change:.2f}"
        )

    with col3:
        st.metric(
            "% Change",
            f"{percent_change:.2f}%"
        )

    # Candlestick Chart
    fig = go.Figure()

    fig.add_trace(
        go.Candlestick(
            x=data.index,
            open=data["Open"],
            high=data["High"],
            low=data["Low"],
            close=data["Close"],
            name="Price"
        )
    )

    fig.update_layout(
        title=f"{symbol} Stock Price",
        xaxis_title="Date",
        yaxis_title="Price",
        height=600
    )

    st.plotly_chart(fig, use_container_width=True)

    # Moving Average
    data["MA20"] = data["Close"].rolling(20).mean()

    st.subheader("Moving Average")

    fig2 = go.Figure()

    fig2.add_trace(
        go.Scatter(
            x=data.index,
            y=data["Close"],
            name="Close Price"
        )
    )

    fig2.add_trace(
        go.Scatter(
            x=data.index,
            y=data["MA20"],
            name="20-Day MA"
        )
    )

    st.plotly_chart(fig2, use_container_width=True)

    # Technical Analysis
    st.subheader("AI Analysis")

    latest_close = float(data["Close"].iloc[-1])
    ma20 = float(data["MA20"].dropna().iloc[-1]) if not data["MA20"].dropna().empty else latest_close

    if latest_close > ma20:
        st.success("📈 Bullish Trend - Price Above MA20")
    elif latest_close < ma20:
        st.error("📉 Bearish Trend - Price Below MA20")
    else:
        st.warning("⚖ Neutral Trend")

    st.subheader("Recent Data")
    st.dataframe(data.tail(20))

except Exception as e:
    st.error(f"Error: {e}")