import streamlit as st
import pandas as pd
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import xml.etree.ElementTree as ET
import urllib.parse
import time

# --- CONFIGURATION (Streamlit Secrets) ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1BHnQm0nYwl3paJ9PUEfHPlzMBLLXdpCZtdC59SFma58/edit?gid=0#gid=0"

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

# --- GOOGLE NEWS EARNINGS FETCH ENGINE ---
def fetch_quarter_news(stock_name):
    search_query = f"{stock_name} (quarterly results OR earnings OR Q1 OR Q2 OR Q3 OR Q4)"
    encoded_query = urllib.parse.quote(search_query)
    
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-IN&gl=IN&ceid=IN:en"
    
    news_list = []
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            for item in root.findall('.//item')[:3]:
                title = item.find('title').text
                link = item.find('link').text
                pub_date = item.find('pubDate').text
                
                keywords = ['result', 'earning', 'profit', 'loss', 'revenue', 'quarter', 'q1', 'q2', 'q3', 'q4', 'margin']
                if any(kw in title.lower() for kw in keywords):
                    news_list.append({"title": title, "link": link, "date": pub_date})
    except Exception as e:
        pass
    return news_list

# --- CORE NEWS SCANNER LOGIC ---
def run_news_radar():
    sheet = get_google_sheet()
    if not sheet: 
        return
    
    records = sheet.get_all_records()
    df_sheet = pd.DataFrame(records)
    if df_sheet.empty or 'Symbol' not in df_sheet.columns: 
        return
    
    symbols = [str(s).split('.')[0].strip() for s in df_sheet['Symbol'].dropna().tolist() if str(s).strip()]
    
    st.markdown("### 🎯 Live Watchlist Headlines")
    
    for sym in symbols:
        news_found = fetch_quarter_news(sym)
        
        if news_found:
            with st.expander(f"🟢 **{sym}** - New Headlines Found! ({len(news_found)})", expanded=True):
                for idx, news in enumerate(news_found):
                    st.markdown(f"**{idx+1}. {news['title']}**")
                    st.caption(f"📅 {news['date'][:16]}")
                    st.markdown(f"🔗 [Read Full Article]({news['link']})")
                    if idx < len(news_found) - 1:
                        st.divider()
            time.sleep(1)
        else:
            st.text(f"⚪ {sym}: No recent quarterly headlines found.")

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
    st.info("🔄 **Auto-Pilot News Mode ON:** The system is continuously rendering fresh content on your display panel below.")
    run_news_radar()
    
    st.success("Watchlist loop complete! Next display update in 1 hour.")
    time.sleep(3600) 
    st.rerun()
else:
    st.warning("Automated News Engine is paused. Click 'Start Live News Radar' to fetch current trends.")
