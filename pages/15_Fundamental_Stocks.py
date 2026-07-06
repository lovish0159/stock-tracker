import streamlit as st
import pandas as pd
import yfinance as yf

# Page Setup
st.set_page_config(page_title="Intraday & Fundamental Screener", layout="wide")
st.title("📈 Custom Stock Screener for Intraday & Swing")
st.markdown("Yeh app aapki Google Sheet se stocks pick karke unka analysis karti hai.")

# Google Sheet Link Input
sheet_url = st.text_input(
    "Apni Google Sheet ka CSV Link yahan paste karein:", 
    placeholder="https://docs.google.com/spreadsheets/d/.../export?format=csv"
)

if sheet_url:
    try:
        # Sheet se data padhna
        df = pd.read_csv(sheet_url)
        
        if 'Symbol' not in df.columns:
            st.error("❌ Google Sheet mein 'Symbol' naam ka column hona zaroori hai!")
        else:
            st.success("✅ Sheet successfully connect ho gayi!")
            
            # Har stock ka data nikalne ka logic
            stock_data = []
            
            with st.spinner("Market data fetch kiya ja raha hai..."):
                for symbol in df['Symbol']:
                    try:
                        ticker = yf.Ticker(symbol)
                        info = ticker.info
                        
                        # Data extraction
                        current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
                        prev_close = info.get('previousClose', 1)
                        intraday_change = ((current_price - prev_close) / prev_close) * 100
                        
                        stock_data.append({
                            "Stock": symbol.replace('.NS', '').replace('.BO', ''),
                            "Price (₹)": current_price,
                            "Intraday Change %": round(intraday_change, 2),
                            "Today's Volume": info.get('volume', 'N/A'),
                            "P/E Ratio": info.get('trailingPE', 'N/A'),
                            "Market Cap (Cr)": round(info.get('marketCap', 0) / 10000000, 2) if info.get('marketCap') else 'N/A',
                            "52W High": info.get('fiftyTwoWeekHigh', 'N/A'),
                            "Debt/Equity": info.get('debtToEquity', 'N/A')
                        })
                    except Exception as e:
                        st.warning(f"{symbol} ka data nahi mil paya.")
            
            # Data ko table (DataFrame) mein badalna
            results_df = pd.DataFrame(stock_data)
            
            # Display Dashboard
            st.subheader("🚀 Live Market Analysis")
            
            # Highlight Intraday Picks (High Volume & Good Momentum)
            st.markdown("### 🎯 Today's Top Intraday Picks (High Volume & Momentum)")
            
            # Filter logic: Jiska volume jyada ho aur change positive ho
            if not results_df.empty:
                # Convert volume to numeric for filtering
                results_df['Today\'s Volume'] = pd.to_numeric(results_df['Today\'s Volume'], errors='coerce')
                
                # Sort by highest volume for intraday liquidity
                intraday_picks = results_df.sort_values(by='Today\'s Volume', ascending=False)
                
                # Show premium table
                st.dataframe(
                    intraday_picks.style.map(
                        lambda x: 'color: green; font-weight: bold' if isinstance(x, (int, float)) and x > 0 else 'color: red' if isinstance(x, (int, float)) and x < 0 else '',
                        subset=['Intraday Change %']
                    ),
                    use_container_width=True
                )
                
                st.info("💡 **Intraday Tip:** Intraday ke liye un stocks par focus karein jinka 'Today's Volume' unusually high ho aur price open hone ke baad strong momentum dikha raha ho. P/E aur Debt/Equity swing trades ke liye strong confidence dete hain.")
                
    except Exception as e:
        st.error(f"❌ Error aayi hai: {e}. Kripya apna Google Sheet link check karein.")
else:
    st.info("👆 Upar apni Google Sheet ka link daalein analysis shuru karne ke liye.")
