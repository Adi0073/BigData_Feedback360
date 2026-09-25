import streamlit as st
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import time
from datetime import datetime

# ==========================================
# BOOTSTRAP 5 & CUSTOM CSS INJECTION
# ==========================================
st.set_page_config(page_title="Feedback360 Dashboard", layout="wide", initial_sidebar_state="expanded")

# Inject Bootstrap 5 CDN and custom dark-theme overrides
st.markdown("""
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<style>
    /* Streamlit overrides to make it look more like a web app */
    .block-container { padding-top: 2rem !important; }
    
    /* Custom KPI Card Styling */
    .kpi-card {
        background-color: #1E1E1E; 
        border-radius: 8px; 
        padding: 20px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        margin-bottom: 20px;
    }
    .kpi-title { color: #A0AEC0; font-size: 0.9rem; font-weight: 600; text-transform: uppercase; margin-bottom: 8px; }
    .kpi-value { font-size: 2rem; font-weight: 700; margin: 0; }
    
    /* Border accents for sentiment */
    .border-blue { border-left: 5px solid #0d6efd; }
    .border-green { border-left: 5px solid #198754; }
    .border-red { border-left: 5px solid #dc3545; }
</style>
""", unsafe_allow_html=True)

# Helper function to render Bootstrap KPI Cards
def render_kpi_card(title, value, border_class, text_color):
    html = f"""
    <div class="kpi-card {border_class}">
        <div class="kpi-title">{title}</div>
        <div class="kpi-value" style="color: {text_color};">{value}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

# ==========================================
# MODULE 1: NLP ANNOTATION ENGINE
# ==========================================
analyzer = SentimentIntensityAnalyzer()

def annotate_sentiment(text):
    score = analyzer.polarity_scores(text)['compound']
    if score >= 0.05:
        return "Positive", "🟩"
    elif score <= -0.05:
        return "Negative", "🟥"
    else:
        return "Neutral", "🟨"

if 'feedback_db' not in st.session_state:
    st.session_state.feedback_db = pd.DataFrame(columns=["Timestamp", "Product", "Channel", "Text", "Sentiment", "Indicator"])

# ==========================================
# UI HEADER
# ==========================================
st.markdown("""
<div style="background-color: #0d6efd; padding: 20px; border-radius: 10px; margin-bottom: 30px;">
    <h2 style="color: white; margin: 0;">🔄 Feedback360 Enterprise Dashboard</h2>
    <p style="color: #e9ecef; margin: 0;">Scalable Multi-Channel Analytics & Sentiment Ingestion</p>
</div>
""", unsafe_allow_html=True)

# ==========================================
# MODULE 2: DATA INGESTION LAYER
# ==========================================
st.sidebar.markdown("### 📥 Pipeline Ingestion")

demo_products = ["Mobile App", "Wireless Earbuds", "Web Dashboard", "Payment Gateway"]

with st.sidebar.form(key='live_feedback'):
    st.markdown("##### Manual Event Entry")
    product_sel = st.selectbox("Product Entity", demo_products)
    channel_sel = st.selectbox("Source Channel", ["In-Person Survey", "Support Logs", "Social Media"])
    live_text = st.text_area("Customer Feedback payload:")
    submit_btn = st.form_submit_button(label='Push Event to Pipeline')

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
        st.sidebar.success(f"Successfully routed to {product_sel} data lake.")

st.sidebar.markdown("---")
if st.sidebar.button("🌊 Inject Kafka Batch Stream", use_container_width=True):
    batch_data = [
        {"Product": "Mobile App", "Channel": "Social Media", "Text": "The new update is incredibly fast and smooth. Love it!"},
        {"Product": "Mobile App", "Channel": "Support Logs", "Text": "This is completely broken and terrible. I hate the new design."},
        {"Product": "Web Dashboard", "Channel": "Social Media", "Text": "Okay experience, nothing special but it works."},
        {"Product": "Wireless Earbuds", "Channel": "In-Person Survey", "Text": "Customer service was very helpful replacing my order."},
        {"Product": "Wireless Earbuds", "Channel": "Support Logs", "Text": "Awful battery life, completely useless. Highly disappointed."}
    ]
    with st.spinner('Running NLP processing across batch...'):
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
    
    unique_products = list(st.session_state.feedback_db['Product'].unique())
    tabs = st.tabs(["🌐 Global Overview"] + [f"📦 {p}" for p in unique_products])
    
    # --- TAB 0: OVERVIEW ---
    with tabs[0]:
        st.markdown("<br>", unsafe_allow_html=True)
        display_db = st.session_state.feedback_db
        
        # Bootstrap KPI Cards
        col1, col2, col3 = st.columns(3)
        with col1:
            render_kpi_card("Total Ingested Events", len(display_db), "border-blue", "#ffffff")
        with col2:
            pos_count = len(display_db[display_db['Sentiment'] == 'Positive'])
            render_kpi_card("Positive Sentiment", pos_count, "border-green", "#198754")
        with col3:
            neg_count = len(display_db[display_db['Sentiment'] == 'Negative'])
            render_kpi_card("Negative Sentiment", neg_count, "border-red", "#dc3545")

        st.markdown("#### 📊 Cross-Channel Distribution Matrix")
        chart_data = display_db.groupby(['Channel', 'Sentiment']).size().unstack(fill_value=0)
        st.bar_chart(chart_data, use_container_width=True)
        
        st.markdown("#### 🗄️ Raw Event Store")
        st.dataframe(display_db, use_container_width=True, hide_index=True)

    # --- TABS 1 to N: INDIVIDUAL PRODUCTS ---
    for i, prod in enumerate(unique_products, start=1):
        with tabs[i]:
            st.markdown("<br>", unsafe_allow_html=True)
            prod_db = st.session_state.feedback_db[st.session_state.feedback_db['Product'] == prod]
            
            c1, c2, c3 = st.columns(3)
            with c1:
                render_kpi_card(f"{prod} Events", len(prod_db), "border-blue", "#ffffff")
            with c2:
                render_kpi_card("Positive", len(prod_db[prod_db['Sentiment'] == 'Positive']), "border-green", "#198754")
            with c3:
                render_kpi_card("Negative", len(prod_db[prod_db['Sentiment'] == 'Negative']), "border-red", "#dc3545")
            
            if not prod_db.empty:
                chart_data = prod_db.groupby(['Channel', 'Sentiment']).size().unstack(fill_value=0)
                st.bar_chart(chart_data, use_container_width=True)
                st.dataframe(prod_db, use_container_width=True, hide_index=True)
else:
    st.info("Pipeline is currently idle. Awaiting data ingestion events from the sidebar.")