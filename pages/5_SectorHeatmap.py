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
        # Pichle 5 din ka data taaki trend pata chale
        hist = yf.download(ticker, period="5d", progress=False)
        if not hist.empty:
            curr_price = hist['Close'].iloc[-1]
            prev_price = hist['Close'].iloc[0]
            pct_change = ((curr_price - prev_price) / prev_price) * 100
            data_list.append({"Sector": name, "5-Day Performance (%)": round(pct_change, 2)})
    return pd.DataFrame(data_list)

# ... (upar ka code waisa hi rehne dein)

if st.button("🌡️ SCAN SECTOR HEATMAP"):
    with st.spinner("Analyzing Sector Money Flow..."):
        df = get_sector_performance()
        
        # 1. Index reset karein taaki table clean ho
        df = df.reset_index(drop=True)
        
        # 2. BULLETPROOF NUMERIC CONVERSION
        # errors='coerce' ka matlab hai: agar koi value number nahi hai, toh use NaN bana do
        df["5-Day Performance (%)"] = pd.to_numeric(df["5-Day Performance (%)"], errors='coerce')
        
        # 3. Sirf wahi rows rakhein jo valid numbers hain (NaN hatayein)
        df = df.dropna(subset=["5-Day Performance (%)"])
        
        # 4. Ab sort karein
        df = df.sort_values(by="5-Day Performance (%)", ascending=False)
        
        # Display the result
        if not df.empty:
            st.dataframe(df.style.background_gradient(subset=["5-Day Performance (%)"], cmap="RdYlGn"), 
                         use_container_width=True, hide_index=True)
            
            # Telegram Alert Logic
            top_sector = df.iloc[0]
            if top_sector['5-Day Performance (%)'] > 0:
                msg = f"🌡️ **SECTOR HOTSPOT**: {top_sector['Sector']} is strong ({top_sector['5-Day Performance (%)']:.2f}%)"
                st.success(msg)
                
                if top_sector['5-Day Performance (%)'] > 3.0:
                    BOT_TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]
                    CHAT_ID = "299717233"
                    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                                  json={"chat_id": CHAT_ID, "text": f"🔥 {msg} - Check stocks now!"})
        else:
            st.warning("Data fetch hua lekin numeric format mein nahi mila. Check your yfinance connection.")
