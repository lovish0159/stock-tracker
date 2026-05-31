import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ==========================================
# 1. PAGE SETUP & TELEGRAM SETTINGS
# ==========================================
st.set_page_config(page_title="Ultimate Trading Dashboard", page_icon="🏦", layout="wide")

# Telegram & Google Sheet configurations via Streamlit Secrets
BOT_TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]  
CHAT_ID = "299717233"    
SHEET_URL = "https://docs.google.com/spreadsheets/d/1BHnQm0nYwl3paJ9PUEfHPlzMBLLXdpCZtdC59SFma58/edit?gid=0#gid=0"

st.title("🏦 Ultimate Trading Command Center")
st.caption("Manage Portfolio & Hunt Intraday Setups via Google Sheets (Cloud Pro Edition)")

def send_telegram_alert(message):
    if not message or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE": 
        return False
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try: 
        resp = requests.post(url, json=payload, timeout=15)
        return resp.status_code == 200
    except: 
        return False

# ==========================================
# 2. BULLETPROOF GOOGLE SHEETS CONNECTION
# ==========================================
@st.cache_resource
def get_gspread_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
    return gspread.authorize(creds)

def load_from_sheets():
    try:
        client = get_gspread_client()
        sheet = client.open_by_url(SHEET_URL).sheet1
        records = sheet.get_all_records()
        
        if not records:
            # If sheet is empty, return structure
            return pd.DataFrame(columns=["Symbol", "Base_Price"])
            
        df = pd.DataFrame(records)
        df.columns = df.columns.str.strip()
        
        # Mapping column variations to standard 'Base_Price'
        col_mapping = {}
        for col in df.columns:
            if col.lower().replace(' ', '_') in ['base_price', 'buy_price']:
                col_mapping[col] = 'Base_Price'
        if col_mapping:
            df.rename(columns=col_mapping, inplace=True)
            
        if 'Base_Price' not in df.columns:
            df['Base_Price'] = 0.0
            
        df['Base_Price'] = pd.to_numeric(df['Base_Price'], errors='coerce').fillna(0.0)
        return df
    except Exception as e:
        st.error(f"⚠️ Google Sheet load karne mein dikkat aayi: {e}")
        return pd.DataFrame(columns=["Symbol", "Base_Price"])

def add_stock_to_sheet(symbol, base_price):
    try:
        client = get_gspread_client()
        sheet = client.open_by_url(SHEET_URL).sheet1
        sheet.append_row([symbol, base_price])
        return True
    except Exception as e:
        st.sidebar.error(f"❌ Save failed: {e}")
        return False

def delete_stock_from_sheet(symbol):
    try:
        client = get_gspread_client()
        sheet = client.open_by_url(SHEET_URL).sheet1
        cell = sheet.find(symbol)
        if cell:
            sheet.delete_rows(cell.row)
            return True
        return False
    except Exception as e:
        st.sidebar.error(f"❌ Delete failed: {e}")
        return False

# Load Watchlist
stocks_df = load_from_sheets()
stocks_list = []
if not stocks_df.empty and 'Symbol' in stocks_df.columns:
    stocks_list = stocks_df['Symbol'].dropna().astype(str).str.upper().tolist()

# ==========================================
# 3. SIDEBAR: ADD, DELETE & FIND
# ==========================================
st.sidebar.header("🛠️ Manage Watchlist")

st.sidebar.subheader("➕ Add Stock")
new_stock = st.sidebar.text_input("Enter Symbol (e.g. SBIN)").strip().upper()
new_price = st.sidebar.number_input("Enter Base Price (₹)", min_value=0.0, step=1.0)

if st.sidebar.button("Add to Cloud Sheet"):
    if new_stock:
        if not new_stock.endswith(".NS") and not new_stock.endswith(".BO"):
            new_stock += ".NS"
            
        if new_stock not in stocks_list:
            if add_stock_to_sheet(new_stock, new_price):
                st.sidebar.success(f"✅ {new_stock} Added to Cloud!")
                st.invalidate_cache(load_from_sheets)
                st.rerun()
        else:
            st.sidebar.warning("Stock already exists!")

st.sidebar.divider()
st.sidebar.subheader("🗑️ Delete Stock")
del_stock = st.sidebar.selectbox("Select Stock to Remove", [""] + stocks_list)
if st.sidebar.button("Delete from Cloud Sheet"):
    if del_stock in stocks_list:
        if delete_stock_from_sheet(del_stock):
            st.sidebar.success(f"❌ {del_stock} Deleted from Cloud!")
            st.invalidate_cache(load_from_sheets)
            st.rerun()

# ==========================================
# 4. TABS SETUP (Dual Engine)
# ==========================================
tab1, tab2 = st.tabs(["📈 Portfolio Tracker (Long-Term)", "⚡ Intraday Hunter (5-Min Live)"])

# ------------------------------------------
# TAB 1: PORTFOLIO TRACKER
# ------------------------------------------
with tab1:
    st.header("📈 Long-Term Portfolio Analysis")
    if st.button("🔍 Scan Portfolio (Base Price vs Live)", type="primary"):
        if not stocks_list:
            st.warning("Watchlist is empty!")
        else:
            with st.spinner("Fetching Daily Data..."):
                data = yf.download(stocks_list, period="3mo", progress=False, threads=True)
                results = []
                
                if data is None or data.empty:
                    st.error("⚠️ Cannot fetch market data. Check internet or market timings.")
                else:
                    for index, row in stocks_df.iterrows():
                        sym = row['Symbol']
                        base_price = float(row['Base_Price'])
                        try:
                            if isinstance(data.columns, pd.MultiIndex):
                                if sym in data['Close'].columns:
                                    close_s = data['Close'][sym].dropna()
                                else: continue
                            else:
                                close_s = data['Close'].dropna()
                                
                            if not close_s.empty:
                                live_price = float(close_s.iloc[-1])
                                pct_change = ((live_price - base_price) / base_price) * 100 if base_price > 0 else 0.0
                                
                                results.append({
                                    "Symbol": sym, "Base Price": base_price, 
                                    "Live Price": round(live_price, 2), "% Change": round(pct_change, 2)
                                })
                        except:
                            pass
                            
                    if results:
                        res_df = pd.DataFrame(results)
                        st.subheader("🚨 10% Movers (Min to Max)")
                        df_10 = res_df[(res_df['% Change'] <= -10) | (res_df['% Change'] >= 10)]
                        df_10 = df_10.sort_values(by="% Change", ascending=True)
                        
                        if not df_10.empty:
                            def color_code(val): return 'color: green' if val > 0 else 'color: red'
                            st.dataframe(df_10.style.map(color_code, subset=['% Change']), use_container_width=True, hide_index=True)
                            
                            msg_lines = ["🚨 *PORTFOLIO 10% ALERT* 🚨\n"]
                            for i, r in df_10.iterrows():
                                icon = "🔴" if r['% Change'] < 0 else "🟢"
                                msg_lines.append(f"{icon} *{r['Symbol']}*: {r['% Change']:.2f}%\n(Base: ₹{r['Base Price']} ➡️ Live: ₹{r['Live Price']})")
                            
                            if send_telegram_alert("\n\n".join(msg_lines)):
                                st.success("✅ Portfolio Alert Sent to Telegram!")
                        else:
                            st.info("No stocks moved 10% from Base Price today.")
                            
                        st.subheader("📂 All Stocks")
                        st.dataframe(res_df, use_container_width=True, hide_index=True)

# ------------------------------------------
# TAB 2: INTRADAY HUNTER
# ------------------------------------------
with tab2:
    st.header("⚡ Live Intraday Scanner (VWAP + RSI + Volume)")
    st.caption("Scans 5-minute candles to find immediate Buy/Short opportunities with Target & SL.")
    
    if st.button("🚀 Run Intraday Scan Now", type="primary"):
        if not stocks_list:
            st.warning("Watchlist is empty!")
        else:
            with st.spinner("Analyzing 5-Min Candles..."):
                try:
                    data = yf.download(stocks_list, period="5d", interval="5m", progress=False, threads=True)
                except:
                    data = pd.DataFrame()
                    
                if data is None or data.empty:
                    st.error("⚠️ Market data fetch failed.")
                else:
                    intra_results = []
                    alert_messages = []
                    
                    for sym in stocks_list:
                        try:
                            if isinstance(data.columns, pd.MultiIndex):
                                if sym in data['Close'].columns:
                                    df = pd.DataFrame({
                                        'Close': data['Close'][sym], 'High': data['High'][sym],
                                        'Low': data['Low'][sym], 'Volume': data['Volume'][sym]
                                    }).dropna()
                                else: continue
                            else:
                                if len(stocks_list) == 1:
                                    df = data.dropna()
                                else: continue
                                
                            if len(df) > 10:
                                last_day = df.index[-1].date()
                                df = df[df.index.date == last_day].copy()
                                
                                df['TP'] = (df['High'] + df['Low'] + df['Close']) / 3
                                df['VWAP'] = (df['TP'] * df['Volume']).cumsum() / df['Volume'].cumsum()
                                
                                delta = df['Close'].diff()
                                gain = delta.where(delta > 0, 0).ewm(alpha=1/14, adjust=False).mean()
                                loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14, adjust=False).mean()
                                df['RSI'] = 100 - (100 / (1 + gain / loss))
                                
                                last = df.iloc[-1]
                                price = float(last['Close'])
                                vwap = float(last['VWAP'])
                                rsi = float(last['RSI'])
                                vol = float(last['Volume'])
                                avg_vol = float(df['Volume'].mean())
                                
                                vol_mult = vol / avg_vol if avg_vol > 0 else 1.0
                                vol_str = f"🔥 {vol_mult:.1f}x" if vol_mult >= 1.5 else f"{vol_mult:.1f}x"
                                
                                signal = "Neutral"
                                target = 0.0
                                sl = 0.0
                                
                                if avg_vol > 0 and vol > (avg_vol * 1.5):
                                    if price > vwap and 55 <= rsi <= 75:
                                        signal = "🚀 BUY"
                                        target = price + (price * 0.01)
                                        sl = vwap - (price * 0.002)
                                        alert_messages.append(f"🚀 *BUY*: {sym} @ ₹{price:.2f}\n🎯 TGT: ₹{target:.2f} | 🛑 SL: ₹{sl:.2f}\nVWAP: ₹{vwap:.2f} | RSI: {rsi:.1f}")
                                    
                                    elif price < vwap and 30 <= rsi <= 45:
                                        signal = "📉 SHORT"
                                        target = price - (price * 0.01)
                                        sl = vwap + (price * 0.002)
                                        alert_messages.append(f"📉 *SHORT*: {sym} @ ₹{price:.2f}\n🎯 TGT: ₹{target:.2f} | 🛑 SL: ₹{sl:.2f}\nVWAP: ₹{vwap:.2f} | RSI: {rsi:.1f}")
                                
                                intra_results.append({
                                    "Symbol": sym, "Live Price": round(price, 2),
                                    "VWAP": round(vwap, 2), "RSI (5m)": round(rsi, 1),
                                    "Volume": vol_str, "Signal": signal,
                                    "Target": round(target, 2) if target > 0 else "-",
                                    "StopLoss": round(sl, 2) if sl > 0 else "-"
                                })
                        except:
                            pass
                            
                    if intra_results:
                        intra_df = pd.DataFrame(intra_results)
                        def highlight_signals(val):
                            if val == "🚀 BUY": return 'color: white; background-color: green; font-weight: bold'
                            elif val == "📉 SHORT": return 'color: white; background-color: red; font-weight: bold'
                            return ''
                            
                        st.dataframe(intra_df.style.map(highlight_signals, subset=['Signal']), use_container_width=True, hide_index=True)
                        
                        if alert_messages:
                            final_msg = f"⚡ *LIVE MANUAL SCAN ({pd.Timestamp.now().strftime('%H:%M')})* ⚡\n\n" + "\n\n".join(alert_messages)
                            send_telegram_alert(final_msg)
                            st.success("✅ Intraday Setups Telegram par bhej diye gaye hain!")
                        else:
                            st.info("Market mein abhi koi solid volume breakout nahi hai.")
