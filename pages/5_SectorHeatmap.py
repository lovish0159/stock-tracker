import streamlit as st
import yfinance as yf
import pandas as pd
import requests

# Sector Tickers (Ensure these are correct)
sectors = {
    "Nifty Bank": "^NSEBANK",
    "Nifty IT": "^CNXIT",
    "Nifty Pharma": "^CNXPHARMA",
    "Nifty Auto": "^CNXAUTO"
}

def get_sector_performance():
    data_list = []
    for name, ticker in sectors.items():
        try:
            hist = yf.download(ticker, period="5d", progress=False)
            if not hist.empty:
                curr_price = float(hist['Close'].iloc[-1])
                prev_price = float(hist['Close'].iloc[0])
                pct_change = ((curr_price - prev_price) / prev_price) * 100
                data_list.append({
                    "Sector": name,
                    "5-Day Performance (%)": float(round(pct_change, 2))
                })
        except Exception:
            continue
    return pd.DataFrame(data_list)

# Main UI
st.title("🌡️ Sector Heatmap")

if st.button("🌡️ SCAN SECTOR HEATMAP"):
    with st.spinner("Analyzing Sector Money Flow..."):
        df = get_sector_performance()
        
        if df.empty:
            st.error("Data fetch nahi hua! Tickers check karein.")
        else:
            # Clean data
            df = df.reset_index(drop=True)
            df = df.sort_values(by="5-Day Performance (%)", ascending=False)
            
            # Display
            st.dataframe(df.style.background_gradient(subset=["5-Day Performance (%)"], cmap="RdYlGn"), 
                         use_container_width=True, hide_index=True)
            
            # Telegram Alert
            top_sector = df.iloc[0]
            if top_sector['5-Day Performance (%)'] > 0:
                msg = f"🌡️ {top_sector['Sector']} is strong ({top_sector['5-Day Performance (%)']}%)"
                st.success(msg)
           
