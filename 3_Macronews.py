import streamlit as st
import requests
import xml.etree.ElementTree as ET
import urllib.parse
import time

st.set_page_config(layout="wide")
st.title("🌐 Macro-Market Sentinel")
st.subheader("National & Global Market Moving News Radar")

# --- TELEGRAM SENDER ---
def send_telegram_alert(message):
    BOT_TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]
    CHAT_ID = "299717233"
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try: 
        requests.post(url, json={"chat_id": CHAT_ID, "text": message}, timeout=15)
    except: pass

# --- GLOBAL NEWS FETCH ENGINE ---
def fetch_big_news():
    # Big Movement wali news ke keywords (Inhe "Alpha Keywords" kehte hain)
    queries = [
        "RBI interest rate hike", "Nifty market outlook", 
        "Global stock market crash", "US Inflation data", 
        "Crude oil prices movement", "Budget 2026 impact"
    ]
    
    all_alerts = []
    for q in queries:
        encoded_q = urllib.parse.quote(q)
        url = f"https://news.google.com/rss/search?q={encoded_q}&hl=en-IN&gl=IN&ceid=IN:en"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                for item in root.findall('.//item')[:1]: # Har keyword se sirf 1 top headline
                    all_alerts.append(f"🌍 **{q.upper()}**: {item.find('title').text}\n🔗 {item.find('link').text}")
        except: continue
    return all_alerts

# --- UI CONTROLS ---
if st.button("🚨 SCAN GLOBAL & NATIONAL MARKETS"):
    with st.spinner("Scanning World Wide News..."):
        news = fetch_big_news()
        if news:
            for n in news:
                st.info(n)
                send_telegram_alert(n)
        else:
            st.warning("Market is currently stable.")

# --- AUTOMATED BACKGROUND MONITOR ---
if st.sidebar.checkbox("Activate 24/7 Global Sentinel"):
    st.success("Monitoring ON. Alerts will be sent if major news hits.")
    # Har 30 minute mein scan
    news = fetch_big_news()
    if news:
        for n in news:
            send_telegram_alert(n)
    time.sleep(1800) 
    st.rerun()