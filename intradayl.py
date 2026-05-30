import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import os

# ==========================================
# 1. PAGE SETUP & TELEGRAM SETTINGS
# ==========================================
st.set_page_config(page_title="Ultimate Trading Dashboard", page_icon="🏦", layout="wide")

# ⚠️ YAHAN APNA TELEGRAM DATA DALEIN
BOT_TOKEN = "8544175428:AAF6iGJasuxk5jZ4rE6_4Lxq2wngrxZoAXY"  # Apna naya token yahan daalein
CHAT_ID = "299717233"      # Apni Chat ID yahan daalein
FILE_NAME = "stocks_list.xlsx"

st.title("🏦 Ultimate Trading Command Center")
st.caption("Manage Portfolio & Hunt Intraday Setups Manually (Bug-Free Pro Edition)")

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
# 2. BULLETPROOF EXCEL HANDLING
# ==========================================
def init_file():
    if not os.path.exists(FILE_NAME):
        pd.DataFrame({"Symbol": ["HAL.NS"], "Base_Price": [3500.0]}).to_excel(FILE_NAME, index=False)

def load_stocks():
    init_file()
    try:
        df = pd.read_excel(FILE_NAME)
    except PermissionError:
        st.error("⚠️ Excel file is open in another program. Please close it!")
        return pd.DataFrame(columns=["Symbol", "Base_Price"])
        
    df.columns = df.columns.str.strip()
    
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

def save_stocks(df):
    try:
        df.to_excel(FILE_NAME, index=False)
        return True
    except PermissionError:
        st.sidebar.error("⚠️ Cannot save! Close the Excel file on your PC first.")
        return False

stocks_df = load_stocks()
stocks_list = stocks_df['Symbol'].dropna().astype(str).str.upper().tolist()

# ==========================================
# 3. SIDEBAR: ADD, DELETE & FIND
# ==========================================
st.sidebar.header("🛠️ Manage Watchlist")

st.sidebar.subheader("➕ Add Stock")
new_stock = st.sidebar.text_input("Enter Symbol (e.g. SBIN)").strip().upper()
new_price = st.sidebar.number_input("Enter Base Price (₹)", min_value=0.0, step=1.0)

if st.sidebar.button("Add to Excel"):
    if new_stock:
        if not new_stock.endswith(".NS") and not new_stock.endswith(".BO"):
            new_stock += ".NS"
            
        if new_stock not in stocks_list:
            new_row = pd.DataFrame({"Symbol": [new_stock], "Base_Price": [new_price]})
            stocks_df = pd.concat([stocks_df, new_row], ignore_index=True)
            if save_stocks(stocks_df):
                st.sidebar.success(f"✅ {new_stock} Added!")
                st.rerun()
        else:
            st.sidebar.warning("Stock already exists!")

st.sidebar.divider()
st.sidebar.subheader("🗑️ Delete Stock")
del_stock = st.sidebar.selectbox("Select Stock to Remove", [""] + stocks_list)
if st.sidebar.button("Delete from Excel"):
    if del_stock in stocks_list:
        stocks_df = stocks_df[stocks_df['Symbol'] != del_stock]
        if save_stocks(stocks_df):
            st.sidebar.success(f"❌ {del_stock} Deleted!")
            st.rerun()

# ==========================================
# 4. TABS SETUP (Dual Engine)
# ==========================================
tab1, tab2 = st.tabs(["📈 Portfolio Tracker (Long-Term)", "⚡ Intraday Hunter (5-Min Live)"])

# ------------------------------------------
# TAB 1: PORTFOLIO TRACKER (Base Price + 10%)
# ------------------------------------------
with tab1:
    st.header("📈 Long-Term Portfolio Analysis")
    if st.button("🔍 Scan Portfolio (Base Price vs Live)", type="primary"):
        if stocks_df.empty:
            st.warning("List is empty!")
        else:
            with st.spinner("Fetching Daily Data..."):
                data = yf.download(stocks_list, period="3mo", progress=False, threads=True)
                results = []
                
                # BUG FIX: Handle completely empty market data
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
# TAB 2: INTRADAY HUNTER (5-Min Timeframe)
# ------------------------------------------
with tab2:
    st.header("⚡ Live Intraday Scanner (VWAP + RSI + Volume)")
    st.caption("Scans 5-minute candles to find immediate Buy/Short opportunities with Target & SL.")
    
    if st.button("🚀 Run Intraday Scan Now", type="primary"):
        if stocks_df.empty:
            st.warning("List is empty!")
        else:
            with st.spinner("Analyzing 5-Min Candles..."):
                try:
                    # BUG FIX: Fetch 5 days to ensure we get data even on weekends, then filter last day
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
                            # Safely extract single stock data
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
                                # BUG FIX: Get ONLY the last trading day's data so VWAP calculation is strictly intraday
                                last_day = df.index[-1].date()
                                df = df[df.index.date == last_day].copy()
                                
                                # Accurate Intraday VWAP (Daily Reset)
                                df['TP'] = (df['High'] + df['Low'] + df['Close']) / 3
                                df['VWAP'] = (df['TP'] * df['Volume']).cumsum() / df['Volume'].cumsum()
                                
                                # RSI (14)
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
                                
                                # Pro-Level Setup Logic
                                if avg_vol > 0 and vol > (avg_vol * 1.5):
                                    if price > vwap and 55 <= rsi <= 75:
                                        signal = "🚀 BUY"
                                        target = price + (price * 0.01)
                                        sl = vwap - (price * 0.002)
                                        alert_messages.append(f"🚀 *BUY*: {sym} @ ₹{price:.2f}\n🎯 TGT: ₹{target:.2f} | 🛑 SL: ₹{sl:.2f}\nVWAP: ₹{vwap:.2f} | RSI: {rsi:.1f} | Vol: {vol_str}")
                                    
                                    elif price < vwap and 30 <= rsi <= 45:
                                        signal = "📉 SHORT"
                                        target = price - (price * 0.01)
                                        sl = vwap + (price * 0.002)
                                        alert_messages.append(f"📉 *SHORT*: {sym} @ ₹{price:.2f}\n🎯 TGT: ₹{target:.2f} | 🛑 SL: ₹{sl:.2f}\nVWAP: ₹{vwap:.2f} | RSI: {rsi:.1f} | Vol: {vol_str}")
                                
                                intra_results.append({
                                    "Symbol": sym, "Live Price": round(price, 2),
                                    "VWAP": round(vwap, 2), "RSI (5m)": round(rsi, 1),
                                    "Volume": vol_str, "Signal": signal,
                                    "Target": round(target, 2) if target > 0 else "-",
                                    "StopLoss": round(sl, 2) if sl > 0 else "-"
                                })
                        except Exception as e:
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
                            if send_telegram_alert(final_msg):
                                st.success("✅ Intraday Setups Telegram par bhej diye gaye hain!")
                        else:
                            st.info("Market mein abhi (is 5-minute candle par) koi solid volume breakout nahi hai.")