
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# --------------------------------
# PAGE CONFIGURATION
# --------------------------------

st.set_page_config(
    page_title="Real-Time Stock Dashboard",
    page_icon="📈",
    layout="wide"
)

# --------------------------------
# AUTOMATIC REFRESH
# --------------------------------

st.title("📈 Real-Time Stock Market Dashboard")

st.caption("Live Stock Monitoring and Data Analysis System")

count = st_autorefresh(
    interval= 5000,
    key="stock_refresh"
)
from datetime import datetime

st.success("🚀 1-SECOND STOCK MONITORING ENABLED")

col1, col2 = st.columns(2)

col1.metric(
    "Refresh Count",
    count
)

col2.metric(
    "Last Dashboard Refresh",
    datetime.now().strftime("%H:%M:%S")
)

st.success("🚀 REAL-TIME MONITORING ENABLED")

st.write(f"Dashboard refresh count: {count}")

# --------------------------------
# STOCK LIST
# --------------------------------

stocks = {
    "Apple (AAPL)": "AAPL",
    "Microsoft (MSFT)": "MSFT",
    "Google (GOOGL)": "GOOGL",
    "Amazon (AMZN)": "AMZN",
    "Tesla (TSLA)": "TSLA",
    "NVIDIA (NVDA)": "NVDA",
    "Meta (META)": "META",
    "Netflix (NFLX)": "NFLX",
    "Reliance": "RELIANCE.NS",
    "TCS": "TCS.NS",
    "Infosys": "INFY.NS",
    "HDFC Bank": "HDFCBANK.NS"
}

# --------------------------------
# SIDEBAR SETTINGS
# --------------------------------

st.sidebar.header("⚙️ Stock Settings")

selected_stock = st.sidebar.selectbox(
    "Select Stock",
    list(stocks.keys())
)

period = st.sidebar.selectbox(
    "Select Period",
    ["1d", "5d", "1mo", "3mo", "6mo", "1y"]
)

ticker = stocks[selected_stock]

intervals = {
    "1d": "1m",
    "5d": "5m",
    "1mo": "30m",
    "3mo": "1d",
    "6mo": "1d",
    "1y": "1d"
}

interval = intervals[period]

currency = "₹" if ticker.endswith(".NS") else "$"

st.sidebar.info(
    f"Selected: {ticker}\n\n"
    f"Period: {period}\n\n"
    f"Interval: {interval}\n\n"
    "Refresh: 60 seconds"
)

# --------------------------------
# FETCH STOCK DATA
# --------------------------------

try:

    stock = yf.Ticker(ticker)

    df = stock.history(
        period=period,
        interval=interval,
        auto_adjust=True
    )

    if df.empty:

        st.error(
            "No stock data available. "
            "Please select another stock or period."
        )

    else:

        df = df.dropna(
            subset=["Close", "Open", "High", "Low"]
        )

        if df.empty:
            st.error("Stock data contains no valid prices.")
            st.stop()

        # --------------------------------
        # TECHNICAL INDICATORS
        # --------------------------------

        df["SMA20"] = df["Close"].rolling(
            window=20,
            min_periods=20
        ).mean()

        df["SMA50"] = df["Close"].rolling(
            window=50,
            min_periods=50
        ).mean()

        # RSI calculation

        delta = df["Close"].diff()

        gain = delta.clip(lower=0)

        loss = -delta.clip(upper=0)

        avg_gain = gain.ewm(
            alpha=1/14,
            min_periods=14,
            adjust=False
        ).mean()

        avg_loss = loss.ewm(
            alpha=1/14,
            min_periods=14,
            adjust=False
        ).mean()

        rs = avg_gain / avg_loss.replace(0, float("nan"))

        df["RSI"] = 100 - (100 / (1 + rs))

        # --------------------------------
        # PRICE CALCULATIONS
        # --------------------------------

        current_price = float(df["Close"].iloc[-1])

        previous_price = (
            float(df["Close"].iloc[-2])
            if len(df) > 1
            else current_price
        )

        change = current_price - previous_price

        percent_change = (
            (change / previous_price) * 100
            if previous_price != 0
            else 0
        )

        latest_volume = int(df["Volume"].iloc[-1])

        # --------------------------------
        # STOCK INFORMATION
        # --------------------------------

        st.header(
            f"📊 {selected_stock} ({ticker})"
        )

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Latest Available Price",
            f"{currency}{current_price:,.2f}"
        )

        col2.metric(
            "Price Change",
            f"{currency}{change:,.2f}",
            f"{percent_change:.2f}%"
        )

        col3.metric(
            "Trading Volume",
            f"{latest_volume:,}"
        )

        col4.metric(
            "Refresh Count",
            count
        )

        st.caption(
            f"Latest available data timestamp: "
            f"{df.index[-1].strftime('%d-%m-%Y %H:%M')}"
        )

        st.divider()

        # --------------------------------
        # STOCK DATA TABLE
        # --------------------------------

        st.subheader("📋 Stock Market Data")

        st.dataframe(
            df.sort_index(ascending=False),
            use_container_width=True
        )

        # --------------------------------
        # CLOSING PRICE CHART
        # --------------------------------

        st.subheader("📈 Closing Price Analysis")

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["Close"],
                mode="lines",
                name="Closing Price"
            )
        )

        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["SMA20"],
                mode="lines",
                name="SMA 20"
            )
        )

        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["SMA50"],
                mode="lines",
                name="SMA 50"
            )
        )

        fig.update_layout(
            title="Stock Price with Moving Averages",
            xaxis_title="Date",
            yaxis_title=f"Price ({currency})",
            height=500,
            hovermode="x unified"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        # --------------------------------
        # CANDLESTICK CHART
        # --------------------------------

        st.subheader("🕯️ Candlestick Analysis")

        candle = go.Figure()

        candle.add_trace(
            go.Candlestick(
                x=df.index,
                open=df["Open"],
                high=df["High"],
                low=df["Low"],
                close=df["Close"],
                name="Stock Price"
            )
        )

        candle.update_layout(
            title="Open, High, Low and Close Prices",
            xaxis_title="Date",
            yaxis_title=f"Price ({currency})",
            height=550
        )

        st.plotly_chart(
            candle,
            use_container_width=True
        )

        # --------------------------------
        # VOLUME ANALYSIS
        # --------------------------------

        st.subheader("📊 Trading Volume Analysis")

        volume_fig = go.Figure()

        volume_fig.add_trace(
            go.Bar(
                x=df.index,
                y=df["Volume"],
                name="Trading Volume"
            )
        )

        volume_fig.update_layout(
            title="Stock Trading Volume",
            xaxis_title="Date",
            yaxis_title="Volume",
            height=400
        )

        st.plotly_chart(
            volume_fig,
            use_container_width=True
        )

        # --------------------------------
        # RSI ANALYSIS
        # --------------------------------

        st.subheader("📉 RSI Indicator")

        rsi_fig = go.Figure()

        rsi_fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["RSI"],
                mode="lines",
                name="RSI"
            )
        )

        rsi_fig.add_hline(
            y=70,
            line_dash="dash",
            annotation_text="Overbought"
        )

        rsi_fig.add_hline(
            y=30,
            line_dash="dash",
            annotation_text="Oversold"
        )

        rsi_fig.update_layout(
            title="Relative Strength Index",
            yaxis_title="RSI",
            yaxis_range=[0, 100],
            height=400
        )

        st.plotly_chart(
            rsi_fig,
            use_container_width=True
        )

        # --------------------------------
        # TECHNICAL ANALYSIS
        # --------------------------------

        st.subheader("📌 Technical Analysis")

        sma20 = df["SMA20"].iloc[-1]

        sma50 = df["SMA50"].iloc[-1]

        rsi = df["RSI"].iloc[-1]

        col1, col2 = st.columns(2)

        with col1:

            st.write("**Moving Average Analysis**")

            if pd.notna(sma20) and pd.notna(sma50):

                if sma20 > sma50:

                    st.success(
                        "Bullish trend: SMA20 is above SMA50."
                    )

                elif sma20 < sma50:

                    st.warning(
                        "Bearish trend: SMA20 is below SMA50."
                    )

                else:

                    st.info("No clear moving-average trend.")

            else:

                st.info("Insufficient data for moving averages.")

        with col2:

            st.write("**RSI Analysis**")

            if pd.notna(rsi):

                if rsi > 70:

                    st.warning(
                        "RSI indicates potentially overbought conditions."
                    )

                elif rsi < 30:

                    st.success(
                        "RSI indicates potentially oversold conditions."
                    )

                else:

                    st.info(
                        f"RSI is {rsi:.2f}: Neutral range."
                    )

            else:

                st.info("Insufficient data for RSI.")

        # --------------------------------
        # FOOTER
        # --------------------------------

        st.divider()

        st.caption(
            "Stock Market Data Analysis Project | "
            "Python | Streamlit | Yahoo Finance | Pandas | Plotly"
        )

        st.caption(
            "Data may be delayed. Technical indicators are "
            "educational tools, not guaranteed trading advice."
        )

except Exception as e:

    st.error(f"Error loading stock data: {e}")
