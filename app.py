import streamlit as st
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from groq import Groq
import time
from datetime import datetime

# ==========================================
# PAGE CONFIGURATION & MODERN SAAS CSS
# ==========================================
st.set_page_config(page_title="Feedback360 | Real-Time Sentiment Intelligence", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; }
    .stApp { background-color: #f8fafc; }
    .block-container { padding-top: 1.5rem !important; padding-bottom: 2rem !important; max-width: 95% !important; }
    .hero-container { background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #312e81 100%); padding: 2.2rem 2.5rem; border-radius: 16px; color: white; margin-bottom: 2rem; box-shadow: 0 20px 25px -5px rgba(15, 23, 42, 0.25); position: relative; overflow: hidden; border: 1px solid rgba(255, 255, 255, 0.1); }
    .hero-badge { background: rgba(99, 102, 241, 0.25); border: 1px solid rgba(129, 140, 248, 0.4); color: #a5b4fc; padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase; display: inline-block; margin-bottom: 0.75rem; }
    .hero-title { font-size: 2.1rem; font-weight: 800; letter-spacing: -0.02em; margin: 0; background: linear-gradient(to right, #ffffff, #cbd5e1); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .hero-sub { font-size: 0.95rem; color: #94a3b8; margin-top: 0.4rem; margin-bottom: 0; }
    .kpi-card { background: #ffffff; border-radius: 14px; padding: 1.25rem 1.5rem; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02), 0 2px 4px -1px rgba(0, 0, 0, 0.02); transition: all 0.2s ease-in-out; display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; }
    .kpi-card:hover { transform: translateY(-3px); box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08); border-color: #cbd5e1; }
    .kpi-label { font-size: 0.75rem; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; }
    .kpi-value { font-size: 2rem; font-weight: 800; color: #0f172a; line-height: 1.2; margin-top: 0.2rem; }
    .kpi-icon-box { width: 3rem; height: 3rem; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 1.3rem; flex-shrink: 0; }
    .icon-indigo { background: #e0e7ff; color: #4338ca; } .icon-emerald { background: #d1fae5; color: #047857; } .icon-rose { background: #ffe4e6; color: #be123c; } .icon-amber { background: #fef3c7; color: #b45309; }
    .ai-panel { background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%); border: 1px solid #e0e7ff; border-left: 5px solid #6366f1; border-radius: 12px; padding: 1.5rem; margin: 1rem 0 2rem 0; box-shadow: 0 10px 15px -3px rgba(99, 102, 241, 0.05); }
    .ai-panel-title { font-size: 1.05rem; font-weight: 700; color: #1e1b4b; display: flex; align-items: center; gap: 8px; margin-bottom: 0.75rem; }
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e2e8f0; }
    
    /* Gallery Image Styling */
    .gallery-img-container { border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
</style>
""", unsafe_allow_html=True)

def render_kpi(label, value, icon, icon_class):
    st.markdown(f'<div class="kpi-card"><div><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div></div><div class="kpi-icon-box {icon_class}">{icon}</div></div>', unsafe_allow_html=True)

# ==========================================
# MODULE 1: ENGINES & SESSION STATE
# ==========================================
analyzer = SentimentIntensityAnalyzer()
custom_lexicon = {"ads": -1.5, "adds": -1.5, "ad": -1.5, "buffering": -2.0, "drain": -2.0, "lag": -1.5, "crash": -2.5, "expensive": -1.5, "glitch": -2.0}
analyzer.lexicon.update(custom_lexicon)

def annotate_sentiment(text):
    score = analyzer.polarity_scores(text.lower())['compound']
    if score >= 0.05: return "Positive"
    elif score <= -0.05: return "Negative"
    else: return "Neutral"

def generate_ai_summary(dataframe, api_key):
    try:
        client = Groq(api_key=api_key)
        available_models = [m.id for m in client.models.list().data]
        
        # Priority list of models, avoiding ones that require explicit terms acceptance
        priority_list = ["llama-3.1-8b-instant", "llama-3.2-3b-preview", "gemma2-9b-it", "mixtral-8x7b-32768"]
        selected_model = next((m for m in priority_list if m in available_models), None)
        
        # Fallback to any model that isn't gated by a slash (third party)
        if not selected_model:
            safe_models = [m for m in available_models if "/" not in m]
            selected_model = safe_models[0] if safe_models else None
            
        if not selected_model: return "⚠️ No standard open-access models found on your Groq key."
        
        # Drop the raw image binary data before sending to LLM to save tokens
        clean_df = dataframe.drop(columns=['Image_Data'], errors='ignore')
        data_sample = clean_df.tail(15).to_dict('records')
        
        prompt = (
            "You are an executive AI decision engine. Analyze this customer feedback dataset. "
            "Pay special attention to specific Entity Details (Brands, Apps, Clothing types) and if images were attached as proof of defects. "
            f"Generate a crisp, 3-bullet point summary outlining key operational issues and positive trends: {data_sample}"
        )
        response = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model=selected_model, temperature=0.3)
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ API Error: {str(e)}"

if 'product_categories' not in st.session_state:
    st.session_state.product_categories = ["Mobile App", "Wireless Earbuds", "Clothes", "Web Dashboard"]

# Added Image_Data to Schema
if 'feedback_db' not in st.session_state:
    st.session_state.feedback_db = pd.DataFrame(columns=["Timestamp", "Product", "Entity_Details", "Channel", "Text", "Sentiment", "Image_Data"])

# ==========================================
# MODULE 2: DYNAMIC INGESTION UI
# ==========================================
st.sidebar.markdown("### ⚡ Pipeline Settings")
groq_key = st.sidebar.text_input("Groq API Key (GenAI Engine)", type="password")
st.sidebar.markdown("---")

selected_filter = st.sidebar.selectbox("🎯 Target Dashboard Scope", ["All Products"] + st.session_state.product_categories)
st.sidebar.markdown("---")

st.sidebar.markdown("##### 📝 Ingest Live Payload")

product_sel = st.sidebar.selectbox("Select Category", st.session_state.product_categories + ["+ Add Custom Category..."])

if product_sel == "+ Add Custom Category...":
    new_cat = st.sidebar.text_input("Enter New Category Name:")
    if st.sidebar.button("Save New Category"):
        if new_cat:
            st.session_state.product_categories.append(new_cat)
            st.rerun()
else:
    with st.sidebar.form(key='live_feedback'):
        if product_sel == "Mobile App":
            col1, col2 = st.columns(2)
            app_name = col1.text_input("App Name", placeholder="e.g., Spotify")
            os_type = col2.selectbox("Platform", ["iOS", "Android", "Cross-Platform"])
        elif product_sel == "Wireless Earbuds":
            col1, col2 = st.columns(2)
            brand_name = col1.text_input("Brand", placeholder="e.g., Sony")
            model_name = col2.text_input("Model", placeholder="e.g., WF-1000XM4")
        elif product_sel == "Clothes":
            col1, col2 = st.columns(2)
            brand_name = col1.text_input("Brand", placeholder="e.g., Zara")
            item_type = col2.text_input("Item Type", placeholder="e.g., Winter Jacket")
        else:
            custom_identifier = st.text_input(f"Specific {product_sel} Identifier/Name:")
        
        uploaded_img = st.file_uploader("Upload Defect/Reference Image (Optional)", type=["jpg", "png", "jpeg"])
        channel_sel = st.selectbox("Channel Source", ["In-Person Survey", "Support Logs", "Social Media"])
        live_text = st.text_area("Customer Text Payload:")
        submit_btn = st.form_submit_button('Push Event to Stream', use_container_width=True)

        if submit_btn and live_text:
            details = ""
            if product_sel == "Mobile App": details = f"{app_name} ({os_type})" if app_name else f"OS: {os_type}"
            elif product_sel == "Wireless Earbuds": details = f"{brand_name} {model_name}".strip() if (brand_name or model_name) else "Unknown Earbuds"
            elif product_sel == "Clothes": details = f"{brand_name} {item_type}".strip() if (brand_name or item_type) else "Unknown Clothing Item"
            else: details = custom_identifier if custom_identifier else "Generic"

            # Capture actual image bytes
            img_data = uploaded_img.read() if uploaded_img is not None else None
            if img_data:
                details += " [📸 Image Attached]"

            sentiment = annotate_sentiment(live_text)
            new_entry = pd.DataFrame([{
                "Timestamp": datetime.now().strftime("%H:%M:%S"),
                "Product": product_sel, 
                "Entity_Details": details,
                "Channel": channel_sel,
                "Text": live_text, 
                "Sentiment": sentiment,
                "Image_Data": img_data
            }])
            st.session_state.feedback_db = pd.concat([new_entry, st.session_state.feedback_db], ignore_index=True)
            st.sidebar.success("Payload routed to lake successfully.")

if st.sidebar.button("🌊 Simulate Batch Stream", use_container_width=True):
    batch_data = [
        {"Product": "Mobile App", "Entity_Details": "Spotify (Android)", "Channel": "Social Media", "Text": "it has more Adds duration in between the songs"},
        {"Product": "Wireless Earbuds", "Entity_Details": "Sony WF-1000XM4", "Channel": "In-Person Survey", "Text": "Customer service was very helpful replacing my order."},
        {"Product": "Mobile App", "Entity_Details": "Banking App (iOS)", "Channel": "Support Logs", "Text": "This is completely broken and terrible. I hate the new design."}
    ]
    with st.spinner('Ingesting distributed events...'):
        time.sleep(0.8)
        for item in batch_data:
            sentiment = annotate_sentiment(item["Text"])
            new_entry = pd.DataFrame([{
                "Timestamp": datetime.now().strftime("%H:%M:%S"),
                "Product": item["Product"], "Entity_Details": item["Entity_Details"],
                "Channel": item["Channel"], "Text": item["Text"], "Sentiment": sentiment,
                "Image_Data": None
            }])
            st.session_state.feedback_db = pd.concat([new_entry, st.session_state.feedback_db], ignore_index=True)

# ==========================================
# MODULE 3: DASHBOARD VIEW
# ==========================================
st.markdown("""
<div class="hero-container">
    <div class="hero-badge">● Dynamic Schema Pipeline Active</div>
    <h1 class="hero-title">Feedback360 Sentiment Intelligence</h1>
    <p class="hero-sub">Adaptable multi-channel opinion centralizer with real-time NLP annotation and GenAI synthesis.</p>
</div>
""", unsafe_allow_html=True)

display_db = st.session_state.feedback_db if selected_filter == "All Products" else st.session_state.feedback_db[st.session_state.feedback_db['Product'] == selected_filter]

if not display_db.empty:
    col1, col2, col3, col4 = st.columns(4)
    with col1: render_kpi("Ingested Events", len(display_db), "⚡", "icon-indigo")
    with col2: render_kpi("Positive Opinions", len(display_db[display_db['Sentiment'] == 'Positive']), "👍", "icon-emerald")
    with col3: render_kpi("Negative Opinions", len(display_db[display_db['Sentiment'] == 'Negative']), "👎", "icon-rose")
    with col4: render_kpi("Neutral Mentions", len(display_db[display_db['Sentiment'] == 'Neutral']), "💬", "icon-amber")

    st.markdown("### 🤖 Autonomous Copilot Insights")
    ai_col1, ai_col2 = st.columns([1, 4])
    with ai_col1:
        run_ai = st.button("Synthesize Executive Report", type="primary", use_container_width=True)
    if run_ai:
        if not groq_key: st.warning("⚠️ Please input a valid Groq API Key in the left sidebar configuration.")
        else:
            with st.spinner("LLM Agent analyzing real-time cross-channel payload..."):
                summary_output = generate_ai_summary(display_db, groq_key)
                st.markdown(f'<div class="ai-panel"><div class="ai-panel-title">🧠 Autonomous Strategic Synthesis</div><div>{summary_output}</div></div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown('##### 📊 Overall Sentiment Profile')
        st.bar_chart(display_db['Sentiment'].value_counts(), use_container_width=True, color="#6366f1")
    with c2:
        st.markdown('##### 📈 Cross-Channel Distribution')
        chart_data = display_db.groupby(['Channel', 'Sentiment']).size().unstack(fill_value=0)
        st.bar_chart(chart_data, use_container_width=True)

    st.markdown("---")
    st.markdown('##### 🗄️ Real-Time Annotated Event Store')
    
    cols = ["Timestamp", "Product", "Entity_Details", "Channel", "Sentiment", "Text"]
    st.dataframe(display_db[cols], use_container_width=True, hide_index=True)

    # ==========================================
    # VISUAL EVIDENCE GALLERY
    # ==========================================
    # Safety check: If old cached data loads, add the missing column to prevent KeyError
    if 'Image_Data' not in display_db.columns:
        display_db['Image_Data'] = None
        
    # Filter only rows that have image data
    images_df = display_db[display_db['Image_Data'].notna()]
    
    if not images_df.empty:
        st.markdown("---")
        st.markdown('##### 📸 Visual Evidence Gallery')
        st.markdown("Images attached to feedback payloads for visual verification.")
        
        # Display images in a clean grid
        gallery_cols = st.columns(4)
        for idx, row in enumerate(images_df.itertuples()):
            with gallery_cols[idx % 4]:
                st.markdown('<div class="gallery-img-container">', unsafe_allow_html=True)
                st.image(row.Image_Data, use_column_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
                st.caption(f"**{row.Entity_Details.replace(' [📸 Image Attached]', '')}**")
                # Truncate text if it's too long for the caption
                short_text = f"{row.Text[:60]}..." if len(row.Text) > 60 else row.Text
                st.caption(f'"{short_text}"')
else:
    col1, col2, col3, col4 = st.columns(4)
    with col1: render_kpi("Ingested Events", "0", "⚡", "icon-indigo")
    with col2: render_kpi("Positive Opinions", "0", "👍", "icon-emerald")
    with col3: render_kpi("Negative Opinions", "0", "👎", "icon-rose")
    with col4: render_kpi("Neutral Mentions", "0", "💬", "icon-amber")
    st.info("Pipeline status: Idle. Click 'Simulate Batch Stream' or use dynamic manual entry to ingest events.")