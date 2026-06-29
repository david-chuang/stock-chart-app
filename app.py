"""
Stock Price Chart — a simple Streamlit app.
Enter a US stock ticker and see its closing price with moving averages, plus a 14-day RSI.
"""

import altair as alt
import pandas as pd
import streamlit as st
import yfinance as yf

# ---- Page setup -------------------------------------------------------------
st.set_page_config(page_title="Stock Price Chart", page_icon="📈", layout="wide")

st.title("📈 Stock Price Chart")
st.caption("Enter a US stock ticker (e.g. AAPL, MSFT, GLW) to see its price, moving averages and RSI.")

# Map each display range to: button label, how much history to FETCH (extra is
# warm-up so indicators are correct from the first visible day), and days to DISPLAY.
PERIODS = {
    "1mo": {"label": "1M", "fetch": "1y", "days": 31},
    "6mo": {"label": "6M", "fetch": "2y", "days": 186},
    "1y": {"label": "1Y", "fetch": "2y", "days": 366},
    "5y": {"label": "5Y", "fetch": "10y", "days": 366 * 5 + 5},
    "max": {"label": "Max", "fetch": "max", "days": None},
}

# Moving averages: column name -> (window in trading days, legend label)
MAS = {
    "MA5": (5, "5-day"),
    "MA10": (10, "10-day"),
    "MA21": (21, "Monthly (21d)"),
    "MA63": (63, "Quarterly (63d)"),
}

# ---- Inputs -----------------------------------------------------------------
left, right = st.columns([2, 3])

with left:
    ticker = st.text_input("Ticker symbol", value="AAPL", max_chars=10).strip().upper()

with right:
    period = st.radio(
        "Time range",
        list(PERIODS.keys()),
        index=2,  # default to 1Y
        horizontal=True,
        format_func=lambda x: PERIODS[x]["label"],
    )


# ---- Helpers ----------------------------------------------------------------
@st.cache_data(ttl=900, show_spinner=False)
def load_prices(symbol: str, fetch_period: str):
    return yf.Ticker(symbol).history(period=fetch_period, auto_adjust=False)


def rsi(series: pd.Series, length: int = 14) -> pd.Series:
    """14-day RSI using Wilder's smoothing."""
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / length, min_periods=length, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / length, min_periods=length, adjust=False).mean()
    rs = avg_gain / avg_loss
    return 100 - 100 / (1 + rs)


# ---- Render -----------------------------------------------------------------
if not ticker:
    st.info("Type a ticker symbol above to get started.")
    st.stop()

cfg = PERIODS[period]

try:
    with st.spinner(f"Loading {ticker}…"):
        data = load_prices(ticker, cfg["fetch"])
except Exception as e:
    st.error(f"Couldn't load data for '{ticker}'. The data source may be busy — try again in a moment.")
    st.caption(f"Details: {e}")
    st.stop()

if data is None or data.empty:
    st.error(f"No data found for '{ticker}'. Double-check the symbol (US stocks only) and try again.")
    st.stop()

# Drop rows with no close (e.g. the current, unfinished trading day)
data = data.dropna(subset=["Close"])
if data.empty:
    st.error(f"No usable price data for '{ticker}' yet. Try again shortly.")
    st.stop()

# Compute indicators on the full (warm-up included) series, then trim to window.
data["RSI"] = rsi(data["Close"])
for col, (window, _label) in MAS.items():
    data[col] = data["Close"].rolling(window).mean()

if cfg["days"] is not None:
    cutoff = data.index.max() - pd.Timedelta(days=cfg["days"])
    view = data[data.index >= cutoff]
else:
    view = data

# Summary metrics
first_close = float(view["Close"].iloc[0])
last_close = float(view["Close"].iloc[-1])
change = last_close - first_close
pct = (change / first_close * 100) if first_close else 0.0
last_rsi = float(view["RSI"].iloc[-1])
rsi_state = "Overbought" if last_rsi >= 70 else "Oversold" if last_rsi <= 30 else "Neutral"

m1, m2, m3, m4 = st.columns(4)
m1.metric("Latest close", f"${last_close:,.2f}")
m2.metric(f"Change ({cfg['label']})", f"${change:,.2f}", f"{pct:+.2f}%")
m3.metric("RSI (14)", f"{last_rsi:.1f}", rsi_state)
m4.metric("Trading days shown", f"{len(view):,}")

# Which moving averages to show
all_labels = [label for _, (_w, label) in MAS.items()]
chosen = st.multiselect("Moving averages to overlay", all_labels, default=all_labels)

# ---- Price chart with moving averages ---------------------------------------
st.subheader(f"{ticker} — closing price")

date_col = view.reset_index().columns[0]  # 'Date' or 'Datetime'
series_order = ["Close"] + [label for _, (_w, label) in MAS.items() if label in chosen]
color_map = {
    "Close": "#0f172a",
    "5-day": "#f59e0b",
    "10-day": "#3b82f6",
    "Monthly (21d)": "#8b5cf6",
    "Quarterly (63d)": "#10b981",
}

# Build a tidy (long) frame with only the selected series.
keep = {"Close": "Close"}
for _col, (_w, label) in MAS.items():
    if label in chosen:
        keep[_col] = label
price_df = view.reset_index()[[date_col] + list(keep.keys())].rename(columns=keep)
long_df = price_df.melt(id_vars=date_col, var_name="Series", value_name="Price").dropna(subset=["Price"])

price_chart = (
    alt.Chart(long_df)
    .mark_line()
    .encode(
        x=alt.X(f"{date_col}:T", title=None),
        y=alt.Y("Price:Q", title="Price ($)", scale=alt.Scale(zero=False)),
        color=alt.Color(
            "Series:N",
            scale=alt.Scale(domain=series_order, range=[color_map[s] for s in series_order]),
            sort=series_order,
            legend=alt.Legend(title=None, orient="top"),
        ),
        size=alt.condition(alt.datum.Series == "Close", alt.value(2.4), alt.value(1.3)),
        tooltip=[
            alt.Tooltip(f"{date_col}:T", title="Date"),
            alt.Tooltip("Series:N", title="Series"),
            alt.Tooltip("Price:Q", title="Price", format="$.2f"),
        ],
    )
    .properties(height=420)
)
st.altair_chart(price_chart, use_container_width=True)

# ---- RSI chart (0–100 scale with 70 / 30 guide lines) -----------------------
st.subheader("Relative Strength Index (RSI 14)")
rsi_df = view.reset_index()
rsi_line = (
    alt.Chart(rsi_df)
    .mark_line(color="#7c3aed")
    .encode(
        x=alt.X(f"{date_col}:T", title=None),
        y=alt.Y("RSI:Q", scale=alt.Scale(domain=[0, 100]), title="RSI"),
        tooltip=[alt.Tooltip(f"{date_col}:T", title="Date"), alt.Tooltip("RSI:Q", format=".1f")],
    )
)
overbought = alt.Chart(pd.DataFrame({"y": [70]})).mark_rule(color="#ef4444", strokeDash=[4, 4]).encode(y="y")
oversold = alt.Chart(pd.DataFrame({"y": [30]})).mark_rule(color="#22c55e", strokeDash=[4, 4]).encode(y="y")
st.altair_chart((rsi_line + overbought + oversold).properties(height=220), use_container_width=True)
st.caption("RSI above 70 = potentially overbought; below 30 = potentially oversold.")

# ---- Optional raw data ------------------------------------------------------
with st.expander("Show raw data"):
    cols = ["Open", "High", "Low", "Close", "Volume", "RSI"] + list(MAS.keys())
    st.dataframe(view[cols].sort_index(ascending=False), use_container_width=True)

st.caption("Data: Yahoo Finance via yfinance. For personal use. Not investment advice.")
