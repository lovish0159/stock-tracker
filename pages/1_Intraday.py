import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time

# --- SECURE CREDENTIALS CONFIG ---
BOT_TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]  
CHAT_ID = "299717233"      
SHEET_URL = "https://docs.google.com/spreadsheets/d/1BHnQm0nYwl3paJ9PUEfHPlzMBLLXdpCZtdC59SFma58/edit?gid=0#gid=0"  # Apni sheet ka link yahan dalein

st.set_page_config(layout="wide")
st.title("🛡️ Institutional Alpha Engine (Triple Confirmation)")
st.subheader("SuperTrend + EMA Crossover + RSI + Volume Spread Scan")

if "auto_scan" not in st.session_state:
    st.session_state.auto_scan = False

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
    # 1. Exponential Moving Averages (EMA 9 and EMA 21)
    df['EMA_9'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['EMA_21'] = df['Close'].ewm(span=21, adjust=False).mean()
    
    # 2. Relative Strength Index (RSI 14)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/14, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14, adjust=False).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # 3. SuperTrend (10, 3) Calculation
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
    
    # 4. Institutional Volume MA Filter
    df['Vol_Avg'] = df['Volume'].rolling(window=20).mean()
    return df

# --- CORE CORE MULTI-SCANNER ---
def execute_alpha_scan():
    sheet = get_google_sheet()
    if not sheet: return
    
    records = sheet.get_all_records()
    df_sheet = pd.DataFrame(records)
    if df_sheet.empty or 'Symbol' not in df_sheet.columns: return
    
    symbols = [str(s).strip() for s in df_sheet['Symbol'].dropna().tolist() if str(s).strip()]
    
    for sym in symbols:
        formatted_sym = sym if (sym.endswith(".NS") or sym.endswith(".BO")) else f"{sym}.NS"
        try:
            # 5-Minute Candle Data download for Intraday Precision
            data = yf.download(formatted_sym, period="3d", interval="5m", progress=False)
            if data.empty: continue
            
            df = calculate_alpha_indicators(data.copy())
            last = df.iloc[-1]
            prev = df.iloc[-2]
            
            close = round(last['Close'], 2)
            rsi = round(last['RSI'], 1)
            vol = int(last['Volume'])
            v_avg = int(last['Vol_Avg'])
            
            # --- TRIPLE CONFIRMATION MATH MATHEMATICS ---
            # 🟢 BUY MATCH: SuperTrend Green + EMA 9 crossed above EMA 21 + RSI is Strong but not Overbought + Huge Volume
            ema_buy = (last['EMA_9'] > last['EMA_21']) and (prev['EMA_9'] <= prev['EMA_21'])
            st_buy = (last['SuperTrend_Dir'] == 1)
            rsi_buy = (rsi >= 50 and rsi <= 68)
            volume_breakout = (vol > v_avg * 1.8) # 1.8x Institutional Volume
            
            # 🔴 SELL MATCH: SuperTrend Red + EMA 9 crossed below EMA 21 + RSI Weak + Big Volume
            ema_sell = (last['EMA_9'] < last['EMA_21']) and (prev['EMA_9'] >= prev['EMA_21'])
            st_sell = (last['SuperTrend_Dir'] == -1)
            rsi_sell = (rsi <= 48 and rsi >= 32)

            # Mathematical Risk-Reward Projections (0.6% SL / 1.5% Target)
            if ema_buy and st_buy and rsi_buy and volume_breakout:
                sl = round(close * 0.994, 2)
                t1 = round(close * 1.012, 2)
                t2 = round(close * 1.025, 2)
                
                msg = f"🟢 ✨ **TRIPLE CONFIRMATION BUY: {sym}** ✨\n\n" \
                      f"💰 Entry Price: ₹{close}\n" \
                      f"📈 RSI Momentum: {rsi} (Perfect)\n" \
                      f"🔥 Volume: {vol:,} (Avg: {v_avg:,} -> 🚀 Institutional Buying!)\n\n" \
                      f"🛡️ StopLoss (0.6%): ₹{sl}\n" \
                      f"🎯 Target 1 (1.2%): ₹{t1}\n" \
                      f"🎯 Target 2 (2.5%): ₹{t2}"
                send_telegram_alert(msg)
                
            elif ema_sell and st_sell and rsi_sell and volume_breakout:
                sl = round(close * 1.006, 2)
                t1 = round(close * 0.988, 2)
                t2 = round(close * 0.975, 2)
                
                msg = f"🔴 ✨ **TRIPLE CONFIRMATION SELL: {sym}** ✨\n\n" \
                      f"💰 Entry Price: ₹{close}\n" \
                      f"📉 RSI Weakness: {rsi}\n" \
                      f"⚠️ Volume: {vol:,} (Avg: {v_avg:,} -> 🚨 Big Block Exit!)\n\n" \
                      f"🛡️ StopLoss (0.6%): ₹{sl}\n" \
                      f"🎯 Target 1 (1.2%): ₹{t1}\n" \
                      f"🎯 Target 2 (2.5%): ₹{t2}"
                send_telegram_alert(msg)
        except:
            continue

# --- AUTOMATION INTERFACE ---
st.sidebar.header("🕹️ Control Dashboard")
if st.sidebar.button("🟢 Start 5-Min Alpha Scanner", type="primary"):
    st.session_state.auto_scan = True
    st.sidebar.success("Triple Confirmation Scanner Active!")

if st.sidebar.button("🔴 Stop Scanner"):
    st.session_state.auto_scan = False
    st.sidebar.warning("Scanner Paused.")

if st.session_state.auto_scan:
    st.info("🔄 **Auto-Pilot Mode Active:** System background mein har 5-minute par data refresh karke scan kar raha hai...")
    with st.spinner("Analyzing Live Volatility Matrices..."):
        execute_alpha_scan()
    st.success("Scan complete! Matrix state holds clean.")
    time.sleep(300)
    st.rerun()
else:
    st.warning("⏸️ Scanner is currently resting. Click 'Start' to wake up the engine.")