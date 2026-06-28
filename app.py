"""
Stock Price Chart — a simple Streamlit app.
Enter a US stock ticker and see its historical closing price.
MVP: price only.
"""

import streamlit as st
import yfinance as yf

# ---- Page setup -------------------------------------------------------------
st.set_page_config(page_title="Stock Price Chart", page_icon="📈", layout="wide")

st.title("📈 Stock Price Chart")
st.caption("Enter a US stock ticker (e.g. AAPL, MSFT, GLW) to see its historical price.")

# ---- Inputs -----------------------------------------------------------------
left, right = st.columns([2, 3])

with left:
    ticker = st.text_input("Ticker symbol", value="AAPL", max_chars=10).strip().upper()

with right:
    period_labels = {"1mo": "1M", "6mo": "6M", "1y": "1Y", "5y": "5Y", "max": "Max"}
    period = st.radio(
        "Time range",
        list(period_labels.keys()),
        index=2,  # default to 1Y
        horizontal=True,
        format_func=lambda x: period_labels[x],
    )


# ---- Data loading (cached for 15 min to be gentle on the data source) -------
@st.cache_data(ttl=900, show_spinner=False)
def load_prices(symbol: str, period: str):
    return yf.Ticker(symbol).history(period=period, auto_adjust=False)


# ---- Render -----------------------------------------------------------------
if not ticker:
    st.info("Type a ticker symbol above to get started.")
    st.stop()

try:
    with st.spinner(f"Loading {ticker}…"):
        data = load_prices(ticker, period)
except Exception as e:
    st.error(f"Couldn't load data for '{ticker}'. The data source may be busy — try again in a moment.")
    st.caption(f"Details: {e}")
    st.stop()

if data is None or data.empty:
    st.error(f"No data found for '{ticker}'. Double-check the symbol (US stocks only) and try again.")
    st.stop()

# Summary metrics
first_close = float(data["Close"].iloc[0])
last_close = float(data["Close"].iloc[-1])
change = last_close - first_close
pct = (change / first_close * 100) if first_close else 0.0

m1, m2, m3 = st.columns(3)
m1.metric("Latest close", f"${last_close:,.2f}")
m2.metric(f"Change ({period_labels[period]})", f"${change:,.2f}", f"{pct:+.2f}%")
m3.metric("Trading days shown", f"{len(data):,}")

# Price chart
st.subheader(f"{ticker} — closing price")
st.line_chart(data["Close"], height=440, use_container_width=True)

# Optional raw data
with st.expander("Show raw data"):
    st.dataframe(
        data[["Open", "High", "Low", "Close", "Volume"]].sort_index(ascending=False),
        use_container_width=True,
    )

st.caption("Data: Yahoo Finance via yfinance. For personal use. Not investment advice.")
