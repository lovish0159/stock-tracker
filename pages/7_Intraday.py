import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time

# --- CONFIGURATION ---
BOT_TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]  
CHAT_ID = "299717233"      
SHEET_URL = "https://docs.google.com/spreadsheets/d/1BHnQm0nYwl3paJ9PUEfHPlzMBLLXdpCZtdC59SFma58/edit?gid=0#gid=0"  # Apni sheet ka link yahan dalein

st.set_page_config(layout="wide")
st.title("🤖 5-Min Auto-Pilot Intraday Engine")
st.subheader("SuperTrend + RSI + Volume Automatic Telegram Scanner")

# --- INITIALIZE STATE FOR AUTO-RUN ---
if "auto_scan" not in st.session_state:
    st.session_state.auto_scan = False

# --- GOOGLE SHEETS CORE CONNECT ---
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

# --- TELEGRAM SENDER ---
def send_telegram_alert(message):
    if not message: return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try: 
        requests.post(url, json={"chat_id": CHAT_ID, "text": message}, timeout=15)
    except: 
        pass

# --- TECHNICAL ALGORITHM ENGINE ---
def calculate_indicators(df):
    rsi_period = 14
    st_period = 10
    st_multiplier = 3.0
    
    # 1. RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/rsi_period, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/rsi_period, adjust=False).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # 2. SuperTrend Math
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    atr = true_range.ewm(alpha=1/st_period, adjust=False).mean()

    hl2 = (df['High'] + df['Low']) / 2
    final_upperband = hl2 + (st_multiplier * atr)
    final_lowerband = hl2 - (st_multiplier * atr)
    
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

# --- SCANNER RUN ACTION ---
def run_full_scan():
    sheet = get_google_sheet()
    if not sheet: return
    
    records = sheet.get_all_records()
    df_sheet = pd.DataFrame(records)
    if df_sheet.empty or 'Symbol' not in df_sheet.columns: return
    
    symbols = [str(s).strip() for s in df_sheet['Symbol'].dropna().tolist() if str(s).strip()]
    telegram_alerts = []
    
    for sym in symbols:
        formatted_sym = sym if (sym.endswith(".NS") or sym.endswith(".BO")) else f"{sym}.NS"
        try:
            data = yf.download(formatted_sym, period="3d", interval="5m", progress=False)
            if data.empty: continue
            
            df_indicators = calculate_indicators(data.copy())
            last_row = df_indicators.iloc[-1]
            prev_row = df_indicators.iloc[-2]
            
            live_price = round(last_row['Close'], 2)
            current_rsi = round(last_row['RSI'], 1)
            current_vol = int(last_row['Volume'])
            avg_vol = int(last_row['Vol_Avg'])
            
            # Volume formatting for easy reading
            vol_text = f"📊 Volume: {current_vol:,} (Avg 20-MA: {avg_vol:,})"
            vol_ratio = current_vol / avg_vol if avg_vol > 0 else 1.0
            
            buy_signal = (last_row['SuperTrend_Dir'] == 1 and prev_row['SuperTrend_Dir'] == -1) and (current_rsi > 48 and current_rsi < 70)
            sell_signal = (last_row['SuperTrend_Dir'] == -1 and prev_row['SuperTrend_Dir'] == 1) and (current_rsi < 52 and current_rsi > 30)
            
            if buy_signal:
                sl = round(live_price * 0.992, 2)
                t1 = round(live_price * 1.01, 2)
                t2 = round(live_price * 1.02, 2)
                
                msg = f"🔥 **TRENDING BUY CALL: {sym}** 🚀\n💰 Price: ₹{live_price}\n📈 RSI: {current_rsi}\n{vol_text}\n\n🛡️ StopLoss: ₹{sl}\n🎯 Target 1 (1%): ₹{t1}\n🎯 Target 2 (2%): ₹{t2}"
                if vol_ratio >= 1.5: msg += "\n💥 HIGH VOLUME BREAKOUT DETECTED!"
                telegram_alerts.append(msg)
                
            elif sell_signal:
                sl = round(live_price * 1.008, 2)
                t1 = round(live_price * 0.99, 2)
                t2 = round(live_price * 0.98, 2)
                
                msg = f"💥 **TRENDING SELL CALL: {sym}** 🔻\n💰 Price: ₹{live_price}\n📉 RSI: {current_rsi}\n{vol_text}\n\n🛡️ StopLoss: ₹{sl}\n🎯 Target 1 (1%): ₹{t1}\n🎯 Target 2 (2%): ₹{t2}"
                if vol_ratio >= 1.5: msg += "\n⚠️ INSTITUTIONAL VOLUME SELLING!"
                telegram_alerts.append(msg)
        except:
            continue
            
    if telegram_alerts:
        for alert in telegram_alerts:
            send_telegram_alert(alert)

# --- SIDEBAR CONTROLS ---
st.sidebar.header("🕹️ Automation Panel")
if st.sidebar.button("🟢 Start 5-Min Auto Scanner", type="primary"):
    st.session_state.auto_scan = True
    st.sidebar.success("Auto-Pilot Mode Activated!")

if st.sidebar.button("🔴 Stop Scanner"):
    st.session_state.auto_scan = False
    st.sidebar.warning("Auto-Pilot Mode Paused.")

# --- LIVE REFRESH LOOP LOGIC ---
if st.session_state.auto_scan:
    st.info("🔄 **Auto-Pilot Mode ON:** Engine chalu hai. Har 5 minute baad yeh page automatically refresh hoga aur Telegram par data bhejega.")
    
    # Pehle turant ek baar scan run karega
    with st.spinner("Scanning active stock list..."):
        run_full_scan()
    st.success("Scan complete! Telegram par alerts check karein. 5-minute ka countdown shuru.")
    
    # UI par countdown ya message hold karne ke liye time script sleep
    time.sleep(300) # 300 seconds = 5 Minutes
    st.rerun() # Page ko auto restart karega taaki loop chalta rahe
else:
    st.warning("⏸️ System Hold state mein hai. Chalu karne ke liye sidebar se 'Start 5-Min Auto Scanner' dabayein.")
