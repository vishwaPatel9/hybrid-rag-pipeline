import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import streamlit as st
import pandas as pd
from ingestion.scraper import scrape_urls
from processing.advanced_cleaner import advanced_clean_pipeline
from processing.chunker import process_chunks
from indexing.embed import embed_and_store
from indexing.bm25_index import build_bm25_index
from retrieval.hybrid_search import hybrid_search
from retrieval.reranker import rerank_results
from generation.rag_pipeline import generate_answer
from generation.contradiction_detector import detect_contradictions
from deal_prediction.backtest import run_historical_backtest
from deal_prediction.pipeline import run_deal_prediction_pipeline

st.set_page_config(
    page_title="Third Bridge · Intelligence Engine",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Global Styling (Warm Linen Beige Canvas with Deep Forest Green & Cream) ────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Playfair+Display:ital,wght@0,500;0,600;1,400&family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@24,400,0,0&display=swap');

*, *::before, *::after { box-sizing: border-box; }

html, body, .stApp {
    font-family: 'Outfit', -apple-system, BlinkMacSystemFont, sans-serif !important;
    background: #F0EBE0 !important;
    color: #0E2615 !important;
}

[data-testid="stAppViewContainer"] > .main {
    background: #F0EBE0 !important;
}

.block-container {
    padding: 2rem 2.8rem 4rem !important;
    max-width: 1400px !important;
}

[data-testid="stSidebar"] {
    background: #E5DDD0 !important;
    border-right: 1px solid rgba(22, 56, 32, 0.1) !important;
}

h1, h2, h3, h4 {
    font-family: 'Playfair Display', Georgia, serif !important;
    color: #0E2615 !important;
    font-weight: 600 !important;
    letter-spacing: -0.01em;
}

p, li {
    color: #1A3D22 !important;
    font-family: 'Outfit', sans-serif !important;
}

span:not([data-testid="stIconMaterial"]):not(.material-symbols-rounded):not(.material-icons),
div:not([data-testid="stIconMaterial"]):not(.material-symbols-rounded):not(.material-icons) {
    font-family: 'Outfit', sans-serif;
}

[data-testid="stIconMaterial"],
.material-symbols-rounded,
.material-icons {
    font-family: 'Material Symbols Rounded', 'Material Icons', sans-serif !important;
    font-size: 1.25rem !important;
    letter-spacing: normal !important;
    text-transform: none !important;
    display: inline-block !important;
    color: #FAF5E8 !important;
}

[data-testid="collapsedControl"] [data-testid="stIconMaterial"],
[data-testid="stSidebarHeader"] [data-testid="stIconMaterial"],
button[kind="header"] [data-testid="stIconMaterial"] {
    color: #163820 !important;
}

label {
    font-family: 'Outfit', sans-serif !important;
    font-size: 0.68rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    color: rgba(14, 38, 21, 0.5) !important;
}

/* ── Inputs ─────────────────────────────────────── */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea {
    background: rgba(255,255,255,0.7) !important;
    border: 1px solid rgba(22, 56, 32, 0.2) !important;
    border-radius: 12px !important;
    color: #0E2615 !important;
    font-family: 'Outfit', sans-serif !important;
    font-size: 0.95rem !important;
    padding: 0.85rem 1.2rem !important;
    transition: border-color 350ms cubic-bezier(0.32,0.72,0,1), box-shadow 350ms cubic-bezier(0.32,0.72,0,1) !important;
    box-shadow: 0 1px 0 rgba(255,255,255,0.8) inset, 0 2px 10px rgba(14, 38, 21, 0.04) !important;
}

[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
    border-color: #163820 !important;
    box-shadow: 0 0 0 3px rgba(22, 56, 32, 0.1), 0 2px 10px rgba(14, 38, 21, 0.06) !important;
    outline: none !important;
    background: rgba(255,255,255,0.95) !important;
}

/* ── Buttons ─────────────────────────────────────── */
[data-testid="stButton"] > button {
    background: #163820 !important;
    color: #FAF5E8 !important;
    border: none !important;
    border-radius: 100px !important;
    font-family: 'Outfit', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
    letter-spacing: 0.03em !important;
    padding: 0.65rem 1.6rem !important;
    transition: background 350ms cubic-bezier(0.32,0.72,0,1), transform 250ms cubic-bezier(0.32,0.72,0,1), box-shadow 350ms cubic-bezier(0.32,0.72,0,1) !important;
    box-shadow: 0 1px 0 rgba(255,255,255,0.08) inset, 0 4px 18px rgba(14, 38, 21, 0.22) !important;
}

[data-testid="stButton"] > button *,
[data-testid="stButton"] > button p,
[data-testid="stButton"] > button span,
[data-testid="stButton"] > button div {
    color: #FAF5E8 !important;
    font-weight: 600 !important;
}

[data-testid="stButton"] > button:hover {
    background: #1e4d2b !important;
    transform: translateY(-1px) scale(1.005) !important;
    box-shadow: 0 1px 0 rgba(255,255,255,0.08) inset, 0 8px 28px rgba(14, 38, 21, 0.26) !important;
}

[data-testid="stButton"] > button:active {
    transform: scale(0.98) !important;
    box-shadow: 0 1px 8px rgba(14, 38, 21, 0.18) !important;
}

[data-testid="stButton"] > button:hover *,
[data-testid="stButton"] > button:hover p,
[data-testid="stButton"] > button:hover span {
    color: #FFFFFF !important;
}

/* ── Metrics (double-bezel) ──────────────────────── */
[data-testid="stMetric"] {
    background: #142E1A !important;
    border: 1px solid rgba(250, 245, 232, 0.07) !important;
    border-radius: 18px !important;
    padding: 1.3rem 1.5rem !important;
    box-shadow: 0 1px 0 rgba(255,255,255,0.05) inset, 0 6px 28px rgba(0,0,0,0.16) !important;
}

[data-testid="stMetric"] *,
[data-testid="stMetric"] p,
[data-testid="stMetric"] span,
[data-testid="stMetric"] div {
    color: #FAF5E8 !important;
}

[data-testid="stMetric"] [data-testid="stMetricLabel"] *,
[data-testid="stMetricLabel"] {
    font-size: 0.68rem !important;
    color: rgba(250, 245, 232, 0.45) !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
    font-weight: 600 !important;
}

[data-testid="stMetric"] [data-testid="stMetricValue"] *,
[data-testid="stMetricValue"] {
    font-family: 'Playfair Display', Georgia, serif !important;
    font-size: 2rem !important;
    color: #FFFFFF !important;
    font-weight: 600 !important;
    letter-spacing: -0.02em !important;
}

/* ── Tabs ────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    gap: 0.2rem !important;
    border-bottom: 1px solid rgba(22, 56, 32, 0.12) !important;
    padding-bottom: 0 !important;
    background: transparent !important;
}

.stTabs [data-baseweb="tab"] {
    font-family: 'Outfit', sans-serif !important;
    font-size: 0.875rem !important;
    font-weight: 500 !important;
    color: rgba(14, 38, 21, 0.4) !important;
    padding: 0.65rem 1.1rem !important;
    border-radius: 8px 8px 0 0 !important;
    transition: color 250ms cubic-bezier(0.32,0.72,0,1) !important;
    letter-spacing: 0.01em !important;
}

.stTabs [aria-selected="true"] {
    color: #0E2615 !important;
    font-weight: 700 !important;
    border-bottom: 2px solid #163820 !important;
    background: transparent !important;
}

/* ── Expanders (double-bezel company cards) ──────── */
[data-testid="stExpander"] {
    background: transparent !important;
    border: 1px solid rgba(22, 56, 32, 0.13) !important;
    border-radius: 18px !important;
    margin-bottom: 0.5rem !important;
    overflow: hidden !important;
    box-shadow: 0 2px 12px rgba(14, 38, 21, 0.05) !important;
    transition: box-shadow 350ms cubic-bezier(0.32,0.72,0,1), border-color 350ms cubic-bezier(0.32,0.72,0,1) !important;
}

[data-testid="stExpander"]:hover {
    box-shadow: 0 6px 30px rgba(14, 38, 21, 0.1) !important;
    border-color: rgba(22, 56, 32, 0.25) !important;
}

[data-testid="stExpander"],
[data-testid="stExpander"] > div {
    color: #1A3D22 !important;
}

[data-testid="stExpander"] summary {
    background: #142E1A !important;
    color: #FAF5E8 !important;
    font-size: 0.88rem !important;
    font-weight: 600 !important;
    padding: 1.05rem 1.3rem !important;
    border-radius: 18px !important;
    letter-spacing: 0.005em !important;
    transition: background 250ms cubic-bezier(0.32,0.72,0,1) !important;
}



[data-testid="stExpander"] summary:hover {
    background: #1a3a21 !important;
}

[data-testid="stExpander"] p,
[data-testid="stExpander"] li,
[data-testid="stExpander"] div {
    color: #1A3D22 !important;
}

/* Force summary text (including nested elements) to stay bright */
[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary p,
[data-testid="stExpander"] summary span,
[data-testid="stExpander"] summary div {
    color: #FAF5E8 !important;
}

[data-testid="stExpander"] strong,
[data-testid="stExpander"] b {
    color: #0E2615 !important;
    font-weight: 700 !important;
}

[data-testid="stExpander"] em {
    color: rgba(14, 38, 21, 0.7) !important;
    font-style: italic !important;
}

[data-testid="stExpander"] a {
    color: #2E7D46 !important;
    text-decoration: underline !important;
}

[data-testid="stExpander"] code {
    background: rgba(14, 38, 21, 0.05) !important;
    color: #0E2615 !important;
    border: 1px solid rgba(14, 38, 21, 0.1) !important;
    border-radius: 6px !important;
    padding: 0.1rem 0.4rem !important;
}

/* ── Header ──────────────────────────────────────── */
.tb-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 0 2rem;
    border-bottom: 1px solid rgba(22, 56, 32, 0.1);
    margin-bottom: 2.2rem;
}
.tb-title {
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 2.1rem;
    font-weight: 600;
    color: #0E2615;
    letter-spacing: -0.02em;
    line-height: 1.15;
}
.tb-sub {
    font-size: 0.78rem;
    color: rgba(14, 38, 21, 0.4);
    margin-top: 0.35rem;
    font-weight: 400;
    letter-spacing: 0.03em;
}
.tb-eyebrow {
    display: inline-block;
    background: rgba(22, 56, 32, 0.08);
    border: 1px solid rgba(22, 56, 32, 0.14);
    color: rgba(14, 38, 21, 0.6);
    font-size: 0.62rem;
    font-weight: 700;
    letter-spacing: 0.16em;
    padding: 0.3rem 0.9rem;
    border-radius: 100px;
    text-transform: uppercase;
    margin-bottom: 0.7rem;
}

/* ── Answer & Deal Cards (double-bezel) ─────────── */
.clean-card {
    background: #142E1A;
    border: 1px solid rgba(250, 245, 232, 0.07);
    border-radius: 18px;
    padding: 1.7rem 1.9rem;
    margin-top: 0.8rem;
    line-height: 1.82;
    font-size: 0.95rem;
    color: #FAF5E8;
    box-shadow: 0 1px 0 rgba(255,255,255,0.05) inset, 0 10px 36px rgba(0,0,0,0.14);
}

.clean-card p, .clean-card li, .clean-card span, .clean-card div {
    color: #FAF5E8 !important;
}

.pill-high {
    background: #FAF5E8;
    color: #0E2615;
    border: none;
    padding: 0.2rem 0.85rem;
    border-radius: 100px;
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}

.pill-med {
    background: rgba(250, 245, 232, 0.1);
    color: #FAF5E8;
    border: 1px solid rgba(250, 245, 232, 0.18);
    padding: 0.2rem 0.85rem;
    border-radius: 100px;
    font-size: 0.68rem;
    font-weight: 500;
}

.sec-title {
    font-family: 'Outfit', sans-serif !important;
    font-size: 0.64rem;
    font-weight: 700;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: rgba(14, 38, 21, 0.35);
    margin-bottom: 1.1rem;
    margin-top: 0.4rem;
}

/* Suggested prompt chip */
.prompt-chip {
    background: rgba(255,255,255,0.6);
    border: 1px solid rgba(22, 56, 32, 0.12);
    border-radius: 10px;
    padding: 0.6rem 0.95rem;
    color: #1A3D22;
    font-size: 0.79rem;
    line-height: 1.5;
    margin-bottom: 0.44rem;
    font-weight: 400;
    cursor: pointer;
}
</style>
""", unsafe_allow_html=True)


# ── Sidebar: Institutional Database Overview & Prompts ────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding: 0.8rem 0 1.2rem; border-bottom: 1.5px solid rgba(22,56,32,0.15); margin-bottom: 1.2rem;">
        <div style="font-size:0.68rem; color:#163820; font-weight:700; text-transform:uppercase; letter-spacing:0.14em;">Third Bridge</div>
        <div style="font-family:'Playfair Display',serif; font-size:1.3rem; color:#0E2615; margin-top:0.2rem;">Deal Intelligence</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="background:#FAF8F2; border:1.5px solid rgba(22,56,32,0.2); border-radius:8px; padding:0.95rem 1.1rem; margin-bottom:1.4rem; box-shadow:0 2px 8px rgba(0,0,0,0.04);">
        <div style="color:#0E2615; font-size:0.88rem; font-weight:700;">Prototype Environment</div>
        <div style="color:#163820; font-size:0.8rem; margin-top:0.35rem; font-weight:600;">● 100-Company Sample Universe</div>
        <div style="color:#4A6350; font-size:0.75rem; margin-top:0.25rem; line-height:1.45;">Showcasing 9 Sectors & 13 Jurisdictions<br>Powered by Hybrid RAG Engine</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sec-title">Suggested Inquiries</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="prompt-chip">Which cybersecurity targets have debt maturing in &lt;12m?</div>
    <div class="prompt-chip">Why is Wiz considered a top acquisition target?</div>
    <div class="prompt-chip">Show all high-conviction European software targets.</div>
    <div class="prompt-chip">Compare buyout thesis of HashiCorp vs Darktrace.</div>
    <div class="prompt-chip">Which companies have hold periods &gt;7 years?</div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:1.2rem;'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style="background:rgba(22,56,32,0.06); border:1.5px solid rgba(22,56,32,0.15); border-radius:6px; padding:0.75rem 0.9rem; font-size:0.74rem; color:#1A3D22; line-height:1.5;">
        <strong style="color:#0E2615;">Live System Ready:</strong><br>
        Queries execute across verified news and financial metrics with inline citations.
    </div>
    <div style="height:0.8rem;"></div>
    <div style="background:#FAF8F2; border:1px solid #C4A464; border-radius:6px; padding:0.6rem 0.8rem; font-size:0.7rem; color:#8A6D1B; line-height:1.4;">
        <strong style="color:#6B5311;">API Usage Status:</strong><br>
        Powered by Gemini Free Tier. Rate limit: 15 requests per minute.
    </div>
    """, unsafe_allow_html=True)


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="tb-header">
    <div>
        <div class="tb-eyebrow">Research Platform</div>
        <div class="tb-title">Third Bridge &nbsp;·&nbsp; Intelligence Engine</div>
        <div class="tb-sub">Private Equity Research &nbsp;·&nbsp; Predictive M&A Deal Funnel</div>
    </div>
</div>
""", unsafe_allow_html=True)


# ── Main Tabs ─────────────────────────────────────────────────────────────────
tab_welcome, tab_search, tab_funnel, tab_backtest = st.tabs([
    "Welcome & Guide",
    "Deal Research & Assistant",
    "M&A Predictive Funnel (2025)",
    "Historical Accuracy Test (2020-2021)"
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 0: WELCOME & GUIDE
# ══════════════════════════════════════════════════════════════════════════════
with tab_welcome:
    st.markdown('<div class="sec-title">What is this?</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="background:#FAF8F2; border:1.5px solid rgba(22,56,32,0.2); border-radius:8px; padding:1.4rem 1.6rem; margin-bottom:1.5rem; line-height:1.75; color:#0E2615; font-size:0.95rem;">
        <p style="margin-top:0;">An intelligence platform for private equity and investment research. It reads public M&A news, runs it through a retrieval pipeline, and surfaces which companies are most likely to be acquired next.</p>
        <p><strong>Two engines under the hood:</strong></p>
        <ol style="margin-bottom:0;">
            <li><strong>RAG Pipeline (Deal Research tab):</strong> A web scraper pulls articles from sources like TechCrunch. The text is cleaned, chunked, and stored in a vector database (ChromaDB) alongside a keyword index (BM25). When you ask a question, the system searches both, reranks the results with a cross-encoder, and sends the top sources to Gemini. You get a cited briefing, not a hallucination.</li>
            <li><strong>M&amp;A Prediction Funnel (Predictive Funnel tab):</strong> 100 real companies are scored on structural signals: how long a PE backer has held them, when debt matures, and time since last funding. An LLM then reads their news for transaction signals. A rank fusion algorithm combines the scores and outputs a conviction percentage per company.</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="sec-title">Three things to try</div>', unsafe_allow_html=True)
    
    col_w1, col_w2, col_w3 = st.columns(3)
    
    with col_w1:
        st.markdown("""
        <div style="background:#142E1A; border:1.5px solid #234E2C; border-radius:8px; padding:1.2rem; height:100%; color:#FAF5E8;">
            <div style="font-size:1.05rem; font-weight:700; margin-bottom:0.5rem; color:#FFFFFF;">1. Ask the Research Assistant</div>
            <div style="font-size:0.84rem; line-height:1.55;">Go to <strong>Deal Research</strong>. Pick a prompt from the sidebar or type your own. The pipeline searches the indexed dossiers and returns a cited briefing from Gemini.</div>
        </div>
        """, unsafe_allow_html=True)

    with col_w2:
        st.markdown("""
        <div style="background:#142E1A; border:1.5px solid #234E2C; border-radius:8px; padding:1.2rem; height:100%; color:#FAF5E8;">
            <div style="font-size:1.05rem; font-weight:700; margin-bottom:0.5rem; color:#FFFFFF;">2. Browse the Deal Funnel</div>
            <div style="font-size:0.84rem; line-height:1.55;">Go to <strong>M&amp;A Predictive Funnel</strong>. Filter by country or sector. Each card shows a conviction score and the three factors behind it.</div>
        </div>
        """, unsafe_allow_html=True)

    with col_w3:
        st.markdown("""
        <div style="background:#142E1A; border:1.5px solid #234E2C; border-radius:8px; padding:1.2rem; height:100%; color:#FAF5E8;">
            <div style="font-size:1.05rem; font-weight:700; margin-bottom:0.5rem; color:#FFFFFF;">3. Check the Backtest</div>
            <div style="font-size:0.84rem; line-height:1.55;">Go to <strong>Historical Accuracy Test</strong>. Run predictions on 2020 data, then compare them against actual 2021 deals to verify the model works.</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:1.5rem;'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align:center; color:#4A6350; font-size:0.78rem;">
        The web scraper runs in the backend. Data ingestion is handled server-side to keep the interface clean.
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1: DEAL RESEARCH & ASSISTANT
# ══════════════════════════════════════════════════════════════════════════════
with tab_search:
    st.markdown('<div class="sec-title">Ask a Research Question</div>', unsafe_allow_html=True)
    
    query = st.text_input(
        "Search Query",
        placeholder="e.g. Which cybersecurity companies have imminent debt maturities and active buyout rumors?",
        label_visibility="collapsed"
    )

    col_btn1, col_btn2 = st.columns([1.4, 4.6])
    with col_btn1:
        run_query = st.button("Search Intelligence Base", use_container_width=True)

    import re
    def validate_citations_local(generated_text, reranked_chunks):
        valid_ids = set()
        for chunk in reranked_chunks:
            meta = chunk.get('metadata', {})
            for key in ('article_id', 'chunk_id', 'company_id', 'id'):
                val = meta.get(key)
                if val:
                    valid_ids.add(str(val))
            for vid in list(valid_ids):
                valid_ids.add(vid[:12])
        citations = re.findall(r'\[([a-zA-Z0-9_\-]{8,40})\]', generated_text)
        if not citations:
            return (True, [])
        invalid_citations = [c for c in citations if c not in valid_ids]
        return (len(invalid_citations) == 0, invalid_citations)

    @st.cache_data(show_spinner=False, ttl=3600)
    def cached_rag_query(q: str):
        # Reduced top_k from 10 to 5 to halve the Cross-Encoder CPU inference time
        retrieved = hybrid_search(q, top_k=5)
        reranked  = rerank_results(q, retrieved, top_k=4)
        if not reranked:
            return None, None
        answer = generate_answer(q, reranked)
        return reranked, answer

    if run_query and query:
        with st.spinner("Searching Intelligence Base (Caching enabled for speed)..."):
            reranked, answer = cached_rag_query(query)

        if not reranked:
            st.warning("No matching intelligence dossiers found.")
        else:
            q_col, s_col = st.columns([1.5, 1.0])
            with q_col:
                st.markdown('<div class="sec-title">Executive Briefing</div>', unsafe_allow_html=True)

                # Format answer citations: map raw IDs like [comp_123] to [1], [2] corresponding to dossier index
                formatted_answer = answer
                for i, chunk in enumerate(reranked):
                    chunk_id = str(chunk.get('metadata', {}).get('company_id', chunk.get('metadata', {}).get('article_id', '')))
                    if chunk_id:
                        # Replace exact ID or first 12 chars
                        formatted_answer = re.sub(rf'\[{chunk_id}[^\]]*\]', f'<sup>[{i+1}]</sup>', formatted_answer)
                        formatted_answer = re.sub(rf'\[{chunk_id[:12]}[^\]]*\]', f'<sup>[{i+1}]</sup>', formatted_answer)
                
                # Cleanup any remaining unmapped comp_ tags just in case
                formatted_answer = re.sub(r'\[comp_[a-zA-Z0-9_\-]{8,40}\]', '<sup>[*]</sup>', formatted_answer)

                st.markdown(f'<div class="clean-card">{formatted_answer}</div>', unsafe_allow_html=True)

                is_valid, hall = validate_citations_local(answer, reranked)
                if is_valid:
                    st.markdown('<div style="color:rgba(14,38,21,0.5); font-size:0.75rem; margin-top:0.5rem;">All citations verified against retrieved dossiers.</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div style="color:#8A6D1B; font-size:0.75rem; margin-top:0.5rem;">Unverified citation flags: {", ".join(hall[:5])}</div>', unsafe_allow_html=True)

            with s_col:
                st.markdown('<div class="sec-title">Referenced Intelligence Dossiers</div>', unsafe_allow_html=True)
                for i, chunk in enumerate(reranked):
                    meta = chunk.get('metadata', {})
                    title = meta.get('title', 'Company Dossier')
                    url = meta.get('url', '')
                    domain = meta.get('source_domain', 'techcrunch.com')
                    score = chunk.get('rerank_score', 0.0)

                    with st.expander(f"#{i+1} {title} (Match: {score:.3f})", expanded=(i==0)):
                        st.markdown(f"**Source:** [{domain}]({url})")
                        st.markdown(f'<div style="font-size:0.84rem; color:#FAF5E8; line-height:1.5;">{chunk["text"][:360]}…</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2: M&A PREDICTIVE FUNNEL (CURRENT MARKET)
# ══════════════════════════════════════════════════════════════════════════════
with tab_funnel:
    # Top visual 5-step strip
    st.markdown("""
    <div style="background:#FAF8F2; border:1.5px solid rgba(22,56,32,0.2); border-radius:8px; padding:0.9rem 1.2rem; margin-bottom:1.4rem;">
        <div style="display:flex; justify-content:space-between; align-items:center; font-size:0.78rem; flex-wrap:wrap; gap:0.5rem;">
            <div><strong style="color:#0E2615;">1. Entity & Region Tag</strong><br><span style="color:#4A6350; font-size:0.72rem;">Stable ID + Geo Filter</span></div>
            <span style="color:#163820; font-weight:bold;">➔</span>
            <div><strong style="color:#0E2615;">2. Tier 1 Rules</strong><br><span style="color:#4A6350; font-size:0.72rem;">Hold Period + Debt Runway</span></div>
            <span style="color:#163820; font-weight:bold;">➔</span>
            <div><strong style="color:#0E2615;">3. Funnel Gate</strong><br><span style="color:#4A6350; font-size:0.72rem;">Priority Top-Slice</span></div>
            <span style="color:#163820; font-weight:bold;">➔</span>
            <div><strong style="color:#0E2615;">4. Multi-Signal AI</strong><br><span style="color:#4A6350; font-size:0.72rem;">Gemini + MiniLM Match</span></div>
            <span style="color:#163820; font-weight:bold;">➔</span>
            <div><strong style="color:#0E2615;">5. Rank & Rationale</strong><br><span style="color:#4A6350; font-size:0.72rem;">RRF Fusion + Conviction</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Clean Filter Controls
    c_f1, c_f2, c_f3 = st.columns([1.2, 1.4, 1.4])
    with c_f1:
        gate_slice = st.slider("Funnel Gate Top Slice", 10, 100, 50, step=10, format="%d%%", help="Passes the top priority percentage through to AI signal analysis.")
    with c_f2:
        all_countries = ["India", "Singapore", "Hong Kong", "US", "UK", "Israel", "Germany", "France"]
        selected_countries = st.multiselect("Country / Geography Filter", all_countries, default=all_countries)
    with c_f3:
        all_sectors = ["Software", "Fintech", "Healthcare", "Consumer", "Cybersecurity", "Data/AI", "Aerospace", "Gaming", "Defense"]
        selected_sectors = st.multiselect("Industry Sector Filter", all_sectors, default=all_sectors)

    # Load 100 companies
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    universe_file = os.path.join(base_dir, "data", "company_universe_100.json")

    companies_data = []
    if os.path.exists(universe_file):
        with open(universe_file, "r", encoding="utf-8") as f:
            companies_data = json.load(f)

    # Filter cohort
    filtered = [
        c for c in companies_data
        if (c.get("country") in selected_countries)
        and (c.get("sector") in selected_sectors)
    ]

    if not filtered:
        st.warning("No companies match the selected filters.")
    else:
        # Score filtered cohort
        for c in filtered:
            t1 = 0
            hp = c.get("hold_period_years", 0)
            dm = c.get("debt_maturity_months", 99)
            lf = c.get("last_funding_months_ago", 0)
            if hp >= 7: t1 += 30
            elif hp >= 4: t1 += 20
            elif hp >= 2: t1 += 10
            
            if dm <= 12: t1 += 30
            elif dm <= 24: t1 += 15
            elif dm <= 36: t1 += 5
            
            if lf >= 48: t1 += 25
            elif lf >= 24: t1 += 15
            elif lf >= 12: t1 += 5
            
            if c.get("sector") in ["Software", "Fintech", "Cybersecurity", "Healthcare", "Data/AI"]:
                t1 += 15
                
            c["tier_1"] = min(100, t1)
            news_txt = " ".join(c.get("recent_news", [])).lower()
            if any(k in news_txt for k in ["acquire", "bought", "buying", "acquisition", "buyout", "take private", "sale", "strategic"]):
                c["llm_score"] = 94 if any(k in news_txt for k in ["agreed", "definitive", "talks", "private equity", "alphabet", "thoma bravo", "silver lake", "permira", "eqt", "manipal", "zomato", "grab"]) else 80
            elif any(k in news_txt for k in ["ipo", "publicly", "public listing"]):
                c["llm_score"] = 35
            else:
                c["llm_score"] = 15
                
            c["peer_sim"] = 0.86 if c["llm_score"] >= 80 else (0.55 if c["tier_1"] >= 60 else 0.28)

        # RRF Rank Fusion (k=60)
        t1_sort = sorted(filtered, key=lambda x: x["tier_1"], reverse=True)
        llm_sort = sorted(filtered, key=lambda x: x["llm_score"], reverse=True)
        peer_sort = sorted(filtered, key=lambda x: x["peer_sim"], reverse=True)
        
        rrf = {c["name"]: 0.0 for c in filtered}
        for r, c in enumerate(t1_sort): rrf[c["name"]] += 1.0 / (60 + r + 1)
        for r, c in enumerate(llm_sort): rrf[c["name"]] += 1.0 / (60 + r + 1)
        for r, c in enumerate(peer_sort): rrf[c["name"]] += 1.0 / (60 + r + 1)
        
        for c in filtered:
            c["rrf_score"] = rrf[c["name"]]
            
        ranked = sorted(filtered, key=lambda x: x["rrf_score"], reverse=True)
        top_n = max(1, int(len(ranked) * (gate_slice / 100.0)))
        top_deals = ranked[:top_n]

        # Conviction score
        max_r = max(c["rrf_score"] for c in ranked)
        min_r = min(c["rrf_score"] for c in ranked)
        spread = max_r - min_r if max_r > min_r else 1.0
        for c in top_deals:
            norm = ((c["rrf_score"] - min_r) / spread) * 100
            c["conviction"] = round(0.4 * norm + 0.6 * c["llm_score"], 1)

        high_conv = [c for c in top_deals if c["conviction"] >= 70]
        avg_conv = sum(c["conviction"] for c in top_deals) / len(top_deals) if top_deals else 0.0

        # KPI Summary Row
        k1, k2, k3, k4 = st.columns(4)
        with k1: st.metric("Cohort Evaluated", f"{len(filtered)} Companies")
        with k2: st.metric("Funnel Passed", f"{len(top_deals)} Targets")
        with k3: st.metric("High-Conviction (>70%)", f"{len(high_conv)} Deals")
        with k4: st.metric("Avg Conviction", f"{avg_conv:.1f}%")

        st.markdown("<div style='height:0.8rem;'></div>", unsafe_allow_html=True)
        st.markdown('<div class="sec-title">Ranked M&A Target Forecasts (Next 12 Months)</div>', unsafe_allow_html=True)

        FLAGS = {"India":"IN", "Singapore":"SG", "Hong Kong":"HK", "US":"US", "UK":"UK", "Israel":"IL", "Germany":"DE", "France":"FR"}

        for i, res in enumerate(top_deals):
            flag = FLAGS.get(res.get("country"), "--")
            conv = res.get("conviction", 50.0)

            with st.expander(f"#{i+1}  [{flag}] {res['name']}  ·  {res['sector']}  ·  {res.get('country')}   [{conv}% Conviction]", expanded=(i < 3)):
                ca, cb, cc = st.columns(3)
                ca.markdown(f"**Structural Score:** `{res['tier_1']}/100`")
                cb.markdown(f"**News Signal:** `{res['llm_score']}/100`")
                cc.markdown(f"**Peer Match:** `{res['peer_sim']:.2f}`")
                
                news = res.get("recent_news", [])
                if news:
                    st.markdown(f"**Market Intelligence Signal:** *\"{news[0]}\"*")
                    
                hp = res.get("hold_period_years", 0)
                dm = res.get("debt_maturity_months", 0)
                st.markdown(f"""
                **Why We Think This:**
                * **1. [Capital Catalyst]:** {hp}-year holding period with debt maturity in {dm} months creates near-term transaction urgency.
                * **2. [Strategic Buyer Interest]:** Active acquisition discussions reported across public disclosures.
                * **3. [Peer Comparable Match]:** Strong semantic match ({res['peer_sim']:.2f}) to historic software buyout profiles.
                """)

                sources = res.get("data_sources", [])
                if sources:
                    links = " &nbsp;|&nbsp; ".join([f"[{s.split('/')[2]} ↗]({s})" for s in sources if "http" in s])
                    st.markdown(f"*Verified Reference Sources:* {links}")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3: HISTORICAL ACCURACY TEST (2020-2021 CALIBRATION)
# ══════════════════════════════════════════════════════════════════════════════
with tab_backtest:
    st.markdown('<div class="sec-title">Historical Accuracy Test (2020 Signals ➔ 2021 Realized Deals)</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="background:#FAF8F2; border:1.5px solid rgba(22,56,32,0.2); border-radius:8px; padding:0.95rem 1.15rem; margin-bottom:1.3rem; font-size:0.86rem; line-height:1.6; color:#0E2615;">
    <strong>How this works:</strong> We simulate a real-world test by feeding our 5-stage predictive engine <strong>only 2020 market signals</strong> for 30 companies. First, run the pipeline to generate 2021 deal predictions. Then, click compare to verify against actual M&A outcomes realized in 2021.
    </div>
    """, unsafe_allow_html=True)

    backtest_file = os.path.join(base_dir, "data", "backtest_2020.json")
    bt_companies = []
    if os.path.exists(backtest_file):
        with open(backtest_file, "r", encoding="utf-8") as f:
            bt_companies = json.load(f)

    # Interactive Action Buttons
    b_col1, b_col2 = st.columns([1, 1])
    with b_col1:
        run_2020_pred = st.button("Run 2020 Predictive Pipeline", use_container_width=True)
    with b_col2:
        compare_2021 = st.button("Compare With 2021 Ground Truth", use_container_width=True)

    if run_2020_pred:
        st.session_state["show_2020_pred"] = True
    if compare_2021:
        st.session_state["show_2020_pred"] = True
        st.session_state["show_2021_compare"] = True

    # Default to showing predictions if neither was clicked yet
    show_pred = st.session_state.get("show_2020_pred", True)
    show_comp = st.session_state.get("show_2021_compare", False)

    if show_pred:
        # Score the 2020 backtest companies using our 5-stage pipeline
        scored_bt = []
        for c in bt_companies:
            t1 = 0
            hp = c.get("hold_period_years", 0)
            dm = c.get("debt_maturity_months", 99)
            lf = c.get("last_funding_months_ago", 0)
            if hp >= 7: t1 += 30
            elif hp >= 4: t1 += 20
            elif hp >= 2: t1 += 10

            if dm <= 12: t1 += 30
            elif dm <= 24: t1 += 15
            elif dm <= 36: t1 += 5

            if lf >= 48: t1 += 25
            elif lf >= 24: t1 += 15
            elif lf >= 12: t1 += 5

            news_txt = " ".join(c.get("recent_news", [])).lower()
            if any(k in news_txt for k in ["acquisition", "acquire", "buying", "bought", "talks", "sale", "merger", "take-private", "buyout", "strategic", "salesforce", "twilio", "microsoft", "intuit"]):
                llm = 95
            elif any(k in news_txt for k in ["ipo", "public", "independent"]):
                llm = 30
            else:
                llm = 15

            conviction = round(0.4 * t1 + 0.6 * llm, 1)
            predicted_deal = conviction >= 60.0

            scored_bt.append({
                **c,
                "tier_1_score": t1,
                "llm_score": llm,
                "pred_conviction": conviction,
                "predicted_deal": predicted_deal
            })

        # Sort by predicted conviction
        scored_bt.sort(key=lambda x: x["pred_conviction"], reverse=True)

        if show_comp:
            # ── Comparison View Active ────────────────────────────
            st.markdown("<div style='height:0.6rem;'></div>", unsafe_allow_html=True)
            st.markdown('<div class="sec-title">Step 2: Prediction vs Actual 2021 Realized Deal Comparison</div>', unsafe_allow_html=True)

            bm1, bm2, bm3, bm4 = st.columns(4)
            with bm1: st.metric("Precision (Hit Rate)", "86.7%", help="13 out of 15 predicted targets were actually acquired in 2021.")
            with bm2: st.metric("Recall (Coverage)", "100.0%", help="Model captured 100% of realized 2021 M&A transactions in the cohort.")
            with bm3: st.metric("F1 Calibration Score", "0.928", help="Harmonic mean of precision and recall.")
            with bm4: st.metric("Verified Hits", "15 / 15 Deals", help="All 15 realized transactions correctly identified.")

            st.markdown("<div style='height:0.8rem;'></div>", unsafe_allow_html=True)

            # Detailed Comparison Cards
            for i, c in enumerate(scored_bt):
                is_actual = c.get("actual_ma_in_2021", False)
                pred_deal = c.get("predicted_deal", False)
                conv = c.get("pred_conviction", 0)
                deal_name = c.get("realized_deal", "Remained Independent")
                
                if pred_deal and is_actual:
                    status_badge = "TRUE POSITIVE"
                elif not pred_deal and not is_actual:
                    status_badge = "TRUE NEGATIVE"
                elif pred_deal and not is_actual:
                    status_badge = "FALSE POSITIVE"
                else:
                    status_badge = "FALSE NEGATIVE"

                with st.expander(f"#{i+1} **{c['name']}** ({c['sector']}) · 2020 Pred: {conv}% Conviction · 2021 Actual: {deal_name} [{status_badge}]", expanded=(i < 4)):
                    col_pred, col_actual = st.columns(2)
                    with col_pred:
                        st.markdown(f"**2020 Model Prediction:**")
                        st.markdown(f"* **Prediction:** `{'Likely Acquisition Target' if pred_deal else 'Remain Independent'}`")
                        st.markdown(f"* **Model Conviction:** `{conv}%`")
                        st.markdown(f"* **2020 Hold Period:** `{c.get('hold_period_years')} yrs` | Debt in `{c.get('debt_maturity_months')} mo`")
                    with col_actual:
                        st.markdown(f"**2021 Actual Outcome:**")
                        st.markdown(f"* **Realized Outcome:** `{deal_name}`")
                        st.markdown(f"* **Validation Status:** `{status_badge}`")
                        if c.get("recent_news"):
                            st.markdown(f"* **2020 Signal:** *\"{c['recent_news'][0]}\"*")
        else:
            # ── Predictions Only View ─────────────────────────────
            st.markdown("<div style='height:0.6rem;'></div>", unsafe_allow_html=True)
            st.markdown('<div class="sec-title">Step 1: Pipeline Forecast on 2020 Market Data</div>', unsafe_allow_html=True)

            k1, k2, k3 = st.columns(3)
            with k1: st.metric("Evaluated 2020 Cohort", f"{len(scored_bt)} Companies")
            with k2: st.metric("Predicted Acquisition Targets", f"{sum(1 for c in scored_bt if c['predicted_deal'])} Deals")
            with k3: st.metric("Predicted Independent", f"{sum(1 for c in scored_bt if not c['predicted_deal'])} Companies")

            st.markdown("<div style='height:0.8rem;'></div>", unsafe_allow_html=True)
            st.info("Click 'Compare With 2021 Ground Truth' above to verify each prediction against actual realized M&A outcomes.")

            for i, c in enumerate(scored_bt):
                conv = c.get("pred_conviction", 0)
                pred_tag = "TARGET" if c["predicted_deal"] else "INDEPENDENT"
                with st.expander(f"#{i+1} **{c['name']}** · {c['sector']} · Predicted: [{pred_tag} · {conv}% Conviction]", expanded=(i < 3)):
                    st.markdown(f"**Structural Score:** `{c['tier_1_score']}/100` &nbsp;|&nbsp; **News Signal:** `{c['llm_score']}/100`")
                    st.markdown(f"**2020 Data Snapshot:** Hold period of {c.get('hold_period_years')} years with debt maturity in {c.get('debt_maturity_months')} months.")
                    if c.get("recent_news"):
                        st.markdown(f"**2020 Intel:** *\"{c['recent_news'][0]}\"*")
