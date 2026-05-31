import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURATION (Streamlit Secrets) ---
BOT_TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]  
CHAT_ID = "299717233"      
SHEET_URL = "https://docs.google.com/spreadsheets/d/1BHnQm0nYwl3paJ9PUEfHPlzMBLLXdpCZtdC59SFma58/edit?gid=0#gid=0" # Apni sheet ka link dalein

st.set_page_config(layout="wide")
st.title("🏛️ Deep Quantitative Alpha Analyzer")
st.subheader("Smart Money Accumulation, Statistical Volatility & Trend Confluence")

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

# --- TELEGRAM SENDER ---
def send_telegram_alert(message):
    if not message: return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try: 
        requests.post(url, json={"chat_id": CHAT_ID, "text": message}, timeout=15)
    except: pass

# --- ADVANCED QUANT MATH ENGINE ---
def analyze_deep_matrix(df_daily, df_weekly):
    analysis = {}
    
    # 1. Statistical Volatility & Z-Score (Mathematical Deviation)
    # Yeh check karta hai ki price normal range se kitna dur nikal gaya hai
    df_daily['MA20'] = df_daily['Close'].rolling(window=20).mean()
    df_daily['STD20'] = df_daily['Close'].rolling(window=20).std()
    df_daily['Z_Score'] = (df_daily['Close'] - df_daily['MA20']) / df_daily['STD20']
    
    # 2. Price Performance over Multiple Timeframes
    last_close = df_daily['Close'].iloc[-1]
    one_month_ago = df_daily['Close'].iloc[-21] if len(df_daily) > 21 else df_daily['Close'].iloc[0]
    
    daily_rsi = df_daily['Close'].diff()
    gain = (daily_rsi.where(daily_rsi > 0, 0)).ewm(alpha=1/14, adjust=False).mean()
    loss = (-daily_rsi.where(daily_rsi < 0, 0)).ewm(alpha=1/14, adjust=False).mean()
    df_daily['RSI_Daily'] = 100 - (100 / (1 + (gain / loss)))
    
    # 3. Smart Money Volume Accumulation (VSA)
    last_vol = df_daily['Volume'].iloc[-1]
    avg_vol_50 = df_daily['Volume'].rolling(window=50).mean().iloc[-1]
    volume_shock = last_vol / avg_vol_50 if avg_vol_50 > 0 else 1.0

    analysis['live_price'] = round(last_close, 2)
    analysis['z_score'] = round(df_daily['Z_Score'].iloc[-1], 2)
    analysis['rsi_daily'] = round(df_daily['RSI_Daily'].iloc[-1], 1)
    analysis['vol_shock'] = round(volume_shock, 2)
    analysis['return_1m'] = round(((last_close - one_month_ago) / one_month_ago) * 100, 2)
    
    # 4. Weekly Macro Trend Check (For Long-Term Support)
    df_weekly['EMA50_W'] = df_weekly['Close'].ewm(span=50, adjust=False).mean()
    analysis['weekly_trend'] = "BULLISH" if df_weekly['Close'].iloc[-1] > df_weekly['EMA50_W'].iloc[-1] else "BEARISH"
    
    return analysis

# --- CORE SCANNER ACTION ---
if st.button("🚀 EXECUTE 360° DEEP ANALYSIS SCAN"):
    sheet = get_google_sheet()
    if sheet:
        with st.spinner("Analyzing Deep Mathematical Strata..."):
            records = sheet.get_all_records()
            df_sheet = pd.DataFrame(records)
            
            if not df_sheet.empty and 'Symbol' in df_sheet.columns:
                symbols = [str(s).strip() for s in df_sheet['Symbol'].dropna().tolist() if str(s).strip()]
                
                deep_results = []
                tele_reports = []
                
                for sym in symbols:
                    formatted_sym = sym if (sym.endswith(".NS") or sym.endswith(".BO")) else f"{sym}.NS"
                    try:
                        # Fetch Daily data (1 year) & Weekly data (2 years)
                        data_daily = yf.download(formatted_sym, period="1y", interval="1d", progress=False)
                        data_weekly = yf.download(formatted_sym, period="2y", interval="1wk", progress=False)
                        
                        if data_daily.empty or data_weekly.empty: continue
                        
                        metrics = analyze_deep_matrix(data_daily.copy(), data_weekly.copy())
                        
                        # --- SCORING INTELLIGENCE SYSTEM ---
                        # Agar Z-Score chota ho (Stock sasta hai), Volume High ho, aur Weekly Trend Up ho = Jackpot!
                        score = 0
                        verdict = "NEUTRAL STATE"
                        
                        if metrics['weekly_trend'] == "BULLISH": score += 1
                        if metrics['rsi_daily'] >= 50 and metrics['rsi_daily'] <= 65: score += 1
                        if metrics['vol_shock'] >= 1.5: score += 1
                        if metrics['z_score'] > 0 and metrics['z_score'] < 1.5: score += 1
                        
                        if score >= 3:
                            verdict = "💎 INSTITUTIONAL ACCUMULATION (STRONG BUY)"
                            report = f"🏛️ **DEEP ALPHA RADAR: {sym}** 💎\n\n" \
                                     f"💰 Current Price: ₹{metrics['live_price']}\n" \
                                     f"📊 Vol Shock: {metrics['vol_shock']}x (Heavy Delivery & Block Buying!)\n" \
                                     f"📈 Daily RSI: {metrics['rsi_daily']} (Perfect Momentum Zone)\n" \
                                     f"🧭 Long-Term Trend: {metrics['weekly_trend']}\n" \
                                     f"📐 Statistical Deviation (Z-Score): {metrics['z_score']}\n" \
                                     f"📅 1-Month Return: {metrics['return_1m']}%\n\n" \
                                     f"🎯 **Verdict:** Institutional Interest Detected. Low Risk Entry Zone."
                            tele_reports.append(report)
                        elif score <= 1 and metrics['z_score'] > 2.0:
                            verdict = "⚠️ OVERVALUED / DISTRIBUTION (RETAIL TRAP)"
                        
                        deep_results.append({
                            "Stock": sym, "Price": metrics['live_price'], "Vol Shock": metrics['vol_shock'],
                            "Z-Score": metrics['z_score'], "Daily RSI": metrics['rsi_daily'], 
                            "Macro Trend": metrics['weekly_trend'], "Verdict": verdict
                        })
                    except: continue
                
                # UI Render Grid
                if deep_results:
                    st.subheader("📊 Quant Institutional Scoring Matrix")
                    st.dataframe(pd.DataFrame(deep_results), use_container_width=True, hide_index=True)
                    
                    if tele_reports:
                        send_telegram_alert("🏛️ **INSTITUTIONAL QUANT DATA REPORT** 🏛️")
                        for rep in tele_reports:
                            send_telegram_alert(rep)
                        st.success("Deep Analysis Report Telegram par dispatch kar di gayi hai!")
                    else:
                        st.info("Scan Complete: Khas Smart Money Accumulation kisi stock mein nahi mila abhi.")