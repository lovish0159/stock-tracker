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
    # NSE ke liye tickers mein '^' zaroori hai, par kabhi kabhi yfinance
    # server side par request block karta hai. Hum yahan small timeout try karenge.
    for name, ticker in sectors.items():
        try:
            # auto_adjust=True se price data saaf milta hai
            hist = yf.download(ticker, period="5d", progress=False, auto_adjust=True)
            
            # Agar hist mein multiple columns hain, toh 'Close' ko nikalna padega
            if not hist.empty:
                # hist['Close'] ek Series ho sakta hai, usse value nikalein
                curr_price = float(hist['Close'].iloc[-1])
                prev_price = float(hist['Close'].iloc[0])
                
                pct_change = ((curr_price - prev_price) / prev_price) * 100
                
                data_list.append({
                    "Sector": name,
                    "5-Day Performance (%)": float(round(pct_change, 2))
                })
        except Exception as e:
            st.write(f"Error fetching {name}: {e}")
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
           
