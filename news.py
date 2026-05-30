import streamlit as st
import feedparser
import pandas as pd
from datetime import datetime
from time import mktime

# ==========================================
# 1. SETUP & CONFIGURATION
# ==========================================
st.set_page_config(page_title="Intraday Live News", page_icon="⚡", layout="wide")

st.title("⚡ Live Intraday Market News Dashboard")
st.caption("Auto-sorted: Showing the absolute newest headlines at the top.")

# Faster, more reliable Indian Stock Market Feeds
RSS_FEEDS = {
    "Livemint (Markets)": "https://www.livemint.com/rss/markets",
    "Moneycontrol (Market Reports)": "https://www.moneycontrol.com/rss/marketreports.xml",
    "Moneycontrol (Latest)": "https://www.moneycontrol.com/rss/latestnews.xml",
    "Economic Times (Markets)": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms"
}

# ==========================================
# 2. DATA FETCHING & SORTING ENGINE
# ==========================================
@st.cache_data(ttl=60) # Cache clears every 60 seconds
def fetch_news(feed_url):
    feed = feedparser.parse(feed_url)
    news_list = []
    
    for entry in feed.entries:
        # Extract precise time and convert to Python Datetime object
        try:
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                pub_time = datetime.fromtimestamp(mktime(entry.published_parsed))
            else:
                pub_time = datetime.now()
        except:
            pub_time = datetime.now()

        news_list.append({
            "Title": entry.title,
            "Published_DT": pub_time, # Hidden column for sorting
            "Published_Str": pub_time.strftime("%d %b %Y, %I:%M %p"), # For display
            "Link": entry.link
        })
    
    df = pd.DataFrame(news_list)
    
    # 🔴 CORE FIX: Sort by Date & Time (Newest exactly at the top)
    if not df.empty:
        df = df.sort_values(by="Published_DT", ascending=False).head(15)
        
    return df

# ==========================================
# 3. INTERFACE LAYOUT
# ==========================================
col1, col2 = st.columns([1, 2.5])

with col1:
    st.subheader("⚙️ Select News Feed")
    selected_feed = st.radio("Choose Source:", list(RSS_FEEDS.keys()))
    
    st.info("💡 **Pro Tip for Intraday:**\nDon't buy just because the news is good. Wait for a breakout on the 5-min or 15-min chart first.")
    
    if st.button("🔄 Refresh News", type="primary"):
        st.cache_data.clear()
        st.rerun()

with col2:
    st.subheader(f"📰 Latest Updates: {selected_feed}")
    
    with st.spinner("Fetching and sorting live market data..."):
        df_news = fetch_news(RSS_FEEDS[selected_feed])
        
        if not df_news.empty:
            for idx, row in df_news.iterrows():
                # Displaying News securely
                st.markdown(f"#### 🔹 {row['Title']}")
                st.caption(f"🕒 Time: {row['Published_Str']}")
                st.markdown(f"[🔗 Read full article]({row['Link']})")
                st.divider()
        else:
            st.warning("⚠️ No news fetched. Check your internet connection or the feed link.")