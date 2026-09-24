import streamlit as st
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import time
from datetime import datetime

# ==========================================
# MODULE 1: NLP ANNOTATION ENGINE
# ==========================================
analyzer = SentimentIntensityAnalyzer()

def annotate_sentiment(text):
    """
    Analyzes raw text using VADER and returns a categorized sentiment and UI icon.
    Future Scope (Review 4): This logic will be migrated to Apache Spark workers.
    """
    score = analyzer.polarity_scores(text)['compound']
    if score >= 0.05:
        return "Positive", "🟩"
    elif score <= -0.05:
        return "Negative", "🟥"
    else:
        return "Neutral", "🟨"

# Initialize local centralized storage (Simulating MongoDB for the 50% MVP)
if 'feedback_db' not in st.session_state:
    st.session_state.feedback_db = pd.DataFrame(
        columns=["Timestamp", "Channel", "Text", "Sentiment", "Indicator"]
    )

# ==========================================
# UI CONFIGURATION & HEADER
# ==========================================
st.set_page_config(page_title="Feedback360 Demo", layout="wide")
st.title("🔄 Feedback360: Multi-Channel Analytical View")
st.markdown("Prototype Pipeline: Centralizing and annotating cross-channel feedback.")

# ==========================================
# MODULE 2: DATA INGESTION LAYER
# ==========================================
st.sidebar.header("📥 Ingestion Channels")

# Channel A: Live Web Form
with st.sidebar.form(key='live_feedback'):
    st.subheader("Manual Entry")
    live_text = st.text_area("Enter Customer Feedback:")
    channel_sel = st.selectbox("Source", ["In-Person Survey", "Support Logs", "Social Media"])
    submit_btn = st.form_submit_button(label='Push to Pipeline')

    if submit_btn and live_text:
        sentiment, icon = annotate_sentiment(live_text)
        new_entry = pd.DataFrame([{
            "Timestamp": datetime.now().strftime("%H:%M:%S"),
            "Channel": channel_sel,
            "Text": live_text,
            "Sentiment": sentiment,
            "Indicator": icon
        }])
        st.session_state.feedback_db = pd.concat([new_entry, st.session_state.feedback_db], ignore_index=True)
        st.sidebar.success("Event ingested successfully.")

# Channel B: Simulated High-Velocity Stream (Kafka Stand-in)
st.sidebar.markdown("---")
if st.sidebar.button("🌊 Simulate Batch Stream"):
    batch_data = [
        {"Channel": "Social Media", "Text": "The new update is incredibly fast and smooth. Love it!"},
        {"Channel": "Support Logs", "Text": "System keeps crashing on my device. Unusable."},
        {"Channel": "Social Media", "Text": "Okay experience, nothing special but it works."},
        {"Channel": "In-Person Survey", "Text": "Customer service was very helpful replacing my order."}
    ]
    with st.spinner('Processing batch through annotation engine...'):
        time.sleep(1) # Simulating network/processing latency
        for item in batch_data:
            sentiment, icon = annotate_sentiment(item["Text"])
            new_entry = pd.DataFrame([{
                "Timestamp": datetime.now().strftime("%H:%M:%S"),
                "Channel": item["Channel"],
                "Text": item["Text"],
                "Sentiment": sentiment,
                "Indicator": icon
            }])
            st.session_state.feedback_db = pd.concat([new_entry, st.session_state.feedback_db], ignore_index=True)

# ==========================================
# MODULE 3: UNIFIED VISUALIZATION
# ==========================================
if not st.session_state.feedback_db.empty:
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Events Ingested", len(st.session_state.feedback_db))
    col2.metric("Positive Events", len(st.session_state.feedback_db[st.session_state.feedback_db['Sentiment'] == 'Positive']))
    col3.metric("Negative Events", len(st.session_state.feedback_db[st.session_state.feedback_db['Sentiment'] == 'Negative']))

    st.subheader("📊 Cross-Channel Sentiment Distribution")
    chart_data = st.session_state.feedback_db.groupby(['Channel', 'Sentiment']).size().unstack(fill_value=0)
    st.bar_chart(chart_data)

    st.subheader("🗄️ Unified Event Store (Annotated)")
    st.dataframe(st.session_state.feedback_db, use_container_width=True)
else:
    st.info("Pipeline idle. Awaiting data ingestion from sidebar.")