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
SHEET_URL = "https://docs.google.com/spreadsheets/d/1BHnQm0nYwl3paJ9PUEfHPlzMBLLXdpCZtdC59SFma58/edit?gid=0#gid=0"

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
    except: 
        pass

# --- ADVANCED QUANT MATH ENGINE ---
def analyze_deep_matrix(df_daily, df_weekly):
    analysis = {}
    
    # 1. Statistical Volatility & Z-Score
    df_daily['MA20'] = df_daily['Close'].rolling(window=20).mean()
    df_daily['STD20'] = df_daily['Close'].rolling(window=20).std()
    df_daily['Z_Score'] = (df_daily['Close'] - df_daily['MA20']) / df_daily['STD20']
    
    # 2. Price Performance over Multiple Timeframes
    last_close = float(df_daily['Close'].iloc[-1])
    one_month_ago = float(df_daily['Close'].iloc[-21]) if len(df_daily) > 21 else float(df_daily['Close'].iloc[0])
    
    daily_rsi = df_daily['Close'].diff()
    gain = (daily_rsi.where(daily_rsi > 0, 0)).ewm(alpha=1/14, adjust=False).mean()
    loss = (-daily_rsi.where(daily_rsi < 0, 0)).ewm(alpha=1/14, adjust=False).mean()
    df_daily['RSI_Daily'] = 100 - (100 / (1 + (gain / loss)))
    
    # 3. Smart Money Volume Accumulation (VSA)
    last_vol = float(df_daily['Volume'].iloc[-1])
    avg_vol_50 = df_daily['Volume'].rolling(window=50).mean().iloc[-1]
    volume_shock = last_vol / avg_vol_50 if avg_vol_50 > 0 else 1.0

    analysis['live_price'] = round(last_close, 2)
    analysis['z_score'] = round(float(df_daily['Z_Score'].iloc[-1]), 2) if not pd.isna(df_daily['Z_Score'].iloc[-1]) else 0.0
    analysis['rsi_daily'] = round(float(df_daily['RSI_Daily'].iloc[-1]), 1) if not pd.isna(df_daily['RSI_Daily'].iloc[-1]) else 50.0
    analysis['vol_shock'] = round(volume_shock, 2)
    analysis['return_1m'] = round(((last_close - one_month_ago) / one_month_ago) * 100, 2)
    
    # 4. Weekly Macro Trend Check
    df_weekly['EMA50_W'] = df_weekly['Close'].ewm(span=50, adjust=False).mean()
    analysis['weekly_trend'] = "BULLISH" if float(df_weekly['Close'].iloc[-1]) > float(df_weekly['EMA50_W'].iloc[-1]) else "BEARISH"
    
    return analysis

# --- DATA COMPILATION FUNCTION ---
def run_core_scanner():
    sheet = get_google_sheet()
    if not sheet: return None, None
    
    records = sheet.get_all_records()
    df_sheet = pd.DataFrame(records)
    
    if df_sheet.empty or 'Symbol' not in df_sheet.columns: return None, None
    
    symbols = [str(s).strip() for s in df_sheet['Symbol'].dropna().tolist() if str(s).strip()]
    deep_results = []
    tele_reports = []
    
    for sym in symbols:
        formatted_sym = sym if (sym.endswith(".NS") or sym.endswith(".BO")) else f"{sym}.NS"
        try:
            data_daily = yf.download(formatted_sym, period="1y", interval="1d", progress=False)
            data_weekly = yf.download(formatted_sym, period="2y", interval="1wk", progress=False)
            
            if data_daily.empty or data_weekly.empty: continue
            
            clean_daily = pd.DataFrame(index=data_daily.index)
            clean_weekly = pd.DataFrame(index=data_weekly.index)
            
            if isinstance(data_daily.columns, pd.MultiIndex):
                clean_daily['Close'] = data_daily['Close'][formatted_sym]
                clean_daily['Volume'] = data_daily['Volume'][formatted_sym]
                clean_weekly['Close'] = data_weekly['Close'][formatted_sym]
            else:
                clean_daily['Close'] = data_daily['Close']
                clean_daily['Volume'] = data_daily['Volume']
                clean_weekly['Close'] = data_weekly['Close']
                
            clean_daily = clean_daily.dropna()
            clean_weekly = clean_weekly.dropna()
            
            metrics = analyze_deep_matrix(clean_daily, clean_weekly)
            
            score = 0
            verdict = "NEUTRAL STATE"
            
            if metrics['weekly_trend'] == "BULLISH": score += 1
            if 50 <= metrics['rsi_daily'] <= 65: score += 1
            if metrics['vol_shock'] >= 1.5: score += 1
            if 0 < metrics['z_score'] < 1.5: score += 1
            
            if score >= 3:
                verdict = "💎 INSTITUTIONAL ACCUMULATION (STRONG BUY)"
                report = f"🏛️ **DEEP ALPHA RADAR: {sym}** 💎\n\n" \
                         f"💰 Current Price: ₹{metrics['live_price']}\n" \
                         f"📊 Vol Shock: {metrics['vol_shock']}x\n" \
                         f"📈 Daily RSI: {metrics['rsi_daily']}\n" \
                         f"🧭 Long-Term Trend: {metrics['weekly_trend']}\n" \
                         f"📐 Z-Score: {metrics['z_score']}\n" \
                         f"📅 1-Month Return: {metrics['return_1m']}%\n\n" \
                         f"🎯 **Verdict:** Institutional Accumulation Zone."
                tele_reports.append(report)
            elif score <= 1 and metrics['z_score'] > 2.0:
                verdict = "⚠️ OVERVALUED / DISTRIBUTION (RETAIL TRAP)"
            
            deep_results.append({
                "Stock": sym, "Price": metrics['live_price'], "Vol Shock": metrics['vol_shock'],
                "Z-Score": metrics['z_score'], "Daily RSI": metrics['rsi_daily'], 
                "Macro Trend": metrics['weekly_trend'], "Verdict": verdict
            })
        except Exception as e:
            continue
            
    return deep_results, tele_reports

# ==========================================
# SIDEBAR CONTROL & BUTTONS MATRIX
# ==========================================
st.sidebar.header("🕹️ Command Center")

# Button 1: Screen UI Analysis
btn_scan = st.sidebar.button("🚀 RUN SCREEN UI SCAN", type="primary", use_container_width=True)

# Button 2: Telegram Dispatcher
btn_telegram = st.sidebar.button("📡 DISPATCH TO TELEGRAM", use_container_width=True)

# --- ACTION TRIGGER: BUTTON 1 (SCREEN DISPLAY ONLY) ---
if btn_scan:
    with st.spinner("Analyzing Deep Mathematical Strata..."):
        deep_results, _ = run_core_scanner()
        
        if deep_results:
            st.subheader("📊 Quant Institutional Scoring Matrix (Local View)")
            res_df = pd.DataFrame(deep_results)
            
            def style_verdict(val):
                if "STRONG BUY" in val: return 'color: white; background-color: green; font-weight: bold'
                elif "RETAIL TRAP" in val: return 'color: white; background-color: red; font-weight: bold'
                return ''
                
            st.dataframe(res_df.style.map(style_verdict, subset=['Verdict']), use_container_width=True, hide_index=True)
            st.success("✅ Screen Scan Complete! Report rendered locally. No alerts sent to Telegram.")
        else:
            st.warning("⚠️ Watchlist data not found or Google Sheet empty.")

# --- ACTION TRIGGER: BUTTON 2 (TELEGRAM DISPATCH) ---
if btn_telegram:
    with st.spinner("Compiling and Dispatching Reports via Telegram Bot..."):
        deep_results, tele_reports = run_core_scanner()
        
        # Pehle screen par table render hoga
        if deep_results:
            st.subheader("📊 Quant Institutional Scoring Matrix")
            res_df = pd.DataFrame(deep_results)
            def style_verdict(val):
                if "STRONG BUY" in val: return 'color: white; background-color: green; font-weight: bold'
                elif "RETAIL TRAP" in val: return 'color: white; background-color: red; font-weight: bold'
                return ''
            st.dataframe(res_df.style.map(style_verdict, subset=['Verdict']), use_container_width=True, hide_index=True)
            
            # Phir on-demand Telegram logic execute hoga
            if tele_reports:
                send_telegram_alert("🏛️ **ON-DEMAND INSTITUTIONAL QUANT REPORT** 🏛️")
                for rep in tele_reports:
                    send_telegram_alert(rep)
                st.success(f"✅ Dispatched! {len(tele_reports)} strong institutional setups sent to Telegram Channel.")
            else:
                send_telegram_alert("🏛️ **QUANT REPORT:** Current scan indicates Neutral/Retail traps across the watchlist. No strong buy setups found today.")
                st.info("⚠️ Watchlist completed. No strong accumulation found, Telegram status updated to Neutral.")
        else:
            st.warning("⚠️ Failed to trigger pipeline. Check connection settings.")
