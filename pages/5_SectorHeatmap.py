import streamlit as st
import yfinance as yf
import pandas as pd
import requests

st.set_page_config(layout="wide")
st.title("🌡️ Sector Rotation & Market Heatmap")
st.subheader("Smart Money Kahan Ghoom Raha Hai?")

# --- SECTORS TO TRACK (Standard Indices + Lovish Custom Focused Baskets) ---
sectors = {
    "Nifty Bank": "^NSEBANK",
    "Nifty IT": "^CNXIT",
    "Nifty Pharma": "^CNXPHARMA",
    "Nifty Auto": "^CNXAUTO",
    "Nifty Energy": "^CNXENERGY",
    "Nifty FMCG": "^CNXFMCG",
    "Nifty Metal": "^CNXMETAL",
    "Defense Sector (Lovish Track)": "BEL.NS,HAL.NS,BDL.NS,MAZDOCK.NS", # Custom basket for Defense
    "Brewery & Spirits (Lovish Track)": "MCDOWELL-N.NS,UNIENT.NS,RADICO.NS,ASALCBR.NS" # Custom basket for Brewery
}

def get_sector_performance():
    data_list = []
    with st.spinner("Fetching Live Market Data..."):
        for name, ticker in sectors.items():
            try:
                # 5-day history for momentum tracking
                hist = yf.download(ticker, period="5d", progress=False, group_by='column')
                
                if hist.empty:
                    continue
                    
                # Fix for MultiIndex columns formatting in latest yfinance
                if 'Close' in hist.columns:
                    close_data = hist['Close']
                    # Agar list of stocks hai (Custom Basket), toh unka average nikalenge
                    if isinstance(close_data, pd.DataFrame):
                        curr_series = close_data.iloc[-1].dropna()
                        prev_series = close_data.iloc[0].dropna()
                        
                        # Calculate pct change for each stock then average it
                        pct_changes = ((curr_series - prev_series) / prev_series) * 100
                        pct_change = pct_changes.mean()
                    else:
                        # Single index ticker configuration
                        curr_price = float(close_data.iloc[-1])
                        prev_price = float(close_data.iloc[0])
                        pct_change = ((curr_price - prev_price) / prev_price) * 100
                        
                    data_list.append({
                        "Sector": name, 
                        "5-Day Performance (%)": round(pct_change, 2)
                    })
            except Exception as e:
                # Graceful bypass to keep the core loop crash-free
                pass
                
    return pd.DataFrame(data_list)

if st.button("🌡️ SCAN SECTOR HEATMAP", type="primary"):
    df = get_sector_performance()
    
    if not df.empty:
        df = df.sort_values(by="5-Day Performance (%)", ascending=False)
        
        # Color coding configuration (Green for Bullish, Red for Bearish)
        st.dataframe(
            df.style.background_gradient(subset=["5-Day Performance (%)"], cmap="RdYlGn", vmin=-5.0, vmax=5.0), 
            use_container_width=True, 
            hide_index=True
        )
        
        # Top Performer Insights
        top_sector = df.iloc[0]
        if top_sector['5-Day Performance (%)'] > 0:
            msg = f"🌡️ **SECTOR HOTSPOT**: {top_sector['Sector']} sabse strong perform kar raha hai ({top_sector['5-Day Performance (%)']}%)"
            st.success(msg)
            
            # If momentum triggers above 3.0%, dispatch Telegram automated log
            if top_sector['5-Day Performance (%)'] > 3.0:
                try:
                    BOT_TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]
                    CHAT_ID = "299717233"
                    requests.post(
                        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                        json={"chat_id": CHAT_ID, "text": f"🔥 {msg} - Yahan ke stocks mein momentum check karein!"},
                        timeout=10
                    )
                    st.toast("📡 Telegram alert dispatched successfully!")
                except:
                    pass
    else:
        st.warning("⚠️ Data fetch failed. Market off-hours ya network check kijiye.")
