import streamlit as st

# 1. Sabse upar Page Configuration set karein
st.set_page_config(
    page_title="Lovish Market Navigator",
    page_icon="📈",
    layout="wide"
)

# 2. Clean Welcome Screen Dashboard UI
st.title("👋 Namaste Lovish!")
st.subheader("Aapka Personal Institutional Trading Dashboard")

st.markdown("""
---
Yeh system aapke liye market ke live trends, smart money flow, aur 
institutional signals ko 24/7 monitor kar raha hai. 

**Sidebar se apne tools select karein:**
1. **Intraday Engine:** 📈 SuperTrend + RSI + Volume Scanner (Google Sheets)
2. **Quarterly Results Radar:** 📰 Earnings aur Profit Guidance
3. **Macro News Sentinel:** 🌐 Global market big movements
4. **Deep Quant Analysis:** 📊 Institutional accumulation matrix
5. **Sector Heatmap:** 🌡️ Smart money rotation tracker
---
""")

# Quick Status Panel Layout
col1, col2 = st.columns(2)

with col1:
    st.info("💡 **Pro Tip:** Jab 'Deep Quant' aur 'Sector Heatmap' dono 'Bullish' dikhayein, tab trade lene ke chances sabse best hote hain.")

with col2:
    st.warning("🛡️ **System Status:** Automation Engines are Ready & Waiting.")

st.balloons()
