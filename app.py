import streamlit as st
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import time
from datetime import datetime

# ==========================================
# PAGE CONFIGURATION & ARGON CSS THEME
# ==========================================
st.set_page_config(page_title="Feedback360 Dashboard", layout="wide", initial_sidebar_state="expanded")

# Injecting Argon Dashboard CSS styles[cite: 6]
st.markdown("""
<style>
    /* Reset background to light gray and hide default top padding */
    .stApp { background-color: #f8f9fe; }
    .block-container { padding-top: 2rem !important; max-width: 95% !important; }
    
    /* The Purple Gradient Header Background */
    .stApp::before {
        content: "";
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 350px;
        background: linear-gradient(87deg, #5e72e4 0, #825ee4 100%) !important;
        z-index: 0;
    }

    /* Style the Sidebar to match */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        box-shadow: 0 0 2rem 0 rgba(136,152,170,.15);
        border-right: 1px solid #e9ecef;
    }

    /* Argon KPI Card Styling */
    .argon-card {
        background-color: #ffffff;
        border-radius: 0.375rem;
        box-shadow: 0 0 2rem 0 rgba(136,152,170,.15);
        padding: 1.5rem;
        position: relative;
        margin-bottom: 2rem;
        z-index: 1;
    }
    .argon-title {
        color: #8898aa;
        font-family: sans-serif;
        font-size: 0.8125rem;
        font-weight: 600;
        text-transform: uppercase;
        margin-bottom: 0.5rem;
    }
    .argon-value {
        color: #32325d;
        font-size: 2rem;
        font-weight: 600;
        font-family: sans-serif;
        margin: 0;
    }
    .argon-icon {
        width: 3rem;
        height: 3rem;
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        color: #ffffff;
        font-size: 1.5rem;
        position: absolute;
        top: 1.5rem;
        right: 1.5rem;
        box-shadow: 0 0 2rem 0 rgba(136,152,170,.15);
    }
    /* Icon Colors */
    .bg-danger { background: linear-gradient(87deg, #f5365c 0, #f56036 100%); }
    .bg-warning { background: linear-gradient(87deg, #fb6340 0, #fbb140 100%); }
    .bg-success { background: linear-gradient(87deg, #2dce89 0, #2dcecc 100%); }
    .bg-info { background: linear-gradient(87deg, #11cdef 0, #1171ef 100%); }
    
    /* Header Text above cards */
    .dashboard-header {
        color: white;
        font-family: sans-serif;
        font-weight: 600;
        font-size: 1.5rem;
        margin-bottom: 2rem;
        position: relative;
        z-index: 1;
    }
</style>
""", unsafe_allow_html=True)

# Helper function to generate Argon HTML cards
def render_argon_card(title, value, icon, bg_color):
    html = f"""
    <div class="argon-card">
        <div class="argon-title">{title}</div>
        <div class="argon-value">{value}</div>
        <div class="argon-icon {bg_color}">{icon}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


# ==========================================
# MODULE 1: NLP ANNOTATION ENGINE
# ==========================================
analyzer = SentimentIntensityAnalyzer()

def annotate_sentiment(text):
    score = analyzer.polarity_scores(text)['compound']
    if score >= 0.05: return "Positive"
    elif score <= -0.05: return "Negative"
    else: return "Neutral"

if 'feedback_db' not in st.session_state:
    st.session_state.feedback_db = pd.DataFrame(columns=["Timestamp", "Product", "Channel", "Text", "Sentiment"])

# ==========================================
# MODULE 2: DATA INGESTION & SIDEBAR
# ==========================================
# Header Title over the purple background
st.markdown('<div class="dashboard-header">Feedback360 Analytics Engine</div>', unsafe_allow_html=True)

st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/b/b2/Bootstrap_logo.svg/256px-Bootstrap_logo.svg.png", width=50)
st.sidebar.markdown("### Data Controls")

demo_products = ["Mobile App", "Wireless Earbuds", "Web Dashboard", "Payment Gateway"]

# Global Filter moved to sidebar
st.sidebar.markdown("#### 🔍 Filter View")
selected_filter = st.sidebar.selectbox("Select Dashboard Scope", ["All Products"] + demo_products)
st.sidebar.markdown("---")

with st.sidebar.form(key='live_feedback'):
    st.markdown("##### Manual Event Entry")
    product_sel = st.selectbox("Product", demo_products)
    channel_sel = st.selectbox("Channel", ["In-Person Survey", "Support Logs", "Social Media"])
    live_text = st.text_area("Feedback Payload:")
    submit_btn = st.form_submit_button(label='Push Event')

    if submit_btn and live_text:
        sentiment = annotate_sentiment(live_text)
        new_entry = pd.DataFrame([{
            "Timestamp": datetime.now().strftime("%H:%M:%S"),
            "Product": product_sel, "Channel": channel_sel,
            "Text": live_text, "Sentiment": sentiment
        }])
        st.session_state.feedback_db = pd.concat([new_entry, st.session_state.feedback_db], ignore_index=True)

if st.sidebar.button("🌊 Inject Kafka Batch Stream", use_container_width=True):
    batch_data = [
        {"Product": "Mobile App", "Channel": "Social Media", "Text": "The new update is incredibly fast and smooth. Love it!"},
        {"Product": "Mobile App", "Channel": "Support Logs", "Text": "This is completely broken and terrible. I hate the new design."},
        {"Product": "Web Dashboard", "Channel": "Social Media", "Text": "Okay experience, nothing special but it works."},
        {"Product": "Wireless Earbuds", "Channel": "In-Person Survey", "Text": "Customer service was very helpful replacing my order."},
        {"Product": "Wireless Earbuds", "Channel": "Support Logs", "Text": "Awful battery life, completely useless. Highly disappointed."}
    ]
    with st.spinner('Running NLP processing...'):
        time.sleep(1)
        for item in batch_data:
            sentiment = annotate_sentiment(item["Text"])
            new_entry = pd.DataFrame([{
                "Timestamp": datetime.now().strftime("%H:%M:%S"),
                "Product": item["Product"], "Channel": item["Channel"],
                "Text": item["Text"], "Sentiment": sentiment
            }])
            st.session_state.feedback_db = pd.concat([new_entry, st.session_state.feedback_db], ignore_index=True)

# ==========================================
# MODULE 3: UNIFIED VISUALIZATION
# ==========================================
# Apply global filter logic
if selected_filter == "All Products":
    display_db = st.session_state.feedback_db
else:
    display_db = st.session_state.feedback_db[st.session_state.feedback_db['Product'] == selected_filter]

if not display_db.empty:
    
    # 4 Argon KPI Cards (matching the image)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_argon_card("Total Traffic", len(display_db), "📈", "bg-danger")
    with col2:
        pos_count = len(display_db[display_db['Sentiment'] == 'Positive'])
        render_argon_card("Positive Feedback", pos_count, "👍", "bg-success")
    with col3:
        neg_count = len(display_db[display_db['Sentiment'] == 'Negative'])
        render_argon_card("Negative Feedback", neg_count, "👎", "bg-warning")
    with col4:
        neu_count = len(display_db[display_db['Sentiment'] == 'Neutral'])
        render_argon_card("Neutral Mentions", neu_count, "💬", "bg-info")

    st.markdown("<br>", unsafe_allow_html=True)

    # Charts Section
    c1, c2 = st.columns([2, 1])
    
    with c1:
        st.markdown('##### Sentiment Over Time (Volume)')
        # Group by timestamp to simulate a time-series line chart
        time_data = display_db.groupby('Timestamp').size()
        st.line_chart(time_data, height=350, use_container_width=True)

    with c2:
        st.markdown('##### Cross-Channel Distribution')
        chart_data = display_db.groupby(['Channel', 'Sentiment']).size().unstack(fill_value=0)
        st.bar_chart(chart_data, height=350, use_container_width=True)

    # Data Table Section
    st.markdown("---")
    st.markdown('##### 🗄️ Unified Event Store (Raw Payload)')
    st.dataframe(display_db, use_container_width=True, hide_index=True)

else:
    # Empty State placeholders mimicking the cards
    col1, col2, col3, col4 = st.columns(4)
    with col1: render_argon_card("Total Traffic", "0", "📈", "bg-danger")
    with col2: render_argon_card("Positive Feedback", "0", "👍", "bg-success")
    with col3: render_argon_card("Negative Feedback", "0", "👎", "bg-warning")
    with col4: render_argon_card("Neutral Mentions", "0", "💬", "bg-info")
    st.info("Pipeline is currently idle. Awaiting data ingestion events from the sidebar.")