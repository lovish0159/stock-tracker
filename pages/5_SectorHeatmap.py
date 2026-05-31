import streamlit as st
import yfinance as yf
import pandas as pd
import requests

st.set_page_config(layout="wide")
st.title("🌡️ Sector Rotation & Market Heatmap")
st.subheader("Smart Money Kahan Ghoom Raha Hai?")

# --- SECTORS TO TRACK ---
sectors = {
    "Nifty Bank": "^NSEBANK",
    "Nifty IT": "^CNXIT",
    "Nifty Pharma": "^CNXPHARMA",
    "Nifty Auto": "^CNXAUTO",
    "Nifty Energy": "^CNXENERGY",
    "Nifty FMCG": "^CNXFMCG",
    "Nifty Metal": "^CNXMETAL"
}

def get_sector_performance():
    data_list = []
    for name, ticker in sectors.items():
        try:
            # Pichle 5 din ka data
            hist = yf.download(ticker, period="5d", progress=False)
            if not hist.empty:
                curr_price = float(hist['Close'].iloc[-1])
                prev_price = float(hist['Close'].iloc[0])
                
                # Percentage change calculation
                pct_change = ((curr_price - prev_price) / prev_price) * 100
                
                # Data list mein saaf numeric values daalein
                data_list.append({
                    "Sector": name, 
                    "5-Day Performance (%)": float(round(pct_change, 2))
                })
                return pd.DataFrame(data_list)
        except Exception:
            continue
            
    return pd.DataFrame(data_list)

# ... (upar ka code waisa hi rehne dein)

if st.button("🌡️ SCAN SECTOR HEATMAP"):
    witif st.button("🌡️ SCAN SECTOR HEATMAP"):
    with st.spinner("Analyzing Sector Money Flow..."):
        df = get_sector_performance()
        
        # 🟢 Yahan check karein ki DataFrame khali toh nahi hai
        if df.empty:
            st.error("Data fetch nahi hua! Tickers ya YFinance connection check karein.")
        
        # 🟢 Check karein ki column naam sahi hai ya nahi
        elif "5-Day Performance (%)" not in df.columns:
            st.error(f"Column nahi mila! Column names ye hain: {df.columns.tolist()}")
            
        else:
            # Ab code safely chalega
            df = df.reset_index(drop=True)
            df = df.sort_values(by="5-Day Performance (%)", ascending=False)
            
            # Display
            st.dataframe(df.style.background_gradient(subset=["5-Day Performance (%)"], cmap="RdYlGn"), 
                         use_container_width=True, hide_index=True)
            
            # Telegram Alert...
