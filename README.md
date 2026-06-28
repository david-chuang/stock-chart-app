# 📈 Stock Price Chart

A simple web app: type a US stock ticker, see its historical closing price.
Built with [Streamlit](https://streamlit.io) + [yfinance](https://pypi.org/project/yfinance/). No API key required.

## Run it on your own computer

1. Install Python 3.9+ (https://www.python.org/downloads/)
2. In a terminal, from this folder:

   ```bash
   pip install -r requirements.txt
   streamlit run app.py
   ```

3. Your browser opens at `http://localhost:8501`.

## Put it online (free, shareable URL)

1. Push this folder to a GitHub repository.
2. Go to https://share.streamlit.io, sign in with GitHub, and click **New app**.
3. Pick your repo, set the main file to `app.py`, and click **Deploy**.
4. You get a public URL you can open from any device.

## Notes

- US stocks only for now (e.g. `AAPL`, `MSFT`, `GLW`).
- Data comes from Yahoo Finance via yfinance — free, but an unofficial feed that can occasionally rate-limit.
- MVP scope: price only. Planned later: moving averages, RSI, compare stocks, CSV/PNG export.
- For personal use. Not investment advice.
