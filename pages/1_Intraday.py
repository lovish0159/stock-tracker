import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# --- SECURE CREDENTIALS CONFIG ---
BOT_TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]  
CHAT_ID = "299717233"      
SHEET_URL = "https://docs.google.com/spreadsheets/d/1BHnQm0nYwl3paJ9PUEfHPlzMBLLXdpCZtdC59SFma58/edit?gid=0#gid=0"

st.set_page_config(layout="wide")
st.title("🛡️ Institutional Alpha Engine (Triple Confirmation)")
st.subheader("SuperTrend + EMA Crossover + RSI + Volume Spread Scan")

# --- GOOGLE SHEETS CONNECTION ---
def get_google_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_url(SHEET_URL).sheet1
        return sheet
    except Exception as e:
        st.error(f"⚠️ Sheet Connection Error: {e}")
        return None

# --- TELEGRAM ALERTS ENGINE ---
def send_telegram_alert(message):
    if not message: return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try: 
        requests.post(url, json={"chat_id": CHAT_ID, "text": message}, timeout=15)
    except: 
        pass

# --- QUANT MATHEMATICAL ENGINE ---
def calculate_alpha_indicators(df):
    df['EMA_9'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['EMA_21'] = df['Close'].ewm(span=21, adjust=False).mean()
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/14, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14, adjust=False).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    atr = true_range.ewm(alpha=1/10, adjust=False).mean()

    hl2 = (df['High'] + df['Low']) / 2
    final_upperband = hl2 + (3.0 * atr)
    final_lowerband = hl2 - (3.0 * atr)
    
    supertrend = np.zeros(len(df))
    direction = np.ones(len(df))

    for i in range(1, len(df)):
        if df['Close'].iloc[i] > final_upperband.iloc[i-1]:
            direction[i] = 1
        elif df['Close'].iloc[i] < final_lowerband.iloc[i-1]:
            direction[i] = -1
        else:
            direction[i] = direction[i-1]
            if direction[i] == 1 and final_lowerband.iloc[i] < final_lowerband.iloc[i-1]:
                final_lowerband.values[i] = final_lowerband.iloc[i-1]
            elif direction[i] == -1 and final_upperband.iloc[i] > final_upperband.iloc[i-1]:
                final_upperband.values[i] = final_upperband.iloc[i-1]

    df['SuperTrend_Dir'] = direction
    df['Vol_Avg'] = df['Volume'].rolling(window=20).mean()
    return df

# --- CORE MULTI-SCANNER COMPILER ---
def execute_alpha_scan():
    sheet = get_google_sheet()
    if not sheet: return None, None
    
    records = sheet.get_all_records()
    df_sheet = pd.DataFrame(records)
    if df_sheet.empty or 'Symbol' not in df_sheet.columns: return None, None
    
    symbols = [str(s).strip() for s in df_sheet['Symbol'].dropna().tolist() if str(s).strip()]
    
    screen_results = []
    tele_reports = []
    
    for sym in symbols:
        formatted_sym = sym if (sym.endswith(".NS") or sym.endswith(".BO")) else f"{sym}.NS"
        try:
            data = yf.download(formatted_sym, period="5d", interval="5m", progress=False)
            if data.empty: continue
            
            # MultiIndex Structure Flattening 
            clean_df = pd.DataFrame(index=data.index)
            if isinstance(data.columns, pd.MultiIndex):
                clean_df['High'] = data['High'][formatted_sym]
                clean_df['Low'] = data['Low'][formatted_sym]
                clean_df['Close'] = data['Close'][formatted_sym]
                clean_df['Volume'] = data['Volume'][formatted_sym]
            else:
                clean_df['High'] = data['High']
                clean_df['Low'] = data['Low']
                clean_df['Close'] = data['Close']
                clean_df['Volume'] = data['Volume']
                
            clean_df = clean_df.dropna()
            
            if len(clean_df) > 25:
                df = calculate_alpha_indicators(clean_df)
                last = df.iloc[-1]
                prev = df.iloc[-2]
                
                close = round(float(last['Close']), 2)
                rsi = round(float(last['RSI']), 1) if not pd.isna(last['RSI']) else 50.0
                vol = int(last['Volume'])
                v_avg = int(last['Vol_Avg']) if not pd.isna(last['Vol_Avg']) else 1
                
                vol_mult = round(vol / v_avg, 1) if v_avg > 0 else 1.0
                
                # --- TRIPLE CONFIRMATION MATH LOGIC ---
                ema_buy = (last['EMA_9'] > last['EMA_21']) and (prev['EMA_9'] <= prev['EMA_21'])
                st_buy = (last['SuperTrend_Dir'] == 1)
                rsi_buy = (50 <= rsi <= 68)
                volume_breakout = (vol > v_avg * 1.8)
                
                ema_sell = (last['EMA_9'] < last['EMA_21']) and (prev['EMA_9'] >= prev['EMA_21'])
                st_sell = (last['SuperTrend_Dir'] == -1)
                rsi_sell = (32 <= rsi <= 48)

                verdict = "🟢 SuperTrend Bullish" if st_buy else "🔴 SuperTrend Bearish"
                    
                if ema_buy and st_buy and rsi_buy and volume_breakout:
                    verdict = "🚀 TRIPLE BUY BREAKOUT"
                    sl = round(close * 0.994, 2)
                    t1 = round(close * 1.012, 2)
                    t2 = round(close * 1.025, 2)
                    report = f"🟢 **TRIPLE BUY MATCH: {sym}** ⚡\n\nPrice: ₹{close}\nRSI: {rsi}\nVol: {vol_mult}x\n\n🛑 SL: ₹{sl}\n🎯 T1: ₹{t1} | T2: ₹{t2}"
                    tele_reports.append(report)
                    
                elif ema_sell and st_sell and rsi_sell and volume_breakout:
                    verdict = "📉 TRIPLE SHORT BREAKOUT"
                    sl = round(close * 1.006, 2)
                    t1 = round(close * 0.988, 2)
                    t2 = round(close * 0.975, 2)
                    report = f"🔴 **TRIPLE SHORT MATCH: {sym}** ⚡\n\nPrice: ₹{close}\nRSI: {rsi}\nVol: {vol_mult
