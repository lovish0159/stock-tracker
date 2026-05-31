import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(layout="wide")
st.title("💎 Institutional Master Force Index")
st.subheader("Bade Khiladiyon Ki Taqat (Force) Ko Track Karein")

def calculate_force_index(df):
    # Force Index = Volume * (Current Close - Prev Close)
    # Yeh batata hai ki kitni buying/selling "taqat" se ho rahi hai
    df['Force_Index'] = df['Volume'] * (df['Close'] - df['Close'].shift(1))
    df['Force_EMA'] = df['Force_Index'].ewm(span=13, adjust=False).mean()
    return df

ticker = st.text_input("Stock Symbol (e.g., RELIANCE.NS):", "RELIANCE.NS").upper()

if st.button("🚀 ANALYZE FORCE"):
    data = yf.download(ticker, period="1mo", interval="15m", progress=False)
    df = calculate_force_index(data)
    
    last = df.iloc[-1]
    
    # EXACT LOGIC:
    # Force EMA Positive hai = Buyers Control mein hain
    # Force EMA Negative hai = Sellers Control mein hain
    
    st.metric("Current Force Index", f"{int(last['Force_Index']):,}")
    
    if last['Force_EMA'] > 0:
        st.success("🟢 INSTITUTIONAL BUYING FORCE: Market mein kharidari ka zor hai. Price upar jane ki sambhavna zyada hai.")
    else:
        st.error("🔴 INSTITUTIONAL SELLING FORCE: Market mein bikwali ka zor hai. Price girne ki sambhavna zyada hai.")
        
    st.line_chart(df[['Force_Index', 'Force_EMA']])
