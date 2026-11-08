
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

from datetime import datetime

# ==========================================
# PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="StockVision | Analytics",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# CUSTOM PROFESSIONAL CSS
# ==========================================

st.markdown("""
<style>
    .stApp {
        background-color: #0b1120;
        color: #f1f5f9;
    }

    [data-testid="stSidebar"] {
        background-color: #111827;
    }

    [data-testid="stMetric"] {
        background-color: #172338;
        padding: 18px;
        border: 1px solid #26364f;
        border-radius: 12px;
    }

    [data-testid="stMetricLabel"] {
        color: #94a3b8;
    }

    [data-testid="stMetricValue"] {
        color: #f8fafc;
    }

    .main-title {
        font-size: 32px;
        font-weight: 750;
        color: #f8fafc;
    }

    .subtitle {
        color: #94a3b8;
        font-size: 14px;
    }

    .section-title {
        color: #e2e8f0;
        font-size: 21px;
        font-weight: 650;
    }

    div[data-testid="stTabs"] button {
        color: #cbd5e1;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# STOCK DATABASE
# ==========================================

stocks = {
    "Apple": "AAPL",
    "Microsoft": "MSFT",
    "Google": "GOOGL",
    "Amazon": "AMZN",
    "Tesla": "TSLA",
    "NVIDIA": "NVDA",
    "Meta": "META",
    "Netflix": "NFLX",
    "Reliance": "RELIANCE.NS",
    "TCS": "TCS.NS",
    "Infosys": "INFY.NS",
    "HDFC Bank": "HDFCBANK.NS"
}

# ==========================================
# SIDEBAR
# ==========================================

st.sidebar.title("📈 StockVision")

st.sidebar.caption("Professional Market Analytics")

st.sidebar.divider()

st.sidebar.subheader("Market Settings")

selected_stock = st.sidebar.selectbox(
    "Choose Stock",
    list(stocks.keys())
)

ticker = stocks[selected_stock]

period = st.sidebar.selectbox(
    "Analysis Period",
    ["1d", "5d", "1mo", "3mo", "6mo", "1y"],
    index=2
)

intervals = {
    "1d": "1m",
    "5d": "5m",
    "1mo": "30m",
    "3mo": "1d",
    "6mo": "1d",
    "1y": "1d"
}

interval = intervals[period]

refresh_seconds = st.sidebar.selectbox(
    "Dashboard Refresh",
    [30, 60, 300],
    index=1,
    format_func=lambda x: f"{x} seconds"
)

currency = "₹" if ticker.endswith(".NS") else "$"

st.sidebar.divider()

st.sidebar.info(
    f"Selected: {ticker}\n\n"
    f"Period: {period}\n\n"
    f"Currency: {currency}"
)

st.sidebar.caption(
    "Data provider: Yahoo Finance"
)

# ==========================================
# AUTOMATIC REFRESH
# ==========================================

count = st_autorefresh(
    interval=refresh_seconds * 1000,
    key="stockvision_refresh"
)

# ==========================================
# HEADER
# ==========================================

col1, col2 = st.columns([3, 1])

with col1:
    st.markdown(
        '<div class="main-title">📈 StockVision Analytics</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<div class="subtitle">'
        'Professional Stock Market Monitoring & Analysis'
        '</div>',
        unsafe_allow_html=True
    )

with col2:
    st.metric("Refresh Count", count)

st.divider()

# ==========================================
# FETCH STOCK DATA
# ==========================================

@st.cache_data(ttl=45)
def fetch_stock_data(symbol, selected_period, selected_interval):
    stock = yf.Ticker(symbol)

    data = stock.history(
        period=selected_period,
        interval=selected_interval,
        auto_adjust=True
    )

    return data


try:
    with st.spinner("Fetching stock market data..."):

        df = fetch_stock_data(
            ticker,
            period,
            interval
        )

    if df.empty:
        st.error("No stock data available. Please try another period.")
        st.stop()

    # ======================================
    # DATA CLEANING
    # ======================================

    required_columns = ["Open", "High", "Low", "Close", "Volume"]

    df = df.dropna(subset=required_columns).copy()

    if df.empty:
        st.error("No valid stock prices found.")
        st.stop()

    # ======================================
    # TECHNICAL INDICATORS
    # ======================================

    df["SMA20"] = df["Close"].rolling(
        window=20,
        min_periods=20
    ).mean()

    df["SMA50"] = df["Close"].rolling(
        window=50,
        min_periods=50
    ).mean()

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

    # Handle periods with gains but no losses
    df.loc[
        (avg_loss == 0) & (avg_gain > 0),
        "RSI"
    ] = 100

    df.loc[
        (avg_gain == 0) & (avg_loss > 0),
        "RSI"
    ] = 0

    # ======================================
    # PRICE CALCULATIONS
    # ======================================

    current_price = float(df["Close"].iloc[-1])

    previous_price = (
        float(df["Close"].iloc[-2])
        if len(df) > 1
        else current_price
    )

    price_change = current_price - previous_price

    percent_change = (
        price_change / previous_price * 100
        if previous_price != 0 else 0
    )

    day_high = float(df["High"].iloc[-1])
    day_low = float(df["Low"].iloc[-1])

    latest_volume = int(df["Volume"].iloc[-1])

    # ======================================
    # STOCK HEADER
    # ======================================

    st.markdown(
        f'<div class="section-title">'
        f'{selected_stock} ({ticker})'
        f'</div>',
        unsafe_allow_html=True
    )

    st.caption(
        f"Latest available data: "
        f"{df.index[-1].strftime('%d %b %Y, %H:%M')}"
    )

    # ======================================
    # KPI CARDS
    # ======================================

    st.subheader("Market Overview")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Latest Price",
        f"{currency}{current_price:,.2f}",
        f"{percent_change:+.2f}%"
    )

    c2.metric(
        "Price Change",
        f"{currency}{price_change:,.2f}"
    )

    c3.metric(
        "Latest High",
        f"{currency}{day_high:,.2f}"
    )

    c4.metric(
        "Trading Volume",
        f"{latest_volume:,}"
    )

    st.divider()

    # ======================================
    # NAVIGATION TABS
    # ======================================

    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Price Analysis",
        "🕯️ Candlestick",
        "📉 Technical Indicators",
        "📋 Data & Download"
    ])

    # ======================================
    # TAB 1: PRICE ANALYSIS
    # ======================================

    with tab1:

        st.subheader("Stock Price Performance")

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["Close"],
                name="Closing Price",
                line=dict(width=2)
            )
        )

        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["SMA20"],
                name="SMA 20",
                line=dict(dash="dot")
            )
        )

        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["SMA50"],
                name="SMA 50",
                line=dict(dash="dash")
            )
        )

        fig.update_layout(
            template="plotly_dark",
            height=500,
            hovermode="x unified",
            xaxis_title="Date",
            yaxis_title=f"Price ({currency})",
            margin=dict(l=20, r=20, t=40, b=20),
            legend=dict(
                orientation="h",
                y=1.1
            )
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        st.subheader("Trading Volume")

        volume_fig = go.Figure()

        volume_fig.add_trace(
            go.Bar(
                x=df.index,
                y=df["Volume"],
                name="Volume"
            )
        )

        volume_fig.update_layout(
            template="plotly_dark",
            height=350,
            xaxis_title="Date",
            yaxis_title="Volume"
        )

        st.plotly_chart(
            volume_fig,
            use_container_width=True
        )

    # ======================================
    # TAB 2: CANDLESTICK
    # ======================================

    with tab2:

        st.subheader("Candlestick Analysis")

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
            template="plotly_dark",
            height=600,
            xaxis_title="Date",
            yaxis_title=f"Price ({currency})",
            xaxis_rangeslider_visible=False
        )

        st.plotly_chart(
            candle,
            use_container_width=True
        )

    # ======================================
    # TAB 3: TECHNICAL INDICATORS
    # ======================================

    with tab3:

        st.subheader("Relative Strength Index")

        rsi_fig = go.Figure()

        rsi_fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["RSI"],
                name="RSI",
                line=dict(width=2)
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
            template="plotly_dark",
            height=400,
            yaxis_range=[0, 100],
            yaxis_title="RSI"
        )

        st.plotly_chart(
            rsi_fig,
            use_container_width=True
        )

        st.divider()

        st.subheader("Technical Analysis Summary")

        sma20 = df["SMA20"].iloc[-1]
        sma50 = df["SMA50"].iloc[-1]
        rsi = df["RSI"].iloc[-1]

        col1, col2 = st.columns(2)

        with col1:

            st.markdown("**Moving Average Analysis**")

            if pd.notna(sma20) and pd.notna(sma50):

                if sma20 > sma50:
                    st.success(
                        "Bullish moving-average trend"
                    )

                elif sma20 < sma50:
                    st.warning(
                        "Bearish moving-average trend"
                    )

                else:
                    st.info("No clear moving-average trend")

            else:
                st.info("Insufficient data for SMA analysis")

        with col2:

            st.markdown("**RSI Analysis**")

            if pd.notna(rsi):

                if rsi > 70:
                    st.warning(
                        f"RSI: {rsi:.2f} - Potentially overbought"
                    )

                elif rsi < 30:
                    st.success(
                        f"RSI: {rsi:.2f} - Potentially oversold"
                    )

                else:
                    st.info(
                        f"RSI: {rsi:.2f} - Neutral range"
                    )

            else:
                st.info("Insufficient data for RSI analysis")

    # ======================================
    # TAB 4: DATA AND DOWNLOAD
    # ======================================

    with tab4:

        st.subheader("Historical Stock Data")

        display_columns = [
            "Open",
            "High",
            "Low",
            "Close",
            "Volume",
            "SMA20",
            "SMA50",
            "RSI"
        ]

        st.dataframe(
            df[display_columns].sort_index(
                ascending=False
            ),
            use_container_width=True
        )

        csv_data = df.to_csv().encode("utf-8")

        st.download_button(
            label="⬇️ Download Stock Data CSV",
            data=csv_data,
            file_name=f"{ticker}_stock_analysis.csv",
            mime="text/csv"
        )

    # ======================================
    # FOOTER
    # ======================================

    st.divider()

    st.caption(
        "StockVision Analytics | Python | Streamlit | "
        "Yahoo Finance | Pandas | Plotly"
    )

    st.caption(
        "Market data may be delayed or unavailable. "
        "Technical indicators are educational tools, "
        "not investment recommendations."
    )

except Exception as e:

    st.error(f"Unable to load stock data: {e}")

    st.info(
        "Check your internet connection, selected stock, "
        "and Yahoo Finance data availability."
    )
