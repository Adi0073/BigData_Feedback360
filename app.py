import streamlit as st
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from groq import Groq
import time
from datetime import datetime

# ==========================================
# PAGE CONFIGURATION & STABLE CSS
# ==========================================
st.set_page_config(page_title="Feedback360 Dashboard", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .stApp { background-color: #f8f9fe; }
    .purple-header { background: linear-gradient(87deg, #5e72e4 0, #825ee4 100%); padding: 3rem 2rem 5rem 2rem; border-radius: 0 0 1rem 1rem; margin-top: -4rem; color: white; }
    .header-title { font-size: 2rem; font-weight: 600; margin-bottom: 0; }
    .header-sub { font-size: 1rem; opacity: 0.8; margin-top: 0; }
    .argon-card { background-color: #ffffff; border-radius: 0.5rem; box-shadow: 0 4px 6px rgba(50, 50, 93, 0.11), 0 1px 3px rgba(0, 0, 0, 0.08); padding: 1.5rem; display: flex; justify-content: space-between; align-items: center; margin-top: -3rem; margin-bottom: 2rem; border: 1px solid #e9ecef; }
    .argon-text-wrapper { display: flex; flex-direction: column; }
    .argon-title { color: #8898aa; font-size: 0.8rem; font-weight: 700; text-transform: uppercase; white-space: nowrap; }
    .argon-value { color: #32325d; font-size: 1.8rem; font-weight: 700; line-height: 1.2; }
    .argon-icon { width: 3rem; height: 3rem; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-size: 1.2rem; box-shadow: 0 4px 6px rgba(50, 50, 93, 0.11); flex-shrink: 0; }
    .bg-danger { background: linear-gradient(87deg, #f5365c, #f56036); }
    .bg-success { background: linear-gradient(87deg, #2dce89, #2dcecc); }
    .bg-warning { background: linear-gradient(87deg, #fb6340, #fbb140); }
    .bg-info { background: linear-gradient(87deg, #11cdef, #1171ef); }
</style>
""", unsafe_allow_html=True)

def render_argon_card(title, value, icon, bg_color):
    html = f'<div class="argon-card"><div class="argon-text-wrapper"><span class="argon-title">{title}</span><span class="argon-value">{value}</span></div><div class="argon-icon {bg_color}">{icon}</div></div>'
    st.markdown(html, unsafe_allow_html=True)

# ==========================================
# NLP & LLM ENGINES
# ==========================================
analyzer = SentimentIntensityAnalyzer()

def annotate_sentiment(text):
    score = analyzer.polarity_scores(text)['compound']
    if score >= 0.05: return "Positive"
    elif score <= -0.05: return "Negative"
    else: return "Neutral"

def generate_ai_summary(dataframe, api_key):
    try:
        client = Groq(api_key=api_key)
        # Convert the last 15 entries to a dictionary to avoid overloading the LLM context window
        data_sample = dataframe.tail(15).to_dict('records')
        prompt = f"Analyze this recent customer feedback data and provide a concise, 3-bullet point executive summary highlighting key issues and positive trends. Data: {data_sample}"
        
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-8b-8192",
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"API Error: Please check your Groq API key or network connection. ({str(e)})"

if 'feedback_db' not in st.session_state:
    st.session_state.feedback_db = pd.DataFrame(columns=["Timestamp", "Product", "Channel", "Text", "Sentiment"])

# ==========================================
# DATA INGESTION & SIDEBAR
# ==========================================
st.sidebar.markdown("### 🎛️ Data Controls")
groq_key = st.sidebar.text_input("Groq API Key (For GenAI Insights)", type="password")
st.sidebar.markdown("---")

demo_products = ["Mobile App", "Wireless Earbuds", "Web Dashboard", "Payment Gateway"]
selected_filter = st.sidebar.selectbox("Select Dashboard Scope", ["All Products"] + demo_products)
st.sidebar.markdown("---")

with st.sidebar.form(key='live_feedback'):
    st.markdown("##### 📝 Manual Event Entry")
    product_sel = st.selectbox("Product", demo_products)
    channel_sel = st.selectbox("Channel", ["In-Person Survey", "Support Logs", "Social Media"])
    live_text = st.text_area("Feedback Payload:")
    if st.form_submit_button('Push Event') and live_text:
        sentiment = annotate_sentiment(live_text)
        new_entry = pd.DataFrame([{"Timestamp": datetime.now().strftime("%H:%M:%S"), "Product": product_sel, "Channel": channel_sel, "Text": live_text, "Sentiment": sentiment}])
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
            new_entry = pd.DataFrame([{"Timestamp": datetime.now().strftime("%H:%M:%S"), "Product": item["Product"], "Channel": item["Channel"], "Text": item["Text"], "Sentiment": sentiment}])
            st.session_state.feedback_db = pd.concat([new_entry, st.session_state.feedback_db], ignore_index=True)

# ==========================================
# UNIFIED VISUALIZATION
# ==========================================
st.markdown('<div class="purple-header"><div class="header-title">Feedback360 Analytics Engine</div><div class="header-sub">Prototype Pipeline: Cross-channel feedback centralizer</div></div>', unsafe_allow_html=True)

display_db = st.session_state.feedback_db if selected_filter == "All Products" else st.session_state.feedback_db[st.session_state.feedback_db['Product'] == selected_filter]

if not display_db.empty:
    
    col1, col2, col3, col4 = st.columns(4)
    with col1: render_argon_card("Traffic", len(display_db), "📈", "bg-danger")
    with col2: render_argon_card("Positive", len(display_db[display_db['Sentiment'] == 'Positive']), "👍", "bg-success")
    with col3: render_argon_card("Negative", len(display_db[display_db['Sentiment'] == 'Negative']), "👎", "bg-warning")
    with col4: render_argon_card("Neutral", len(display_db[display_db['Sentiment'] == 'Neutral']), "💬", "bg-info")

    st.markdown("### 🧠 Autonomous Agent Insights")
    if st.button("Generate Executive Report", type="primary"):
        if not groq_key:
            st.warning("⚠️ Please enter your Groq API key in the sidebar first.")
        else:
            with st.spinner("Agent analyzing cross-channel sentiment data..."):
                report = generate_ai_summary(display_db, groq_key)
                st.info(report)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown('**📊 Overall Sentiment Profile**')
        st.bar_chart(display_db['Sentiment'].value_counts(), use_container_width=True)
    with c2:
        st.markdown('**📈 Cross-Channel Dist.**')
        st.bar_chart(display_db.groupby(['Channel', 'Sentiment']).size().unstack(fill_value=0), use_container_width=True)

    st.markdown("---")
    st.markdown('**🗄️ Unified Event Store (Raw Data)**')
    st.dataframe(display_db, use_container_width=True, hide_index=True)

else:
    col1, col2, col3, col4 = st.columns(4)
    with col1: render_argon_card("Traffic", "0", "📈", "bg-danger")
    with col2: render_argon_card("Positive", "0", "👍", "bg-success")
    with col3: render_argon_card("Negative", "0", "👎", "bg-warning")
    with col4: render_argon_card("Neutral", "0", "💬", "bg-info")
    st.info("Pipeline is currently idle. Inject a data stream from the sidebar.")