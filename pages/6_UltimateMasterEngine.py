import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(layout="wide")
st.title("💎 Institutional Master Force Index")
st.subheader("Bade Khiladiyon Ki Taqat (Force) Ko Track Karein")

def calculate_force_index(df):
    # Force Index = Volume * (Current Close - Prev Close)
    # Yeh volume aur price change ko multiply karke 'Smart Money Pressure' nikalta hai
    df['Force_Index'] = df['Volume'] * (df['Close'] - df['Close'].shift(1))
    df['Force_EMA'] = df['Force_Index'].ewm(span=13, adjust=False).mean()
    return df

ticker = st.text_input("Stock Symbol (e.g., RELIANCE.NS, ASALCBR.NS, HAL.NS):", "RELIANCE.NS").upper()

if st.button("🚀 ANALYZE FORCE", type="primary"):
    with st.spinner(f"Extracting multi-layered order flows for {ticker}..."):
        try:
            # Fetching 1-month data with 15-minute candles
            data = yf.download(ticker, period="1mo", interval="15m", progress=False)
            
            if data.empty:
                st.warning("⚠️ Is symbol ke liye data nahi mila. Ek baar ticker proper `.NS` suffix ke sath check karein.")
            else:
                # --- MultiIndex Column Flattening Bug Fix ---
                df = pd.DataFrame(index=data.index)
                
                if isinstance(data.columns, pd.MultiIndex):
                    df['Close'] = data['Close'][ticker]
                    df['Volume'] = data['Volume'][ticker]
                else:
                    df['Close'] = data['Close']
                    df['Volume'] = data['Volume']
                
                # Drop rows where data is missing
                df = df.dropna()
                
                # Run institutional logic
                df = calculate_force_index(df)
                df = df.dropna() # Shift(1) ki wajah se pehli row empty hogi use saaf kiya
                
                last_row = df.iloc[-1]
                current_force = float(last_row['Force_Index'])
                current_ema = float(last_row['Force_EMA'])
                
                # --- Metrics Display Panel ---
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Last Candle Force Index", f"{int(current_force):,}")
                with col2:
                    st.metric("Force EMA (13-Period Trend)", f"{int(current_ema):,}")
                
                st.divider()
                
                # --- Core Institutional Logic Alert ---
                if current_ema > 0:
                    st.success("🟢 **INSTITUTIONAL BUYING FORCE:** Buyers control mein hain aur heavy volume ke sath accumulation ho rahi hai. Price upar jane ki sambhavna zyada hai.")
                else:
                    st.error("🔴 **INSTITUTIONAL SELLING FORCE:** Sellers control mein hain. High volume distribution chal rahi hai, price girne ki sambhavna zyada hai.")
                
                # --- Visual Chart Optimization ---
                st.markdown("### 📊 Force Index & 13-EMA Timeline (Last 5 Days Trends)")
                # Poore mahine ke bajaye last 5 days ka graph taaki 15m intervals par lines overlap na karein
                chart_df = df.tail(375)[['Force_Index', 'Force_EMA']] 
                st.line_chart(chart_df, use_container_width=True)
                
        except Exception as e:
            st.error(f"⚠️ Calculation Pipeline Error: {e}")
