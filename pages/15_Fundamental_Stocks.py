import streamlit as st
import pandas as pd
import yfinance as yf
from streamlit_gsheets import GSheetsConnection

# Page Setup
st.set_page_config(page_title="Intraday & Fundamental Screener", layout="wide")
st.title("📈 Custom Stock Screener for Intraday & Swing")

# Google Sheet Link Input
sheet_url = st.text_input("Apni Google Sheet ka Link yahan paste karein:")

if sheet_url:
    try:
        # Streamlit ka official aur secure Google Sheets connection
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        # Access token ka use karke private sheet read karna
        df = conn.read(spreadsheet=sheet_url)
        
        if 'Symbol' not in df.columns:
            st.error("❌ Aapki Google Sheet mein 'Symbol' naam ka column hona zaroori hai!")
        else:
            st.success("✅ Secure Sheet successfully connect ho gayi!")
            
            stock_data = []
            
            with st.spinner("Market data fetch kiya ja raha hai..."):
                # Har stock (jaise HAL.NS, BEL.NS, ya ASALCBR.BO) ka data nikalna
                for symbol in df['Symbol']:
                    # Khali ya invalid entry ko ignore karna
                    if pd.isna(symbol) or str(symbol).strip() == '':
                        continue
                        
                    try:
                        ticker = yf.Ticker(str(symbol).strip())
                        info = ticker.info
                        
                        current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
                        prev_close = info.get('previousClose', 1)
                        intraday_change = ((current_price - prev_close) / prev_close) * 100
                        
                        stock_data.append({
                            "Stock": str(symbol).replace('.NS', '').replace('.BO', ''),
                            "Price (₹)": current_price,
                            "Intraday Change %": round(intraday_change, 2),
                            "Today's Volume": info.get('volume', 0),
                            "P/E Ratio": info.get('trailingPE', 'N/A'),
                            "Market Cap (Cr)": round(info.get('marketCap', 0) / 10000000, 2) if info.get('marketCap') else 'N/A',
                            "52W High": info.get('fiftyTwoWeekHigh', 'N/A'),
                            "Debt/Equity": info.get('debtToEquity', 'N/A')
                        })
                    except Exception as e:
                        st.warning(f"{symbol} ka data nahi mil paya.")
            
            # Data ko table mein convert karna
            results_df = pd.DataFrame(stock_data)
            
            if not results_df.empty:
                st.subheader("🚀 Live Market Analysis")
                
                # Volume ko number format mein ensure karna taaki sort ho sake
                results_df["Today's Volume"] = pd.to_numeric(results_df["Today's Volume"], errors='coerce').fillna(0)
                
                # Intraday ke liye sabse pehle High Volume wale stocks
                intraday_picks = results_df.sort_values(by="Today's Volume", ascending=False)
                
                st.dataframe(
                    intraday_picks.style.map(
                        lambda x: 'color: green; font-weight: bold' if isinstance(x, (int, float)) and x > 0 else 'color: red' if isinstance(x, (int, float)) and x < 0 else '',
                        subset=['Intraday Change %']
                    ),
                    use_container_width=True
                )
                
                st.info("💡 **Trading Tip:** P/E aur Debt/Equity aapko long-term aur swing mein madad karenge, par intraday ke liye sabse upar dikhne wale (High Volume + Positive Change) stocks par nazar rakhein.")
                
    except Exception as e:
        st.error(f"❌ Connection Error: {e}. Kripya check karein ki Streamlit Secrets mein access token sahi se configure hai.")
else:
    st.info("👆 Upar apni Google Sheet ka link daalein analysis shuru karne ke liye.")
