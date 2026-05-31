import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# --- CONFIGURATION (Streamlit Secrets & Core URL) ---
BOT_TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]  
CHAT_ID = "299717233"      
SHEET_URL = "https://docs.google.com/spreadsheets/d/1BHnQm0nYwl3paJ9PUEfHPlzMBLLXdpCZtdC59SFma58/edit?gid=0#gid=0"

st.set_page_config(layout="wide")
st.title("⚡ Live Intraday Hunter (5-Min Smart Automation)")
st.subheader("VWAP + RSI + Volume Breakout Sentinel Engine")

if "hunter_active" not in st.session_state:
    st.session_state.hunter_active = False

# --- GOOGLE SHEETS PIPELINE ---
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

def get_stocks_from_sheets():
    sheet = get_google_sheet()
    if sheet:
        try:
            records = sheet.get_all_records()
            df = pd.DataFrame(records)
            if not df.empty and 'Symbol' in df.columns:
                return [str(s).strip().upper() for s in df['Symbol'].dropna().tolist() if str(s).strip()]
        except Exception as e:
            st.error(f"⚠️ Watchlist processing error: {e}")
    return ["HAL.NS", "MAZDOCK.NS", "BDL.NS", "SBIN.NS"]

# --- INTRADAY CALCULATIONS ---
def calculate_intraday_indicators(df):
    df['TP'] = (df['High'] + df['Low'] + df['Close']) / 3
    df['VWAP'] = (df['TP'] * df['Volume']).cumsum() / df['Volume'].cumsum()
    
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0).ewm(alpha=1/14, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14, adjust=False).mean()
    df['RSI'] = 100 - (100 / (1 + gain / loss))
    return df

def send_telegram_alert(message):
    if not message: return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try: 
        requests.post(url, json=payload, timeout=10)
    except: 
        pass

# --- AUTOMATED HUNTING CORE LOGIC ---
def hunt_trades():
    raw_symbols = get_stocks_from_sheets()
    symbols = [s + ".NS" if not s.endswith(".NS") and not s.endswith(".BO") else s for s in raw_symbols]
    messages = []
    display_data = []
    
    try:
        data = yf.download(symbols, period="1d", interval="5m", progress=False, threads=True)
    except Exception as e:
        st.error("⚠️ Data connection lost with Yahoo Finance APIs.")
        return
        
    for sym in symbols:
        try:
            if isinstance(data.columns, pd.MultiIndex):
                if sym in data['Close'].columns:
                    df = pd.DataFrame({
                        'Open': data['Open'][sym], 'High': data['High'][sym],
                        'Low': data['Low'][sym], 'Close': data['Close'][sym],
                        'Volume': data['Volume'][sym]
                    }).dropna()
                else: continue
            else:
                if len(symbols) == 1:
                    df = data.dropna()
                else: continue
            
            if len(df) > 10:
                df = calculate_intraday_indicators(df)
                last = df.iloc[-1]
                
                price = float(last['Close'])
                vwap = float(last['VWAP'])
                rsi = float(last['RSI'])
                vol = float(last['Volume'])
                avg_vol = float(df['Volume'].mean())
                
                vol_mult = vol / avg_vol if avg_vol > 0 else 1.0
                signal = "Neutral"
                
                # Pro Setup Scan Rules
                if avg_vol > 0 and vol > (avg_vol * 2):
                    if price > vwap and 60 <= rsi <= 75:
                        target = price + (price * 0.01) 
                        sl = vwap - (price * 0.002)     
                        signal = "🚀 BUY"
                        messages.append(f"🚀 *INTRADAY BUY*: {sym}\n💵 *Entry*: ₹{price:.2f}\n🎯 *Target*: ₹{target:.2f}\n🛑 *Stop-Loss*: ₹{sl:.2f}\n📊 RSI: {rsi:.1f} | Vol: {vol_mult:.1f}x")
                        
                    elif price < vwap and 30 <= rsi <= 45:
                        target = price - (price * 0.01)
                        sl = vwap + (price * 0.002)
                        signal = "📉 SHORT"
                        messages.append(f"📉 *INTRADAY SHORT*: {sym}\n💵 *Entry*: ₹{price:.2f}\n🎯 *Target*: ₹{target:.2f}\n🛑 *Stop-Loss*: ₹{sl:.2f}\n📊 RSI: {rsi:.1f} | Vol: {vol_mult:.1f}x")
                
                display_data.append({
                    "Symbol": sym, "Price": round(price, 2), "VWAP": round(vwap, 2),
                    "RSI (5m)": round(rsi, 1), "Volume Multiplier": f"{vol_mult:.1f}x", "Signal": signal
                })
        except:
            continue
            
    # Display Dashboard Grid on Screen
    if display_data:
        res_df = pd.DataFrame(display_data)
        def highlight_signals(val):
            if val == "🚀 BUY": return 'color: white; background-color: green; font-weight: bold'
            elif val == "📉 SHORT": return 'color: white; background-color: red; font-weight: bold'
            return ''
        st.dataframe(res_df.style.map(highlight_signals, subset=['Signal']), use_container_width=True, hide_index=True)

    if messages:
        final_alert = f"⚡ *LIVE SETUPS ({datetime.now().strftime('%H:%M')})* ⚡\n\n" + "\n\n".join(messages)
        send_telegram_alert(final_alert)
        st.toast("📡 Active alerts sent to Telegram Channel!")

# --- SIDEBAR CONTROL LAYER ---
st.sidebar.header("🕹️ Automation Controller")
if st.sidebar.button("🟢 Start Intraday Hunter", type="primary"):
    st.session_state.hunter_active = True
    st.sidebar.success("Automation Core Triggered!")

if st.sidebar.button("🔴 Stop Intraday Hunter"):
    st.session_state.hunter_active = False
    st.sidebar.warning("Automation Core Interrupted.")

# --- LIVE AUTO-REFRESH MATRIX LOOP ---
if st.session_state.hunter_active:
    now = datetime.now()
    # Check Market Session (Mon-Fri, 9:00 AM to 3:30 PM)
    if now.weekday() < 5 and (9 <= now.hour < 15 or (now.hour == 15 and now.minute <= 30)):
        st.info(f"🔄 **Automated Scanning Active:** Last Checked at **{now.strftime('%H:%M:%S')}**. System syncing with 5-minute charts...")
        hunt_trades()
        
        # Calculate countdown until next 5m sync slot smoothly
        minute = now.minute
        next_minute = ((minute // 5) + 1) * 5
        sleep_seconds = ((next_minute - minute - 1) * 60 + (60 - now.second)) + 2 if next_minute != 60 else ((59 - minute) * 60 + (60 - now.second)) + 2
        
        st.write(f"⏳ Syncing next data block in **{sleep_seconds}** seconds...")
        st.page_link("pages/1_Intraday_Hunter.py", label="Force Sync Page Manually", icon="🔄")
        
        # Streamlit Cloud native dynamic refresh configuration
        st.fragment(lambda: None)() 
        st.rerun()
    else:
        st.warning("💤 **Market is Closed:** The matrix scanner is now on standby. Automatic looping will resume at Monday 09:00 AM.")
        st.info("Current Watchlist Snapshot Status:")
        hunt_trades()
else:
    st.warning("Dashboard Core is Idle. Click 'Start Intraday Hunter' to stream algorithmic setups.")
