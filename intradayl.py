import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os

# --- SECURE CONFIGURATION ---
# GitGuardian se bachne ke liye hum token aur credentials ko secrets se load kar rahe hain
BOT_TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]  
CHAT_ID = "299717233"      

# 🔴 YAHAN APNI GOOGLE SHEET KA ASLI URL PASTE KAREIN (Yeh GitHub par safe hai)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1BHnQm0nYwl3paJ9PUEfHPlzMBLLXdpCZtdC59SFma58/edit?gid=0#gid=0"

# --- GOOGLE SHEETS CONNECTION ENGINE ---
def get_google_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    try:
        # Streamlit Cloud ke Secrets se direct connect karne ke liye
        creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_url(SHEET_URL).sheet1
        return sheet
    except Exception as e:
        st.error(f"⚠️ Cloud Sheet Connection Error: {e}")
        return None

def load_sheet_data():
    sheet = get_google_sheet()
    if sheet is None: 
        return pd.DataFrame(columns=['Symbol', 'Base_Price'])
    
    try:
        records = sheet.get_all_records()
        df = pd.DataFrame(records)
        if df.empty or 'Symbol' not in df.columns:
            df = pd.DataFrame(columns=['Symbol', 'Base_Price'])
        return df
    except:
        return pd.DataFrame(columns=['Symbol', 'Base_Price'])

# --- TELEGRAM SPLITTER ENGINE ---
def send_telegram_alert(message):
    if not message: return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    lines = message.split("\n")
    current_chunk = []
    current_length = 0
    chunks = []
    
    for line in lines:
        if current_length + len(line) + 1 > 3500:
            chunks.append("\n".join(current_chunk))
            current_chunk = [line]
            current_length = len(line)
        else:
            current_chunk.append(line)
            current_length += len(line) + 1
            
    if current_chunk: 
        chunks.append("\n".join(current_chunk))
        
    for index, chunk in enumerate(chunks):
        final_text = f"{chunk}\n\n(Part {index+1}/{len(chunks)})" if len(chunks) > 1 else chunk
        try: 
            requests.post(url, json={"chat_id": CHAT_ID, "text": final_text}, timeout=15)
        except: 
            pass

# --- MARKET DATA FETCH ENGINE ---
def fetch_market_data(symbols):
    results = {}
    if not symbols: return results
    try:
        data = yf.download(symbols, period="1y", group_by='ticker', progress=False, threads=True)
        if data.empty: return results
        for sym in symbols:
            try:
                ticker_df = data[sym] if len(symbols) > 1 else data
                ticker_df = ticker_df.dropna(subset=['Close'])
                if not ticker_df.empty:
                    vol_series = ticker_df['Volume'] if 'Volume' in ticker_df else pd.Series(dtype=float)
                    vol_curr = vol_series.iloc[-1] if not vol_series.empty else 0
                    vol_avg = vol_series.iloc[-21:-1].mean() if len(vol_series) > 20 else vol_curr
                    
                    delta = ticker_df['Close'].diff()
                    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/14, adjust=False).mean()
                    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14, adjust=False).mean()
                    rs = gain / loss
                    rsi = 100 - (100 / (1 + rs))
                    
                    results[sym] = {
                        "Live Price": round(ticker_df['Close'].iloc[-1], 2),
                        "RSI": round(rsi.iloc[-1], 1) if len(rsi) >= 14 else 50.0,
                        "52W High": round(ticker_df['High'].max(), 2),
                        "52W Low": round(ticker_df['Low'].min(), 2),
                        "vol_curr": vol_curr,
                        "vol_avg": vol_avg
                    }
            except: 
                continue
    except: 
        pass
    return results

# ==========================================
# STREAMLIT UI LAYOUT
# ==========================================
st.set_page_config(page_title="Stock Tracker Pro", page_icon="📈", layout="wide")
st.title("📈 Live Dashboard + Google Sheets AI")

if 'live_df' not in st.session_state:
    st.session_state.live_df = pd.DataFrame()

# Sidebar: Watchlist Configuration
st.sidebar.header("📁 Google Sheets Watchlist")
watchlist_df = load_sheet_data()
edited_watchlist = st.sidebar.data_editor(watchlist_df, num_rows="dynamic", use_container_width=True, key="sheets_editor")

if st.sidebar.button("💾 Save Changes To Google Sheet", type="primary"):
    sheet = get_google_sheet()
    if sheet:
        with st.spinner("Google Sheet Syncing..."):
            if not edited_watchlist.empty and 'Symbol' in edited_watchlist.columns:
                edited_watchlist['Symbol'] = edited_watchlist['Symbol'].apply(
                    lambda x: str(x).upper().strip() + ".NS" if pd.notna(x) and not (str(x).upper().endswith(".NS") or str(x).upper().endswith(".BO")) else x
                )
            
            sheet.clear()
            sheet.update([edited_watchlist.columns.values.tolist()] + edited_watchlist.values.tolist())
            st.sidebar.success("Google Sheet Updated Successfully!")
            st.rerun()

# Main Panel Controls
col_ctrl1, col_ctrl2, col_ctrl3 = st.columns(3)

with col_ctrl1:
    if st.button("🔄 REFRESH LIVE PRICES", use_container_width=True, type="secondary"):
        symbols = [str(s).strip() for s in edited_watchlist['Symbol'].dropna().tolist() if str(s).strip()]
        if symbols:
            with st.spinner("Fetching data..."):
                m_data = fetch_market_data(symbols)
                rows = []
                for _, row in edited_watchlist.iterrows():
                    sym = str(row['Symbol']).strip()
                    base = float(row['Base_Price']) if row['Base_Price'] else 0.0
                    d = m_data.get(sym, {})
                    live_p = d.get("Live Price", 0.0)
                    pct_chg = round(((live_p - base) / base) * 100, 2) if live_p and base > 0 else 0.0
                    
                    rows.append({
                        "Symbol": sym, "Buy Price": base, "Live Price": live_p if live_p else "N/A",
                        "% Change": pct_chg, "RSI": d.get("RSI", "N/A"),
                        "52W Range": f"H:{d.get('52W High', 0)} / L:{d.get('52W Low', 0)}" if d else "N/A",
                        "_vol_curr": d.get("vol_curr", 0), "_vol_avg": d.get("vol_avg", 0)
                    })
                st.session_state.live_df = pd.DataFrame(rows)
                st.success("Prices Updated!")
        else:
            st.warning("Pehle Watchlist mein stocks add karein!")

with col_ctrl2:
    if st.button("🚀 SCAN & SEND TELEGRAM ALERTS", use_container_width=True):
        if st.session_state.live_df.empty:
            st.error("⚠️ Pehle 'REFRESH LIVE PRICES' button dabayein!")
        else:
            alerts = []
            for _, row in st.session_state.live_df.iterrows():
                if row['Live Price'] == "N/A": continue
                sym = row['Symbol']
                pct = row['% Change']
                rsi = row['RSI']
                
                if abs(pct) >= 1.0:
                    emoji = "🚀" if pct > 0 else "🔻"
                    alerts.append(f"{emoji} {sym}: {pct}% (Price: ₹{row['Live Price']})")
                if row['_vol_avg'] > 0 and row['_vol_curr'] >= (row['_vol_avg'] * 2.0):
                    alerts.append(f"🔥 {sym}: Volume Breakout! ({int(row['_vol_curr']):,} shares)")
                if rsi != "N/A":
                    if rsi < 30: alerts.append(f"🟢 {sym}: RSI Oversold ({rsi})")
                    elif rsi > 75: alerts.append(f"🔴 {sym}: RSI Overbought ({rsi})")
                    
            if alerts:
                send_telegram_alert("⚡ FAST SMART ALERTS ⚡\n\n" + "\n".join(alerts))
                st.success(f"Sent {len(alerts)} alerts to Telegram!")
            else:
                send_telegram_alert("⚡ Scan Complete: Watchlist checked, no major breakouts found right now.")
                st.info("Scan completed! Matrix is quiet.")

with col_ctrl3:
    sort_action = st.selectbox("📊 Sort Data View:", ["Default", "Max to Min % Change", "Min to Max % Change"])

# Main Dashboard Grid
st.subheader("📊 Live Tracking Monitor")
search_q = st.text_input("🔍 Quick Filter/Search Stock by Symbol Name:", "").upper().strip()

if not st.session_state.live_df.empty:
    display_df = st.session_state.live_df.copy().drop(columns=["_vol_curr", "_vol_avg"])
    if search_q: 
        display_df = display_df[display_df['Symbol'].str.contains(search_q)]
    if sort_action == "Max to Min % Change": 
        display_df = display_df.sort_values(by="% Change", ascending=False)
    elif sort_action == "Min to Max % Change": 
        display_df = display_df.sort_values(by="% Change", ascending=True)
    st.dataframe(display_df, use_container_width=True, hide_index=True)
else:
    st.info("Dashboard is waiting for input data. Click on 'REFRESH LIVE PRICES' to spin the engine.")