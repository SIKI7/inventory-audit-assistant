import os
import streamlit as st
import chromadb
from chromadb.utils import embedding_functions
from groq import Groq
from dotenv import load_dotenv

# Import custom backend service layers
from services import db_service
from services import chart_service
from services import alert_service
from services import root_cause
from services import summary_service
from services import risk_score
from services import insights

# 1. Page Configuration
st.set_page_config(page_title="AuditGPT Dashboard", page_icon="🤖", layout="wide")
load_dotenv()

# ==========================================
# CUSTOM CSS: HIGH-CONTRAST REACTIVE SAAS THEME
# ==========================================
st.markdown(
    """
    <style>
    /* Global Background and Typography Baseline */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    .stApp {
        background: linear-gradient(180deg, #F8FAFC 0%, #FFFFFF 400px) !important;
        color: #0F172A !important;
        font-family: 'Inter', sans-serif;
    }
    
    /* Force high contrast text on standard text rendering channels */
    p, span, label, li {
        color: #334155 !important;
    }
    
    h1, h2, h3, h4, h5, h6 {
        color: #0F172A !important;
        font-weight: 700 !important;
    }
    
    /* Elegant Sidebar Styling Layout */
    [data-testid="stSidebar"] {
        background-color: #F1F5F9 !important;
        border-right: 1px solid #E2E8F0;
    }
    
    /* High Contrast KPI Cards & Metric Overrides */
    div[data-testid="stMetric"], .enterprise-card, div.stAlert {
        background-color: #FFFFFF !important;
        border: 1px solid #CBD5E1 !important; /* Slightly darker grey boundary to prevent washout */
        border-radius: 12px !important;
        padding: 1.25rem !important;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04) !important;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    
    /* Micro-Interactions: Soft Elevation & Scale on Hover */
    div[data-testid="stMetric"]:hover, .enterprise-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(15, 23, 42, 0.08), 0 4px 6px -2px rgba(15, 23, 42, 0.04) !important;
        border-color: #6366F1 !important; /* Premium Indigo reactive highlight */
    }

    /* Absolute visibility configuration for Metric labels and numerical readouts */
    div[data-testid="stMetric"] label {
        color: #475569 !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }
    
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #0F172A !important;
        font-weight: 700 !important;
        font-size: 1.85rem !important;
        letter-spacing: -0.03em;
    }
    
    /* Active Focus Animation glow on Input Controls */
    input[type="text"], select, textarea {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        border: 1px solid #CBD5E1 !important;
        transition: all 0.2s ease-in-out !important;
    }
    
    input[type="text"]:focus {
        border-color: #6366F1 !important;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15) !important;
    }
    
    /* Interactive Button Transitions */
    .stButton>button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }
    
    .stButton>button:hover {
        transform: scale(1.01);
    }
    
    /* High Contrast Chat Interface Bubble Ecosystem */
    .chat-bubble-user {
        background-color: #1E293B !important; /* Deep charcoal background */
        color: #FFFFFF !important; /* Pure white text for reading protection */
        padding: 14px 18px;
        border-radius: 16px 16px 2px 16px;
        margin-bottom: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .chat-bubble-user p, .chat-bubble-user b {
        color: #FFFFFF !important;
    }
    
    .chat-bubble-assistant {
        background-color: #F8FAFC !important;
        color: #0F172A !important;
        padding: 14px 18px;
        border-radius: 16px 16px 16px 2px;
        margin-bottom: 12px;
        border: 1px solid #E2E8F0 !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .chat-bubble-assistant p, .chat-bubble-assistant b {
        color: #1E293B !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("""
        <div style="text-align: center; margin-top: 50px; margin-bottom: 30px;">
            <h2 style="color: #0F172A; font-weight: 800; tracking-tight: -0.03em;">🔒 AuditGPT Secure Gateway</h2>
            <p style="color: #64748B; font-size: 0.95rem;">Please authenticate your credentials to access the regional database records.</p>
        </div>
    """, unsafe_allow_html=True)
    
    with st.container():
        login_col1, login_col2, login_col3 = st.columns([1, 2, 1])
        with login_col2:
            st.markdown('<div class="enterprise-card" style="padding: 2rem !important;">', unsafe_allow_html=True)
            user_input = st.text_input("Corporate ID / Email", placeholder="e.g. admin@flowdash.com")
            pass_input = st.text_input("Security Access Token", type="password", placeholder="••••••••")
            
            if st.button("Verify Identity & Unlock Registry ➔", type="primary", use_container_width=True):
                if user_input == "admin" and pass_input == "hackathon2026":
                    st.session_state.authenticated = True
                    st.success("Identity Verified. Decrypting telemetry tables...")
                    st.rerun()
                else:
                    st.error("Authentication failed. Unauthorized access footprint logged.")
            st.markdown('</div>', unsafe_allow_html=True)
            
    st.stop()
# ====================================================================
# END OF SECURITY GATEWAY PANEL
# ====================================================================

# 2. Initialize Backend AI Systems (Cached for performance)
@st.cache_resource
def init_rag_system():
    chroma_client = chromadb.PersistentClient(path="./chroma_data")
    default_ef = embedding_functions.DefaultEmbeddingFunction()
    collection = chroma_client.get_collection(
        name="inventory_audits", 
        embedding_function=default_ef
    )
    groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    return collection, groq_client

try:
    collection, groq_client = init_rag_system()
except Exception as e:
    st.error(f"Error initializing backend AI: {e}")

# Fetch full raw dataset from database service
try:
    raw_df = db_service.get_all_inventory()
except Exception as e:
    st.error(f"Failed to load inventory dataset: {e}")
    raw_df = None

# ==========================================
# LEFT SIDEBAR NAVIGATION & DEMO COMMANDS
# ==========================================
st.sidebar.markdown("### 🔍 Inventory Filters")
if raw_df is not None:
    search_sku = st.sidebar.text_input("Search SKU ID:", placeholder="e.g. SKU-10042").strip()
    unique_locations = ["All Locations"] + list(raw_df["location"].unique())
    selected_location = st.sidebar.selectbox("Warehouse Location:", unique_locations)
    unique_statuses = ["All Statuses"] + list(raw_df["status"].unique())
    selected_status = st.sidebar.selectbox("Discrepancy Status:", unique_statuses)

    # Filtering Logic Engine
    filtered_df = raw_df.copy()
    if search_sku:
        filtered_df = filtered_df[filtered_df["sku_id"].str.contains(search_sku, case=False)]
    if selected_location != "All Locations":
        filtered_df = filtered_df[filtered_df["location"] == selected_location]
    if selected_status != "All Statuses":
        filtered_df = filtered_df[filtered_df["status"] == selected_status]

st.sidebar.write("---")

# Demo Interactive Guided Links Panel
st.sidebar.markdown("### 💡 Guided Demo Queries")
st.sidebar.markdown("Click to show judges instantaneous responses:")
demo_queries = [
    "Show stock mismatch",
    "Show phantom inventory",
    "Show high-risk items",
    "Generate audit summary",
    "Which warehouse needs re-audit?",
    "Show inventory loss"
]

clicked_demo_query = None
for q in demo_queries:
    if st.sidebar.button(f"👉 {q}", key=f"side_{q}"):
        clicked_demo_query = q

# ==========================================
# MAIN DASHBOARD PANELS
# ==========================================

# SECTION 1 — HERO HEADER WITH AMBIENT FLOW
st.markdown("## 🤖 AuditGPT")
st.markdown("#### *AI-Powered Inventory Audit Assistant*")
st.markdown("<p style='color: #475569; font-size: 1.1rem; margin-top:-10px; font-weight: 500;'>Monitor inventory health, identify discrepancies, and generate audit insights using conversational AI.</p>", unsafe_allow_html=True)
st.write("---")

# SECTION 5 — CRITICAL ALERTS PANEL
try:
    active_alerts = alert_service.scan_for_critical_alerts()
    if active_alerts:
        st.markdown("### 🚨 Real-Time Security & Risk Alerts")
        for alert in active_alerts:
            if alert["level"] == "CRITICAL":
                st.error(alert["message"])
            else:
                st.warning(alert["message"])
        st.write("---")
except Exception as e:
    st.error(f"⚠️ Failed to process active risk alerts: {e}")

# SECTION 10 & 9 — MANAGER INSIGHTS & EXECUTIVES SNAPSHOTS
st.markdown("### 💡 AuditGPT Smart Executive Insights")
try:
    mgr_insights = insights.generate_manager_insights()
    ins_col1, ins_col2, ins_col3, ins_col4 = st.columns(4)
    with ins_col1:
        st.info(f"🏢 **Primary Failure Facility**\n\n**{mgr_insights['top_warehouse']}**")
    with ins_col2:
        st.info(f"📍 **Highest Vulnerability Zone**\n\n**{mgr_insights['top_rack']}**")
    with ins_col3:
        st.info(f"📦 **Maximum Exposure SKU**\n\n**{mgr_insights['top_sku']}**")
    with ins_col4:
        st.info(f"💰 **Total Network Impact**\n\n**${mgr_insights['financial_impact']:,}**")
    st.write("---")
except Exception as e:
    st.error(f"⚠️ Failed to calculate executive insights: {e}")

# SECTION 4 — AUDIT PROGRESS
try:
    total_skus = db_service.get_total_skus()
    audited_skus = int(total_skus * 0.8)
    progress_percentage = audited_skus / total_skus
    
    st.markdown("### 🎯 Overall Audit Milestone Progress")
    prog_col1, prog_col2 = st.columns([9, 1])
    with prog_col1:
        st.progress(progress_percentage)
    with prog_col2:
        st.markdown(f"<h4 style='margin-top:-5px; color:#0F172A;'><b>{int(progress_percentage * 100)}%</b></h4>", unsafe_allow_html=True)
except Exception as e:
    st.error(f"⚠️ Failed to compute audit progress: {e}")
st.write("---")

# SECTION 6 — THREAT VECTOR PRIORITIZATION LEADERBOARD
st.markdown("### 🎯 Threat Vector Prioritization (High-Risk Matrix)")
try:
    scored_risk_df = risk_score.calculate_inventory_risk_scores()
    if not scored_risk_df.empty:
        top_items = scored_risk_df.head(4)
        risk_cols = st.columns(4)
        for idx, (_, item) in enumerate(top_items.iterrows()):
            with risk_cols[idx]:
                st.metric(
                    label=f"🚨 {item['sku_id']} ({item['location']})",
                    value=f"Index: {item['risk_score']}/100",
                    delta=f"${item['value']:,} At Risk",
                    delta_color="inverse"
                )
    st.write("---")
except Exception as e:
    st.error(f"⚠️ Failed to calculate threat scoring: {e}")

# SECTION 2 — KPI CARDS
st.markdown("### 📊 Live Warehouse Metrics")
try:
    discrepancies = db_service.get_total_discrepancies()
    estimated_loss = db_service.get_estimated_loss()

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric(label="Total SKUs", value=f"{total_skus:,}")
    with col2:
        st.metric(label="Audited SKUs", value=f"{audited_skus:,}")
    with col3:
        st.metric(label="Pending Audits", value=f"{total_skus - audited_skus:,}")
    with col4:
        st.metric(label="Discrepancies Found", value=f"{discrepancies:,}")
    with col5:
        st.metric(label="Estimated Loss", value=f"${estimated_loss:,}")
except Exception as e:
    st.error(f"⚠️ Failed to load dashboard metrics: {e}")
st.write("---")

# SECTION 9 — REPORT GENERATOR CALL-TO-ACTION
st.markdown("### 📑 Automated Executive Audit Reporter")
if st.button("🚀 Generate Executive Audit Report", type="primary"):
    with st.spinner("Analyzing operational records and drafting executive brief..."):
        generated_brief = summary_service.generate_executive_llm_summary()
        st.markdown('<div style="background-color: #FFFFFF; border: 1px solid #CBD5E1; padding: 25px; border-radius: 12px; margin-top:15px; margin-bottom:15px; color:#0F172A !important;">', unsafe_allow_html=True)
        st.markdown(generated_brief)
        st.markdown('</div>', unsafe_allow_html=True)
    st.write("---")

# SECTION 7 — INVENTORY DATA SHEET GRID
st.markdown("### 📋 Filtered Warehouse Data Records")
if raw_df is not None:
    st.dataframe(filtered_df, use_container_width=True, hide_index=True)
else:
    st.error("No record data loaded.")
st.write("---")

# SECTION 3 — GRAPHICS VISUAL ANALYTICS ENGINE
st.markdown("### 📈 Visual Analytics Engine")
chart_col1, chart_col2 = st.columns(2)
with chart_col1:
    health_pie = chart_service.inventory_health_chart()
    st.plotly_chart(health_pie, use_container_width=True)
with chart_col2:
    location_bar = chart_service.warehouse_comparison_chart()
    st.plotly_chart(location_bar, use_container_width=True)

risk_bar = chart_service.discrepancy_chart()
st.plotly_chart(risk_bar, use_container_width=True)
st.write("---")

# SECTION 8 — AI ASSISTANT CONVERSATION CONTEXT (GEMINI MINIMAL STYLE)
st.markdown("### 💬 AuditGPT Chat Assistant")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I am AuditGPT. Ask me any precise question regarding structural stock variances or select a guided prompt from the sidebar."}
    ]

# Stream chat items onto screen using styled typography blocks
for message in st.session_state.messages:
    if message["role"] == "user":
        st.markdown(f'<div class="chat-bubble-user"><b>👤 User:</b><br><p style="color: #FFFFFF !important; margin: 4px 0 0 0;">{message["content"]}</p></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="chat-bubble-assistant"><b>🤖 AuditGPT:</b><br><p style="color: #0F172A !important; margin: 4px 0 0 0;">{message["content"]}</p></div>', unsafe_allow_html=True)

# Process active inputs
user_question = st.chat_input("Ask a question about the warehouse audit...")
if clicked_demo_query:
    user_question = clicked_demo_query

if user_question:
    if not st.session_state.messages or st.session_state.messages[-1]["content"] != user_question:
        st.session_state.messages.append({"role": "user", "content": user_question})
        
        try:
            # Query local vectors from ChromaDB
            results = collection.query(query_texts=[user_question], n_results=4)
            retrieved_context = "\n".join(results['documents'][0])
            
            prompt_path = os.path.join("prompts", "system_prompt.txt")
            if os.path.exists(prompt_path):
                with open(prompt_path, "r") as f:
                    system_instruction = f.read()
            else:
                system_instruction = "You are an Inventory Audit Assistant."
            
            user_prompt = f"Context:\n{retrieved_context}\n\nQuestion: {user_question}"
            
            response = groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1
            )
            
            answer = response.choices[0].message.content
            st.session_state.messages.append({"role": "assistant", "content": answer})
            st.rerun()
            
        except Exception as e:
            st.error(f"An error occurred: {e}")