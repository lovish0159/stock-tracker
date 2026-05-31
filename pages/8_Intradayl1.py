import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURATION (Streamlit Secrets Se Safe Connection) ---
BOT_TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]  
CHAT_ID = "299717233"      
SHEET_URL = "https://docs.google.com/spreadsheets/d/1BHnQm0nYwl3paJ9PUEfHPlzMBLLXdpCZtdC59SFma58/edit?gid=0#gid=0"  # Apni sheet ka link yahan dalein

st.set_page_config(layout="wide")
st.title("🚀 Intraday Sheet Multi-Scanner & Telegram Engine")
st.subheader("SuperTrend + RSI + Volume Automated Profit Matrix")

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

# --- MAIN CONTROLLER ---
st.sidebar.header("⏱️ Intraday Settings")
interval = st.sidebar.selectbox("Select Timeframe Candle:", ["1m", "5m", "15m"], index=1)

if st.button("⚡ START AUTOMATED SHEET MULTI-SCAN"):
    sheet = get_google_sheet()
    if sheet:
        with st.spinner("Google Sheet se stocks fetch ho rahe hain..."):
            records = sheet.get_all_records()
            df_sheet = pd.DataFrame(records)
            
            if df_sheet.empty or 'Symbol' not in df_sheet.columns:
                st.warning("⚠️ Google Sheet khali hai ya usme 'Symbol' column nahi hai!")
            else:
                symbols = [str(s).strip() for s in df_sheet['Symbol'].dropna().tolist() if str(s).strip()]
                
                st.write(f"🔍 Total **{len(symbols)}** Stocks scan ho rahe hain... Please wait.")
                
                scan_results = []
                telegram_alerts = []
                
                for sym in symbols:
                    # Sahi NSE format check karne ke liye (.NS automatic add karega)
                    formatted_sym = sym if (sym.endswith(".NS") or sym.endswith(".BO")) else f"{sym}.NS"
                    
                    try:
                        # Intraday 5m data download for each stock
                        data = yf.download(formatted_sym, period="3d", interval=interval, progress=False)
                        if data.empty: continue
                        
                        df_indicators = calculate_indicators(data.copy())
                        last_row = df_indicators.iloc[-1]
                        prev_row = df_indicators.iloc[-2]
                        
                        live_price = round(last_row['Close'], 2)
                        current_rsi = round(last_row['RSI'], 1)
                        current_vol = last_row['Volume']
                        avg_vol = last_row['Vol_Avg']
                        
                        # Conditions Mapping
                        buy_signal = (last_row['SuperTrend_Dir'] == 1 and prev_row['SuperTrend_Dir'] == -1) and (current_rsi > 48 and current_rsi < 70)
                        sell_signal = (last_row['SuperTrend_Dir'] == -1 and prev_row['SuperTrend_Dir'] == 1) and (current_rsi < 52 and current_rsi > 30)
                        vol_breakout = current_vol > (avg_vol * 1.5)
                        
                        status = "HOLD"
                        if buy_signal:
                            status = "🚀 BUY CALL"
                            sl = round(live_price * 0.992, 2)
                            t1 = round(live_price * 1.01, 2)
                            t2 = round(live_price * 1.02, 2)
                            
                            msg = f"🟢 **INTRADAY BUY ALERT: {sym}** 🚀\n💰 Price: ₹{live_price}\n📈 RSI: {current_rsi}\n🛡️ StopLoss: ₹{sl}\n🎯 Target 1: ₹{t1}\n🎯 Target 2: ₹{t2}"
                            if vol_breakout: msg += "\n🔥 HIGH VOLUME CONFIRMED!"
                            telegram_alerts.append(msg)
                            
                        elif sell_signal:
                            status = "🔻 SHORT-SELL"
                            sl = round(live_price * 1.008, 2)
                            t1 = round(live_price * 0.99, 2)
                            msg = f"🔴 **INTRADAY SELL ALERT: {sym}** 🔻\n💰 Price: ₹{live_price}\n📉 RSI: {current_rsi}\n🛡️ StopLoss: ₹{sl}\n🎯 Target: ₹{t1}"
                            telegram_alerts.append(msg)
                        
                        scan_results.append({
                            "Stock": sym, "Live Price": live_price, "RSI": current_rsi, 
                            "Volume State": "🔥 High" if vol_breakout else "Normal", "System Action": status
                        })
                    except:
                        continue
                
                # --- DISPLAY GRID ---
                if scan_results:
                    res_df = pd.DataFrame(scan_results)
                    st.subheader("📊 Live Sheet Scan Performance Sheet")
                    st.dataframe(res_df, use_container_width=True, hide_index=True)
                    
                    # Send telegram updates if any signals exist
                    if telegram_alerts:
                        send_telegram_alert("⚡ **PROFIT MATRIX SIGNALS DETECTED** ⚡")
                        for alert in telegram_alerts:
                            send_telegram_alert(alert)
                        st.success(f"🎉 Total {len(telegram_alerts)} Signal Alerts Telegram par bhej diye gaye hain!")
                    else:
                        st.info("Scan Complete: Google Sheet wale sabhi stocks safe zone mein hain, koi naya breakout nahi mila.")
