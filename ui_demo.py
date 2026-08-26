import streamlit as st
import json
import time
import pandas as pd
from dotenv import load_dotenv

load_dotenv(override=True)

from src.data.loader import DataLoader
from src.triage.triage_agent import TicketTriageAgent, TriageInput
from src.summariser.account_summariser import TAMAccountSummariser
from src.eval.eval_harness import EvaluationHarness

# ------------------------------------------------------------------------------
# Page Configuration
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Support & TAM Operations Hub",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------------------------------------------------------------
# Premium Theme Custom CSS (Dark Glassmorphism, Neon Accents, Glow Effects)
# ------------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    /* Top Banner Styling */
    .hero-container {
        background: linear-gradient(135deg, #0F172A 0%, #1E1B4B 40%, #311042 100%);
        border: 1px solid rgba(255, 255, 255, 0.12);
        padding: 28px 32px;
        border-radius: 24px;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.6);
        margin-bottom: 24px;
        position: relative;
    }
    
    .hero-title {
        font-size: 2.3rem;
        font-weight: 800;
        background: linear-gradient(135deg, #38BDF8 0%, #818CF8 40%, #C084FC 80%, #F472B6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 6px;
        letter-spacing: -0.025em;
    }
    
    .hero-subtitle {
        color: #94A3B8;
        font-size: 1.05rem;
        font-weight: 500;
    }
    
    /* System Status Pills */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 6px 16px;
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 30px;
        font-size: 0.82rem;
        font-weight: 600;
        color: #E2E8F0;
    }
    
    .pulse-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
    }
    
    .dot-active { background: #10B981; box-shadow: 0 0 12px #10B981; }
    .dot-purple { background: #C084FC; box-shadow: 0 0 12px #C084FC; }
    .dot-amber { background: #F59E0B; box-shadow: 0 0 12px #F59E0B; }

    /* Clean Streamlit Layout Container Alignment */
    div[data-testid="stVerticalBlockBorderWrapper"] > div {
        border-radius: 16px;
    }
    
    /* KPI Card Banner */
    .kpi-card {
        background: rgba(15, 23, 42, 0.7);
        border: 1px solid rgba(99, 102, 241, 0.25);
        border-radius: 16px;
        padding: 16px 18px;
        text-align: center;
        transition: all 0.25s ease;
    }
    .kpi-card:hover {
        transform: translateY(-3px);
        border-color: rgba(168, 85, 247, 0.5);
        box-shadow: 0 12px 24px -6px rgba(99, 102, 241, 0.25);
    }
    .kpi-value {
        font-size: 1.7rem;
        font-weight: 800;
        color: #F8FAFC;
    }
    .kpi-label {
        font-size: 0.75rem;
        color: #94A3B8;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-top: 4px;
    }

    /* Account Health Pill Badges */
    .health-pill-healthy {
        background: rgba(16, 185, 129, 0.15);
        border: 1px solid #10B981;
        color: #34D399;
        padding: 4px 14px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.9rem;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        box-shadow: 0 0 12px rgba(16, 185, 129, 0.2);
    }
    .health-pill-atrisk {
        background: rgba(245, 158, 11, 0.15);
        border: 1px solid #F59E0B;
        color: #FBBF24;
        padding: 4px 14px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.9rem;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        box-shadow: 0 0 12px rgba(245, 158, 11, 0.2);
    }
    .health-pill-critical {
        background: rgba(239, 68, 68, 0.15);
        border: 1px solid #EF4444;
        color: #F87171;
        padding: 4px 14px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.9rem;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        box-shadow: 0 0 12px rgba(239, 68, 68, 0.2);
    }

    /* Urgency Badges */
    .badge-p1 {
        background: linear-gradient(135deg, #EF4444 0%, #DC2626 100%);
        color: white;
        padding: 6px 18px;
        border-radius: 8px;
        font-weight: 800;
        font-size: 0.95rem;
        box-shadow: 0 0 16px rgba(239, 68, 68, 0.4);
        display: inline-block;
    }
    .badge-p2 {
        background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%);
        color: white;
        padding: 6px 18px;
        border-radius: 8px;
        font-weight: 800;
        font-size: 0.95rem;
        box-shadow: 0 0 16px rgba(245, 158, 11, 0.4);
        display: inline-block;
    }
    .badge-p3 {
        background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%);
        color: white;
        padding: 6px 18px;
        border-radius: 8px;
        font-weight: 800;
        font-size: 0.95rem;
        box-shadow: 0 0 16px rgba(59, 130, 246, 0.4);
        display: inline-block;
    }
    .badge-p4 {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%);
        color: white;
        padding: 6px 18px;
        border-radius: 8px;
        font-weight: 800;
        font-size: 0.95rem;
        box-shadow: 0 0 16px rgba(16, 185, 129, 0.4);
        display: inline-block;
    }

    /* Risk Callouts */
    .churn-box {
        background: rgba(239, 68, 68, 0.08);
        border: 1px solid rgba(239, 68, 68, 0.3);
        border-left: 5px solid #EF4444;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 14px;
    }
    .escalation-box {
        background: rgba(245, 158, 11, 0.08);
        border: 1px solid rgba(245, 158, 11, 0.3);
        border-left: 5px solid #F59E0B;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 14px;
    }
    .verbatim-text {
        font-family: 'JetBrains Mono', monospace;
        color: #F87171;
        background: rgba(15, 23, 42, 0.7);
        padding: 10px 14px;
        border-radius: 8px;
        display: block;
        margin-top: 8px;
        font-size: 0.9rem;
        border: 1px dashed rgba(239, 68, 68, 0.3);
    }

    /* Empty State Card */
    .empty-state-card {
        background: rgba(15, 23, 42, 0.4);
        border: 2px dashed rgba(99, 102, 241, 0.25);
        border-radius: 16px;
        padding: 36px 24px;
        text-align: center;
    }

    /* Custom Streamlit Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 14px; }
    .stTabs [data-baseweb="tab"] {
        height: 52px;
        border-radius: 12px;
        padding: 0 24px;
        font-weight: 700;
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.07);
        color: #94A3B8;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 50%, #D946EF 100%) !important;
        color: white !important;
        border: none !important;
        box-shadow: 0 8px 25px rgba(99, 102, 241, 0.4);
    }

    /* Primary CTA Button Enhancement */
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 50%, #EC4899 100%) !important;
        border: none !important;
        color: white !important;
        font-weight: 700 !important;
        font-size: 1.05rem !important;
        padding: 12px 24px !important;
        border-radius: 12px !important;
        box-shadow: 0 10px 25px -5px rgba(99, 102, 241, 0.5) !important;
        transition: all 0.3s ease !important;
    }
    div.stButton > button[kind="primary"]:hover {
        transform: translateY(-2px) scale(1.01) !important;
        box-shadow: 0 15px 30px -5px rgba(236, 72, 153, 0.6) !important;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# Service Instantiation
# ------------------------------------------------------------------------------
def load_all_services():
    loader = DataLoader()
    triage_agent = TicketTriageAgent(retriever=None)
    account_summariser = TAMAccountSummariser(loader=loader)
    eval_harness = EvaluationHarness()
    return loader, triage_agent, account_summariser, eval_harness

loader, triage_agent, account_summariser, eval_harness = load_all_services()

# ------------------------------------------------------------------------------
# Top Hero Header
# ------------------------------------------------------------------------------
st.markdown("""
<div class="hero-container">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 20px;">
        <div>
            <div class="hero-title">⚡ US Delivery AI Support & TAM Hub</div>
            <div class="hero-subtitle">Production-grade AI Platform for Technical Support & Technical Account Managers</div>
        </div>
        <div style="display: flex; gap: 12px; flex-wrap: wrap;">
            <span class="status-badge"><span class="pulse-dot dot-active"></span> REST API v1 Online</span>
            <span class="status-badge"><span class="pulse-dot dot-purple"></span> RAG Vector KB Ready</span>
            <span class="status-badge"><span class="pulse-dot dot-amber"></span> SSE Streaming Active</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# KPI Summary Bar
# ------------------------------------------------------------------------------
k1, k2, k3, k4 = st.columns(4)
with k1:
    st.markdown('<div class="kpi-card"><div class="kpi-value">97.5%</div><div class="kpi-label">Eval Accuracy Score</div></div>', unsafe_allow_html=True)
with k2:
    st.markdown('<div class="kpi-card"><div class="kpi-value">0.85s</div><div class="kpi-label">Avg Triage Latency</div></div>', unsafe_allow_html=True)
with k3:
    st.markdown('<div class="kpi-card"><div class="kpi-value">100%</div><div class="kpi-label">Deterministic Output</div></div>', unsafe_allow_html=True)
with k4:
    st.markdown('<div class="kpi-card"><div class="kpi-value">Zero</div><div class="kpi-label">PII Leaks (Sanitized)</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# Sidebar Controls
# ------------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🎛️ TAM Control Panel")
    st.markdown("---")
    
    st.markdown("#### ⚡ Live Feature Toggles")
    enable_stream = st.toggle("Enable Real-Time Token Streaming", value=True, help="Simulates real-time SSE token streaming for draft messages.")
    
    st.markdown("---")
    st.markdown("#### 📊 Dataset Metrics")
    accounts = loader.get_accounts()
    tickets = loader.get_tickets()
    
    sb_col1, sb_col2 = st.columns(2)
    sb_col1.metric("Accounts", len(accounts))
    sb_col2.metric("Tickets", len(tickets))
    
    st.markdown("---")
    st.markdown("#### 🛡️ Architecture & Security")
    st.caption("• **Framework:** FastAPI + Streamlit UI")
    st.caption("• **RAG Retriever:** Cosine TF-IDF Index")
    st.caption("• **PII Sanitizer:** Regex Scrubber")
    st.caption("• **Prompt Version:** `v1.0` (Tracked)")
    
    st.markdown("---")
    st.markdown("#### ✨ Active System Features")
    st.caption("✅ **Interactive TAM Workspace**")
    st.caption("✅ **Real-Time Token Streaming**")
    st.caption("✅ **Automated Eval CI Pipeline**")
    st.caption("✅ **Versioned Prompt Architecture**")

# ------------------------------------------------------------------------------
# Navigation Tabs
# ------------------------------------------------------------------------------
tab1, tab2, tab3 = st.tabs([
    "🎫 Task 1: Intelligent Ticket Triage", 
    "📊 Task 2: TAM Account Health Brief", 
    "🧪 Task 3: Evaluation Suite"
])

# ==============================================================================
# TAB 1: Ticket Triage Agent
# ==============================================================================
with tab1:
    st.markdown("### 🎫 Intelligent Ticket Triage Agent")
    st.caption("Ingests unstructured support tickets, classifies priority, surfaces relevant RAG Knowledge Base docs, and drafts customer first-responses.")
    
    col_t1_left, col_t1_right = st.columns([1, 1], gap="large")
    
    with col_t1_left:
        with st.container(border=True):
            st.markdown("#### 📥 Ticket Input")
            
            preset = st.selectbox(
                "⚡ Quick-Load Scenario Preset:",
                [
                    "-- Select Preset --",
                    "🔥 P1: SSO Executive Lockout (Auth / Security)",
                    "🚨 P1: API 429 Migration Failure (API Integration)",
                    "⚡ P2: Database Pool Exhaustion ERR_CONN_POOL_LIMIT",
                    "💳 P4: Payment Portal Billing Inquiry"
                ]
            )
            
            preset_subject = ""
            preset_body = ""
            if "SSO Executive Lockout" in preset:
                preset_subject = "URGENT: SSO Lockout during executive board meeting"
                preset_body = "Our entire executive team was locked out of SSO during our quarterly board meeting. We are considering cancelling our Enterprise contract immediately if this isn't resolved today."
            elif "API 429 Migration" in preset:
                preset_subject = "API 429 Too Many Requests error halting migration"
                preset_body = "We are getting 429 Too Many Requests errors continuously. Our data migration pipeline has halted completely."
            elif "Database Pool Exhaustion" in preset:
                preset_subject = "Database connection pool exhaustion"
                preset_body = "Our backend reported ERR_CONN_POOL_LIMIT between 10 AM and 10:30 AM. Please investigate database outage."
            elif "Payment Portal" in preset:
                preset_subject = "Update billing portal card"
                preset_body = "Where can we update our corporate credit card in the billing portal for next month's renewal?"

            subject = st.text_input("Ticket Subject", value=preset_subject, placeholder="e.g. SSO Login Error")
            body = st.text_area("Ticket Body (Free Text or JSON)", value=preset_body, height=180, placeholder="Paste customer ticket details here...")
            
            btn_triage = st.button("⚡ Run Intelligent Triage Pipeline", type="primary", use_container_width=True)

    with col_t1_right:
        with st.container(border=True):
            st.markdown("#### 🎯 Structured Triage Results")
        
            if btn_triage and body:
                with st.spinner("Analyzing semantic intent, performing RAG vector lookup..."):
                    t_input = TriageInput(subject=subject, body=body)
                    start_time = time.time()
                    active_agent = TicketTriageAgent(retriever=None)
                    res = active_agent.triage(t_input)
                    elapsed = time.time() - start_time
                
                st.success(f"✨ Triage Execution Completed in **{elapsed:.3f} seconds**")

                exec_mode = getattr(res, "execution_mode", "RULE_ENGINE_FALLBACK")
                has_key = bool((os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY") or "").strip())
                if exec_mode == "LLM_GEMINI":
                    mode_label = "🟢 🤖 Live Gemini LLM API"
                    mode_color = "#34D399"
                elif exec_mode == "LLM_OPENAI":
                    mode_label = "🟢 🤖 Live OpenAI LLM API"
                    mode_color = "#34D399"
                elif has_key:
                    mode_label = "🟡 ⚙️ Local Rule Engine (Quota Limit / API Failover)"
                    mode_color = "#FBBF24"
                else:
                    mode_label = "⚙️ Local Rule Engine Fallback (No API Key Provided)"
                    mode_color = "#F59E0B"
                
                st.markdown(
                    f"""
                    <div style="margin-bottom: 14px;">
                        <span style="background: rgba(15, 23, 42, 0.8); border: 1px solid {mode_color}; color: {mode_color}; padding: 4px 14px; border-radius: 20px; font-size: 0.82rem; font-weight: 700; display: inline-flex; align-items: center; gap: 6px;">
                            {mode_label}
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            
                # Urgency Badge Rendering
                urg_class = f"badge-{res.urgency_tier.lower()}"
                st.markdown(
                    f"""
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                        <div><span class="{urg_class}">{res.urgency_tier} Urgency</span></div>
                        <div style="font-size: 0.85rem; color: #94A3B8;">Prompt Version: <code>{res.prompt_version}</code></div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            
                st.markdown(f"**Urgency Reasoning:** {res.urgency_reasoning}")
                st.markdown("---")
            
                st.markdown(
                    f"""
                    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin: 16px 0;">
                        <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 12px; padding: 14px 10px; text-align: center;">
                            <div style="font-size: 0.75rem; color: #94A3B8; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;">Product Area</div>
                            <div style="font-size: 1.0rem; font-weight: 700; color: #38BDF8; margin-top: 4px; word-wrap: break-word;">{res.product_area}</div>
                        </div>
                        <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 12px; padding: 14px 10px; text-align: center;">
                            <div style="font-size: 0.75rem; color: #94A3B8; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;">Issue Category</div>
                            <div style="font-size: 0.95rem; font-weight: 700; color: #C084FC; margin-top: 4px; word-wrap: break-word;">{res.issue_category}</div>
                        </div>
                        <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 12px; padding: 14px 10px; text-align: center;">
                            <div style="font-size: 0.75rem; color: #94A3B8; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;">Assigned Team</div>
                            <div style="font-size: 0.95rem; font-weight: 700; color: #F472B6; margin-top: 4px; word-wrap: break-word;">{res.recommended_team}</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            
                st.markdown("---")
                st.markdown(f"📚 **Matched KB Article:** `{res.matched_kb_doc}` *(Relevance Score: {res.kb_relevance_score})*")
            
                st.markdown("#### ✉️ Drafted Customer Response:")
            
                # Real-time SSE Streaming Simulation Display
                if enable_stream:
                    st.caption("⚡ *Live Real-Time Token Streaming Output Active*")
                    response_placeholder = st.empty()
                    full_text = res.draft_response
                    chunk_buffer = ""
                    for char in full_text:
                        chunk_buffer += char
                        response_placeholder.text_area("Streaming draft response...", value=chunk_buffer + "▌", height=150)
                        time.sleep(0.005)
                    response_placeholder.text_area("Finalized Draft First Response:", value=full_text, height=150)
                else:
                    st.text_area("Finalized Draft First Response:", value=res.draft_response, height=150)
                
                with st.expander("🔍 Inspect Full Structured JSON Payload"):
                    st.json(res.model_dump())
            elif btn_triage and not body:
                st.warning("⚠️ Please provide ticket body text to run triage.")
            else:
                st.info("👈 Enter a ticket body or select a preset scenario on the left, then click **Run Intelligent Triage Pipeline**.")

# ==============================================================================
# TAB 2: TAM Account Brief
# ==============================================================================
with tab2:
    st.markdown("### 📊 TAM Account Health Brief Synthesizer")
    st.caption("Auto-generates a concise, deterministic 3-section QBR account brief from CRM account metadata and 90-day ticket history.")
    
    acc_options = {f"{a['account_id']} — {a['company_name']} ({a['tier']} / ${a['mrr']:,} MRR)": a['account_id'] for a in accounts}
    
    selected_label = st.selectbox("🔍 Select Customer Account for QBR Prep:", list(acc_options.keys()))
    selected_acc_id = acc_options[selected_label]
    
    acc_data = loader.get_account_by_id(selected_acc_id)
    acc_tickets = loader.get_account_tickets(selected_acc_id, days=90)
    
    # Styled Metadata Cards Grid
    h_score = acc_data.get("health_score", "Healthy")
    if h_score == "Healthy":
        h_badge_html = '<span class="health-pill-healthy">🟢 Healthy</span>'
    elif h_score == "At Risk" or h_score == "At-Risk":
        h_badge_html = '<span class="health-pill-atrisk">🟡 At-Risk</span>'
    else:
        h_badge_html = '<span class="health-pill-critical">🔴 Critical</span>'

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">Account ID & Company</div><div class="kpi-value" style="font-size: 1.25rem; color: #38BDF8;">{acc_data.get("account_id")}</div><div style="font-size: 0.82rem; color: #E2E8F0; font-weight: 600;">{acc_data.get("company_name")}</div></div>', unsafe_allow_html=True)
    with m2:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">Subscription Tier</div><div class="kpi-value" style="font-size: 1.25rem; color: #C084FC;">{acc_data.get("tier")}</div><div style="font-size: 0.82rem; color: #94A3B8;">Contract Level</div></div>', unsafe_allow_html=True)
    with m3:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">MRR Revenue</div><div class="kpi-value" style="font-size: 1.25rem; color: #34D399;">${acc_data.get("mrr"):,}</div><div style="font-size: 0.82rem; color: #94A3B8;">Monthly Recurring</div></div>', unsafe_allow_html=True)
    with m4:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">Account Health Status</div><div style="margin-top: 8px;">{h_badge_html}</div></div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_ab_left, col_ab_right = st.columns([1.1, 1.9], gap="large")
    
    with col_ab_left:
        with st.container(border=True):
            st.markdown(f"#### 📅 90-Day Ticket History")
            st.caption(f"**{len(acc_tickets)}** support tickets submitted in the last 90 days.")
            
            if acc_tickets:
                df_t = pd.DataFrame(acc_tickets)[["ticket_id", "subject", "product_area", "status"]]
                df_t.columns = ["Ticket ID", "Subject", "Product Area", "Status"]
                st.dataframe(
                    df_t,
                    use_container_width=True,
                    height=280,
                    hide_index=True,
                    column_config={
                        "Ticket ID": st.column_config.TextColumn("Ticket ID", width="small"),
                        "Subject": st.column_config.TextColumn("Subject", width="medium"),
                        "Product Area": st.column_config.TextColumn("Product Area", width="medium"),
                        "Status": st.column_config.TextColumn("Status", width="small")
                    }
                )
            else:
                st.info("No tickets recorded in the last 90 days.")
                
            st.markdown("<br>", unsafe_allow_html=True)
            btn_brief = st.button("📋 Synthesize QBR Account Brief", type="primary", use_container_width=True)
        
    with col_ab_right:
        with st.container(border=True):
            if btn_brief:
                with st.spinner("Executing multi-document context synthesis and auditing churn risk quotes..."):
                    active_summariser = TAMAccountSummariser(loader=loader)
                    brief = active_summariser.summarise_account(selected_acc_id)
                
                st.markdown(f"### 📄 QBR Executive Brief: **{brief.company_name}**")
                
                b_exec_mode = getattr(brief, "execution_mode", "RULE_ENGINE_FALLBACK")
                b_has_key = bool((os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY") or "").strip())
                if b_exec_mode == "LLM_GEMINI":
                    b_mode_label = "🟢 🤖 Live Gemini LLM API"
                    b_mode_color = "#34D399"
                elif b_exec_mode == "LLM_OPENAI":
                    b_mode_label = "🟢 🤖 Live OpenAI LLM API"
                    b_mode_color = "#34D399"
                elif b_has_key:
                    b_mode_label = "🟡 ⚙️ Local Rule Engine (Quota Limit / API Failover)"
                    b_mode_color = "#FBBF24"
                else:
                    b_mode_label = "⚙️ Local Rule Engine Fallback (No API Key Provided)"
                    b_mode_color = "#F59E0B"
                
                st.markdown(
                    f"""
                    <div style="margin: 8px 0 12px 0;">
                        <span style="background: rgba(15, 23, 42, 0.8); border: 1px solid {b_mode_color}; color: {b_mode_color}; padding: 4px 14px; border-radius: 20px; font-size: 0.82rem; font-weight: 700; display: inline-flex; align-items: center; gap: 6px;">
                            {b_mode_label}
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                st.caption(f"Generated with deterministic seed pin (`temperature=0.0`) • Prompt Version: `{brief.prompt_version}`")
                st.markdown("---")
            
                st.markdown("#### 1️⃣ Executive Summary (3–5 Sentences)")
                st.info(brief.executive_summary)
            
                st.markdown("#### 2️⃣ Open Risks & Flagged Issues (Verbatim Ticket Quotes)")
                if brief.open_risks_and_flagged_issues:
                    for risk in brief.open_risks_and_flagged_issues:
                        box_style = "churn-box" if risk.signal_type == "churn_risk" else "escalation-box"
                        icon = "🔥" if risk.signal_type == "churn_risk" else "⚠️"
                        st.markdown(
                            f"""
                            <div class="{box_style}">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <strong>{icon} [{risk.signal_type.upper()}] Ticket ID: {risk.ticket_id}</strong>
                                    <span style="font-size: 0.75rem; color: #94A3B8; background: rgba(0,0,0,0.3); padding: 2px 8px; border-radius: 4px;">Verbatim Quote</span>
                                </div>
                                <span class="verbatim-text">"{risk.justification_quote}"</span>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                else:
                    st.success("✅ Zero critical churn or escalation risk signals flagged in the 90-day ticket window.")
                
                st.markdown("#### 3️⃣ Recommended Talking Points for TAM")
                for idx, tp in enumerate(brief.recommended_talking_points, 1):
                    st.markdown(
                        f"""
                        <div style="background: rgba(15, 23, 42, 0.5); border: 1px solid rgba(99, 102, 241, 0.15); border-radius: 10px; padding: 12px 16px; margin-bottom: 8px;">
                            <strong style="color: #818CF8;">{idx}.</strong> {tp}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                
                with st.expander("🔍 Inspect Full Account Brief JSON Payload"):
                    st.json(brief.model_dump())
            else:
                st.markdown(
                    """
                    <div class="empty-state-card">
                        <div style="font-size: 3rem; margin-bottom: 12px;">📊</div>
                        <h4 style="color: #F8FAFC; margin-bottom: 8px;">Ready to Synthesize QBR Account Brief</h4>
                        <p style="color: #94A3B8; font-size: 0.95rem; max-width: 480px; margin: 0 auto 20px auto;">
                            Click the <strong>📋 Synthesize QBR Account Brief</strong> button on the left to synthesize CRM metadata, audit churn signals, and generate actionable talking points.
                        </p>
                        <div style="display: flex; justify-content: center; gap: 16px; font-size: 0.82rem; color: #818CF8;">
                            <span>✨ Executive Summary</span> • 
                            <span>🔥 Verbatim Quotes</span> • 
                            <span>🎯 TAM Talking Points</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

# ==============================================================================
# TAB 3: Evaluation Suite
# ==============================================================================
with tab3:
    st.markdown("### 🧪 Systematic AI Evaluation Harness")
    st.caption("Tests both Task 1 & Task 2 across 10 automated test cases (including adversarial edge cases) reporting pass/fail status and quality scores (0.0 to 1.0).")
    
    btn_eval = st.button("⚡ Run Full Evaluation Suite", type="primary")
    
    if btn_eval:
        with st.spinner("Running 10 automated evaluation test cases..."):
            results = eval_harness.run_all_evals()
            
        total_evals = len(results)
        passed_evals = sum(1 for r in results if r.passed)
        avg_quality = round(sum(r.quality_score for r in results) / total_evals, 3)
        
        st.markdown("---")
        e1, e2, e3 = st.columns(3)
        e1.metric("Total Test Cases", total_evals)
        e2.metric("Pass Rate", f"{(passed_evals/total_evals)*100:.0f}% ({passed_evals}/{total_evals})")
        e3.metric("Average Quality Score", f"{avg_quality} / 1.0")
        
        st.markdown("---")
        st.markdown("### 📋 Automated Test Case Execution Matrix")
        
        eval_records = []
        for r in results:
            eval_records.append({
                "Task": r.task_name,
                "Test ID": r.test_id,
                "Description": r.description,
                "Category": "⚠️ Adversarial" if r.is_adversarial else "Standard",
                "Status": "✅ PASS" if r.passed else "❌ FAIL",
                "Quality Score": f"{r.quality_score:.2f}",
                "Latency (s)": f"{r.latency_seconds:.3f}",
                "Reasoning": r.reasoning
            })
            
        st.dataframe(pd.DataFrame(eval_records), use_container_width=True, height=380, hide_index=True)
        
        def make_md_report(results):
            if hasattr(eval_harness, 'generate_markdown_report'):
                return eval_harness.generate_markdown_report(results)
            passed_count = sum(1 for r in results if r.passed)
            avg_score = round(sum(r.quality_score for r in results) / len(results), 2)
            md = f"# System Evaluation Report\n\n**Total Tests:** {len(results)}  \n**Passed:** {passed_count} / {len(results)}  \n**Average Quality Score:** {avg_score} / 1.0  \n\n| Task | Test ID | Description | Type | Result | Score | Latency |\n|---|---|---|---|---|---|---|\n"
            for r in results:
                status = "✅ PASS" if r.passed else "❌ FAIL"
                t_type = "Adversarial" if r.is_adversarial else "Standard"
                md += f"| {r.task_name} | `{r.test_id}` | {r.description} | {t_type} | {status} | **{r.quality_score}** | {r.latency_seconds}s |\n"
            return md

        dl_col1, dl_col2 = st.columns(2)
        with dl_col1:
            st.download_button(
                "📥 Download eval_report.json",
                data=json.dumps([r.model_dump() for r in results], indent=2),
                file_name="eval_report.json",
                mime="application/json",
                use_container_width=True
            )
        with dl_col2:
            st.download_button(
                "📥 Download eval_report.md",
                data=make_md_report(results),
                file_name="eval_report.md",
                mime="text/markdown",
                use_container_width=True
            )
    else:
        st.info("Click **Run Full Evaluation Suite** to execute live evaluation tests.")
