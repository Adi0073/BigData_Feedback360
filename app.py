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
    """
    score = analyzer.polarity_scores(text)['compound']
    if score >= 0.05:
        return "Positive", "🟩"
    elif score <= -0.05:
        return "Negative", "🟥"
    else:
        return "Neutral", "🟨"

# Initialize local centralized storage with the new "Product" column
if 'feedback_db' not in st.session_state:
    st.session_state.feedback_db = pd.DataFrame(
        columns=["Timestamp", "Product", "Channel", "Text", "Sentiment", "Indicator"]
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

demo_products = ["Mobile App", "Web Dashboard", "Wireless Earbuds", "Payment Gateway"]

# Channel A: Live Web Form with Product Selection
with st.sidebar.form(key='live_feedback'):
    st.subheader("Manual Entry")
    product_sel = st.selectbox("Product Entity", demo_products)
    channel_sel = st.selectbox("Source", ["In-Person Survey", "Support Logs", "Social Media"])
    live_text = st.text_area("Enter Customer Feedback:")
    submit_btn = st.form_submit_button(label='Push to Pipeline')

    if submit_btn and live_text:
        sentiment, icon = annotate_sentiment(live_text)
        new_entry = pd.DataFrame([{
            "Timestamp": datetime.now().strftime("%H:%M:%S"),
            "Product": product_sel,
            "Channel": channel_sel,
            "Text": live_text,
            "Sentiment": sentiment,
            "Indicator": icon
        }])
        st.session_state.feedback_db = pd.concat([new_entry, st.session_state.feedback_db], ignore_index=True)
        st.sidebar.success("Event ingested successfully.")

# Channel B: Simulated High-Velocity Stream with Explicit Negative Events
st.sidebar.markdown("---")
if st.sidebar.button("🌊 Simulate Batch Stream"):
    batch_data = [
        {"Product": "Mobile App", "Channel": "Social Media", "Text": "The new update is incredibly fast and smooth. Love it!"},
        {"Product": "Mobile App", "Channel": "Support Logs", "Text": "This is completely broken and terrible. I hate the new design."},
        {"Product": "Web Dashboard", "Channel": "Social Media", "Text": "Okay experience, nothing special but it works."},
        {"Product": "Wireless Earbuds", "Channel": "In-Person Survey", "Text": "Customer service was very helpful replacing my order."},
        {"Product": "Wireless Earbuds", "Channel": "Support Logs", "Text": "Awful battery life, completely useless. Highly disappointed."}
    ]
    with st.spinner('Processing batch through annotation engine...'):
        time.sleep(1) # Simulating network/processing latency
        for item in batch_data:
            sentiment, icon = annotate_sentiment(item["Text"])
            new_entry = pd.DataFrame([{
                "Timestamp": datetime.now().strftime("%H:%M:%S"),
                "Product": item["Product"],
                "Channel": item["Channel"],
                "Text": item["Text"],
                "Sentiment": sentiment,
                "Indicator": icon
            }])
            st.session_state.feedback_db = pd.concat([new_entry, st.session_state.feedback_db], ignore_index=True)

# ==========================================
# MODULE 3: UNIFIED VISUALIZATION & FILTERING
# ==========================================
if not st.session_state.feedback_db.empty:
    
    # --- PRODUCT FILTER DRIVER ---
    st.subheader("🔍 Filter by Product")
    all_products = ["All Products"] + list(st.session_state.feedback_db['Product'].unique())
    selected_filter = st.selectbox("Select a product to view specific analytics:", all_products)
    
    # Apply the filter to a display dataframe
    if selected_filter == "All Products":
        display_db = st.session_state.feedback_db
    else:
        display_db = st.session_state.feedback_db[st.session_state.feedback_db['Product'] == selected_filter]
    
    st.markdown("---")
    
    # Metrics based on filtered data
    col1, col2, col3 = st.columns(3)
    col1.metric(f"Total Events ({selected_filter})", len(display_db))
    col2.metric("Positive Events", len(display_db[display_db['Sentiment'] == 'Positive']))
    col3.metric("Negative Events", len(display_db[display_db['Sentiment'] == 'Negative']))

    # Chart based on filtered data
    st.subheader(f"📊 Sentiment Distribution: {selected_filter}")
    if not display_db.empty:
        chart_data = display_db.groupby(['Channel', 'Sentiment']).size().unstack(fill_value=0)
        st.bar_chart(chart_data)
    else:
        st.info("No data available for this specific product.")

    # Table based on filtered data
    st.subheader("🗄️ Unified Event Store (Annotated)")
    st.dataframe(display_db, use_container_width=True)
else:
    st.info("Pipeline idle. Awaiting data ingestion from sidebar.")