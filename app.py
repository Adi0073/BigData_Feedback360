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

demo_products = ["Mobile App", "Wireless Earbuds", "Web Dashboard", "Payment Gateway"]

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
        st.sidebar.success(f"Event ingested for {product_sel}.")

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
        time.sleep(1)
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
# MODULE 3: UNIFIED VISUALIZATION & TABS
# ==========================================
if not st.session_state.feedback_db.empty:
    st.subheader("📊 Product-Specific Analytics")
    
    # Get all unique products currently in the database
    unique_products = list(st.session_state.feedback_db['Product'].unique())
    
    # Create tabs dynamically based on the products present
    tabs = st.tabs(["Overview (All Products)"] + unique_products)
    
    # --- TAB 0: OVERVIEW (ALL PRODUCTS) ---
    with tabs[0]:
        display_db = st.session_state.feedback_db
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Events (Global)", len(display_db))
        col2.metric("Positive Events", len(display_db[display_db['Sentiment'] == 'Positive']))
        col3.metric("Negative Events", len(display_db[display_db['Sentiment'] == 'Negative']))

        chart_data = display_db.groupby(['Channel', 'Sentiment']).size().unstack(fill_value=0)
        st.bar_chart(chart_data)
        st.dataframe(display_db, use_container_width=True)

    # --- TABS 1 to N: INDIVIDUAL PRODUCTS ---
    for i, prod in enumerate(unique_products, start=1):
        with tabs[i]:
            # Filter database for just this specific product
            prod_db = st.session_state.feedback_db[st.session_state.feedback_db['Product'] == prod]
            
            c1, c2, c3 = st.columns(3)
            c1.metric(f"Total Events ({prod})", len(prod_db))
            c2.metric("Positive Events", len(prod_db[prod_db['Sentiment'] == 'Positive']))
            c3.metric("Negative Events", len(prod_db[prod_db['Sentiment'] == 'Negative']))
            
            if not prod_db.empty:
                chart_data = prod_db.groupby(['Channel', 'Sentiment']).size().unstack(fill_value=0)
                st.bar_chart(chart_data)
                st.dataframe(prod_db, use_container_width=True)
else:
    st.info("Pipeline idle. Awaiting data ingestion from sidebar.")