import streamlit as st
import pandas as pd
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import xml.etree.ElementTree as ET
import urllib.parse
import time

# --- CONFIGURATION (Streamlit Secrets) ---
BOT_TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]  
CHAT_ID = "299717233"      
SHEET_URL = "https://docs.google.com/spreadsheets/d/1BHnQm0nYwl3paJ9PUEfHPlzMBLLXdpCZtdC59SFma58/edit?gid=0#gid=0"  # Apni sheet ka link yahan dalein

st.set_page_config(layout="wide")
st.title("📰 Institutional Earnings & Quarter News Radar")
st.subheader("Google Sheet Watchlist Live Results Sentiment Engine")

if "news_scan" not in st.session_state:
    st.session_state.news_scan = False

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

# --- GOOGLE NEWS EARNINGS FETCH ENGINE ---
def fetch_quarter_news(stock_name):
    # Sirf kaam ki news nikalne ke liye keywords set kiye hain
    search_query = f"{stock_name} (quarterly results OR earnings OR Q1 OR Q2 OR Q3 OR Q4)"
    encoded_query = urllib.parse.quote(search_query)
    
    # RSS Feed URL from Google News (India Region)
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-IN&gl=IN&ceid=IN:en"
    
    news_list = []
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            # Sirf top 3 sabse taza news nikalenge taaki faltu kachra na aaye
            for item in root.findall('.//item')[:3]:
                title = item.find('title').text
                link = item.find('link').text
                pub_date = item.find('pubDate').text
                
                # Filter: Pakka karne ke liye ki khabar results ke baare mein hi hai
                keywords = ['result', 'earning', 'profit', 'loss', 'revenue', 'quarter', 'q1', 'q2', 'q3', 'q4', 'margin']
                if any(kw in title.lower() for kw in keywords):
                    news_list.append({"title": title, "link": link, "date": pub_date})
    except Exception as e:
        pass
    return news_list

# --- CORE NEWS SCANNER LOGIC ---
def run_news_radar():
    sheet = get_google_sheet()
    if not sheet: return
    
    records = sheet.get_all_records()
    df_sheet = pd.DataFrame(records)
    if df_sheet.empty or 'Symbol' not in df_sheet.columns: return
    
    # .NS ya .BO hata kar saaf naam nikalna (jaise SBIN.NS ka sirf SBIN)
    symbols = [str(s).split('.')[0].strip() for s in df_sheet['Symbol'].dropna().tolist() if str(s).strip()]
    
    for sym in symbols:
        with st.spinner(f"Analyzing headlines for {sym}..."):
            news_found = fetch_quarter_news(sym)
            
            if news_found:
                # Telegram ke liye sunder format message banana
                msg = f"📰 ✨ **QUARTER RESULT RADAR: {sym}** ✨\n\n"
                for idx, news in enumerate(news_found):
                    msg += f"{idx+1}. {news['title']}\n📅 {news['date'][:16]}\n🔗 Link: {news['link']}\n\n"
                
                send_telegram_alert(msg)
                st.success(f"🟢 {sym} ke results ki news Telegram par bhej di gayi hai!")
                time.sleep(2) # API hit control karne ke liye break
            else:
                st.text(f"⚪ {sym}: Filhal aane wale results ko lekar koi tazi headline nahi hai.")

# --- SIDEBAR CONTROL PANEL ---
st.sidebar.header("🕹️ News Controller")
if st.sidebar.button("🟢 Start Live News Radar", type="primary"):
    st.session_state.news_scan = True
    st.sidebar.success("News Automation Active!")

if st.sidebar.button("🔴 Stop News Radar"):
    st.session_state.news_scan = False
    st.sidebar.warning("News Radar Paused.")

# --- RUN ENGINE AUTOMATION ---
if st.session_state.news_scan:
    st.info("🔄 **Auto-Pilot News Mode ON:** Yeh system har 1 ghante (ya aapke set time) baad Google Sheet ke stocks ki corporate news scan karega.")
    run_news_radar()
    
    # Earnings news din mein 1-2 baar hi aati hai, isliye ise har 1 ghante (3600 seconds) par chalana best hai
    st.success("Watchlist complete! Agla automatic news scan 1 ghante baad hoga.")
    time.sleep(3600) 
    st.rerun()
else:
    st.warning("Automated News Engine abhi rukka hua hai. Chalu karne ke liye 'Start Live News Radar' dabayein.")