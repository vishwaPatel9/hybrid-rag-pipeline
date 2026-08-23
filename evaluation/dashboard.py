import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import streamlit as st
from ingestion.scraper import scrape_urls
from processing.advanced_cleaner import advanced_clean_pipeline
from processing.chunker import process_chunks
from indexing.embed import embed_and_store
from indexing.bm25_index import build_bm25_index
import pandas as pd
from retrieval.hybrid_search import hybrid_search
from retrieval.reranker import rerank_results
from generation.rag_pipeline import generate_answer
from generation.citation_validator import validate_citations
from generation.contradiction_detector import detect_contradictions

st.set_page_config(
    page_title="Third Bridge · Intelligence Engine",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,500;0,600;1,400&family=Inter:wght@300;400;500;600&display=swap');

/*
  PALETTE
  Background:   #0F1A0D   (deep forest, almost black)
  Surface:      #152112   (dark forest green)
  Border:       #213320   (muted green border)
  Cream:        #EDE3CC   (warm cream — primary text)
  Parchment:    #C4B896   (muted beige — secondary text)
  Dust:         #7A6E57   (dusty tan — tertiary / labels)
  Accent:       #3A6641   (classic dark green — CTAs, highlights)
  Accent light: #4D8558   (hover state)
  Gold:         #B8943F   (warm gold for special highlights)
*/

*, *::before, *::after { box-sizing: border-box; margin: 0; }

html, body, .stApp {
    font-family: 'Inter', sans-serif !important;
    background: #0F1A0D !important;
    color: #EDE3CC !important;
}

/* ── Hide Streamlit chrome ─────────────────────── */
#MainMenu, footer, [data-testid="stHeader"],
[data-testid="stToolbar"], .stDeployButton { display: none !important; }

/* ── App container ─────────────────────────────── */
[data-testid="stAppViewContainer"] > .main {
    background: #0F1A0D !important;
}
.block-container {
    padding: 2rem 2.5rem 3rem !important;
    max-width: 1360px !important;
}

/* ── Sidebar ───────────────────────────────────── */
[data-testid="stSidebar"] {
    background: #0C1509 !important;
    border-right: 1px solid #213320 !important;
}
[data-testid="stSidebar"] > div:first-child {
    padding: 0 !important;
}

/* ── Global text overrides ─────────────────────── */
h1, h2, h3, h4 {
    font-family: 'EB Garamond', Georgia, serif !important;
    color: #EDE3CC !important;
    letter-spacing: 0.01em;
    font-weight: 500 !important;
}
p, li, span, div {
    color: #C4B896 !important;
}
label {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.7rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    color: #7A6E57 !important;
}
code, pre {
    font-size: 0.82rem !important;
    background: #1C2B19 !important;
    color: #B8943F !important;
    border-radius: 4px !important;
    padding: 0.1em 0.45em !important;
}

/* ── Text inputs ───────────────────────────────── */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea {
    background: #152112 !important;
    border: 1px solid #213320 !important;
    border-radius: 6px !important;
    color: #EDE3CC !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.9rem !important;
    padding: 0.7rem 0.9rem !important;
    transition: border-color 0.2s !important;
    caret-color: #4D8558 !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
    border-color: #3A6641 !important;
    box-shadow: 0 0 0 3px rgba(58, 102, 65, 0.18) !important;
    outline: none !important;
}
[data-testid="stTextInput"] input::placeholder,
[data-testid="stTextArea"] textarea::placeholder {
    color: #4A4236 !important;
}

/* ── Buttons ───────────────────────────────────── */
[data-testid="stButton"] > button {
    background: #3A6641 !important;
    color: #EDE3CC !important;
    border: 1px solid #4D8558 !important;
    border-radius: 6px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.82rem !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
    padding: 0.65rem 1.25rem !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 2px 12px rgba(58, 102, 65, 0.3) !important;
    width: 100% !important;
}
[data-testid="stButton"] > button:hover {
    background: #4D8558 !important;
    border-color: #5A9A66 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 18px rgba(58, 102, 65, 0.45) !important;
    color: #EDE3CC !important;
}
[data-testid="stButton"] > button:active {
    transform: translateY(0) !important;
}

/* ── Slider ────────────────────────────────────── */
.stSlider [data-baseweb="slider"] div[role="slider"] {
    background: #3A6641 !important;
    border-color: #3A6641 !important;
}
.stSlider [data-baseweb="slider"] [data-testid="stSliderTrackFill"] {
    background: #3A6641 !important;
}

/* ── Checkbox ──────────────────────────────────── */
[data-testid="stCheckbox"] label {
    color: #C4B896 !important;
    font-size: 0.875rem !important;
    text-transform: none !important;
    letter-spacing: normal !important;
    font-weight: 400 !important;
}

/* ── Expanders ─────────────────────────────────── */
[data-testid="stExpander"] {
    background: #152112 !important;
    border: 1px solid #213320 !important;
    border-radius: 6px !important;
    margin-bottom: 0.4rem !important;
}
[data-testid="stExpander"] summary {
    color: #C4B896 !important;
    font-size: 0.8rem !important;
    font-weight: 500 !important;
    padding: 0.65rem 0.9rem !important;
    font-family: 'Inter', sans-serif !important;
}
[data-testid="stExpander"] summary:hover { color: #EDE3CC !important; }
[data-testid="stExpander"] summary svg { fill: #7A6E57 !important; }

/* ── Divider ───────────────────────────────────── */
hr { border-color: #213320 !important; margin: 1.25rem 0 !important; }

/* ── Alerts ────────────────────────────────────── */
[data-testid="stAlert"] {
    background: #152112 !important;
    border: 1px solid #213320 !important;
    border-radius: 6px !important;
    font-size: 0.85rem !important;
    font-family: 'Inter', sans-serif !important;
}

/* ══════════════════════════════════════════════════
   CUSTOM COMPONENTS
══════════════════════════════════════════════════ */

/* Top header bar */
.tb-header {
    display: flex;
    align-items: flex-start;
    gap: 1.25rem;
    padding: 1.5rem 0 1.75rem;
    border-bottom: 1px solid #213320;
    margin-bottom: 2rem;
}
.tb-wordmark {
    font-family: 'EB Garamond', Georgia, serif !important;
    font-size: 1.65rem !important;
    font-weight: 500 !important;
    color: #EDE3CC !important;
    letter-spacing: 0.01em;
    line-height: 1;
}
.tb-divider-dot {
    color: #3A6641 !important;
    font-size: 1.65rem !important;
    line-height: 1;
    padding: 0 0.1rem;
}
.tb-sub {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.72rem !important;
    color: #7A6E57 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    margin-top: 0.35rem !important;
}
.tb-badge {
    margin-left: auto;
    align-self: flex-start;
    margin-top: 0.2rem;
    background: rgba(58, 102, 65, 0.15);
    border: 1px solid #3A6641;
    color: #4D8558 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.65rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.12em !important;
    padding: 0.2rem 0.65rem;
    border-radius: 3px;
    text-transform: uppercase;
}

/* Sidebar header */
.sb-header {
    padding: 1.5rem 1.25rem 1.25rem;
    border-bottom: 1px solid #213320;
    margin-bottom: 1.25rem;
}
.sb-eyebrow {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.62rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.16em !important;
    text-transform: uppercase !important;
    color: #3A6641 !important;
    margin-bottom: 0.4rem;
}
.sb-title {
    font-family: 'EB Garamond', Georgia, serif !important;
    font-size: 1.1rem !important;
    font-weight: 500 !important;
    color: #EDE3CC !important;
    line-height: 1.3;
    margin-bottom: 0.4rem;
}
.sb-desc {
    font-size: 0.78rem !important;
    color: #7A6E57 !important;
    line-height: 1.55 !important;
    font-family: 'Inter', sans-serif !important;
}

/* Section labels */
.sec-label {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.65rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.14em !important;
    text-transform: uppercase !important;
    color: #7A6E57 !important;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 0.9rem;
}
.sec-label::after {
    content: '';
    flex: 1;
    height: 1px;
    background: #213320;
}

/* Answer card */
.answer-card {
    background: #152112;
    border: 1px solid #213320;
    border-left: 3px solid #3A6641;
    border-radius: 6px;
    padding: 1.6rem 1.75rem;
    font-family: 'EB Garamond', Georgia, serif !important;
    font-size: 1.05rem !important;
    line-height: 1.9 !important;
    color: #DDD5BC !important;
    margin-top: 0.5rem;
}
.answer-card p  { color: #DDD5BC !important; line-height: 1.9 !important; margin-bottom: 0.75rem; }
.answer-card li { color: #C4B896 !important; line-height: 1.8 !important; margin-bottom: 0.35rem; }
.answer-card strong, .answer-card b {
    color: #EDE3CC !important;
    font-weight: 600 !important;
}
.answer-card h2, .answer-card h3, .answer-card h4 {
    color: #EDE3CC !important;
    font-size: 1rem !important;
    margin-top: 1rem;
    margin-bottom: 0.4rem;
}
.answer-card code {
    background: #1C2B19 !important;
    color: #B8943F !important;
    font-size: 0.82em !important;
    padding: 0.1em 0.4em !important;
    border-radius: 3px !important;
    font-family: 'Courier New', monospace !important;
}

/* Status pills */
.pill {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.75rem !important;
    font-weight: 500 !important;
    padding: 0.28rem 0.75rem;
    border-radius: 3px;
    margin-top: 0.65rem;
    letter-spacing: 0.02em;
}
.pill-ok     { background: rgba(58,102,65,0.14); border:1px solid #3A6641; color:#4D8558 !important; }
.pill-warn   { background: rgba(184,148,63,0.10); border:1px solid #B8943F; color:#C8A445 !important; }
.pill-danger { background: rgba(160,50,50,0.12); border:1px solid #7A3030; color:#C47A7A !important; }

/* Source card */
.src-meta {
    font-family: 'Inter', sans-serif !important;
    margin-bottom: 0.5rem;
}
.src-rank   { font-size:0.62rem !important; font-weight:700 !important; color:#3A6641 !important; letter-spacing:0.1em; text-transform:uppercase; }
.src-domain { font-size:0.88rem !important; font-weight:500 !important; color:#EDE3CC !important; margin-top:0.1rem; }
.src-score  { font-size:0.72rem !important; color:#7A6E57 !important; }
.src-text   { font-family:'EB Garamond', Georgia, serif !important; font-size:0.92rem !important; color:#7A6E57 !important; line-height:1.7 !important; margin-top:0.6rem; }

/* Contradiction block */
.conflict-card {
    background: rgba(120,40,40,0.08);
    border: 1px solid #5A2A2A;
    border-left: 3px solid #7A3030;
    border-radius: 6px;
    padding: 1rem 1.25rem;
    margin-top: 0.5rem;
    font-family: 'Inter', sans-serif !important;
}
.conflict-card .vs      { color:#C4B896 !important; font-size:0.75rem !important; }
.conflict-card .names   { color:#DDD5BC !important; font-size:0.85rem !important; font-weight:500; }
.conflict-card .explain { color:#A89070 !important; font-size:0.875rem !important; margin-top:0.4rem; line-height:1.6; }

/* Tip box */
.tip-box {
    background: rgba(58,102,65,0.07);
    border: 1px solid #213320;
    border-radius: 5px;
    padding: 0.75rem 1rem;
    margin-top: 1rem;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.75rem !important;
    color: #7A6E57 !important;
    line-height: 1.55;
}
.tip-box em { color: #4D8558 !important; font-style: normal; font-weight: 500; }
</style>
""", unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sb-header">
        <div class="sb-eyebrow">Third Bridge</div>
        <div class="sb-title">Data Ingestion</div>
        <div class="sb-desc">Paste one URL per line. The pipeline will scrape, clean, chunk, and index each source automatically.</div>
    </div>
    """, unsafe_allow_html=True)

    url_input = st.text_area(
        "Target URLs",
        placeholder="https://www.thirdbridge.com/en-us\nhttps://bloomberg.com/...",
        height=155,
        label_visibility="visible"
    )

    if st.button("Execute Ingestion", use_container_width=True):
        urls = [u.strip() for u in url_input.strip().splitlines() if u.strip()]
        if not urls:
            st.error("Enter at least one URL.")
        else:
            base_dir        = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            raw_json        = os.path.join(base_dir, "ingestion",  "raw_articles.json")
            cleaned_parquet = os.path.join(base_dir, "processing", "cleaned_articles.parquet")
            chunked_parquet = os.path.join(base_dir, "processing", "chunked_articles.parquet")

            with st.spinner(f"Scraping {len(urls)} source(s)…"):
                articles = scrape_urls(urls, max_workers=5)
                with open(raw_json, "w", encoding="utf-8") as f:
                    json.dump(articles, f, ensure_ascii=False, indent=4)

            if not articles:
                st.error("No content extracted. Verify the URLs.")
            else:
                with st.spinner("Data quality pipeline…"):
                    df_raw   = pd.DataFrame(articles)
                    df_clean = advanced_clean_pipeline(df_raw)
                    df_clean.to_parquet(cleaned_parquet, index=False)
                    process_chunks(cleaned_parquet, chunked_parquet)

                with st.spinner("Embedding → ChromaDB · BM25…"):
                    embed_and_store(chunked_parquet)
                    build_bm25_index(chunked_parquet)

                st.success(f"{len(articles)} source(s) indexed.")

    st.markdown("""
    <div class="tip-box">
        <em>Re-index anytime</em> — ChromaDB upsert is idempotent. Existing records are safely overwritten.
    </div>
    """, unsafe_allow_html=True)


# ── Main ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="tb-header">
    <div>
        <div style="display:flex;align-items:baseline;gap:0">
            <span class="tb-wordmark">Third Bridge</span>
            <span class="tb-divider-dot">&nbsp;·&nbsp;</span>
            <span class="tb-wordmark">Intelligence Engine</span>
        </div>
        <div class="tb-sub">Hybrid retrieval &nbsp;·&nbsp; Cross-encoder reranking &nbsp;·&nbsp; Gemini generation</div>
    </div>
    <div class="tb-badge">Live · v2.0</div>
</div>
""", unsafe_allow_html=True)

query = st.text_input(
    "Research Query",
    placeholder="e.g.  What is Third Bridge's value proposition for private equity firms?",
    label_visibility="visible"
)

col_k, col_c = st.columns([1, 1])
with col_k:
    top_k = st.slider("Retrieval depth", min_value=3, max_value=10, value=5)
with col_c:
    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
    check_contradictions = st.checkbox("Enable contradiction analysis", value=True)

st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)

if st.button("Run Intelligence Pipeline", use_container_width=True):
    if not query.strip():
        st.warning("Enter a research query above.")
    else:
        with st.spinner("Hybrid search — vector + BM25 fusion…"):
            retrieved = hybrid_search(query, top_k=20)

        if not retrieved:
            st.markdown('<div class="pill pill-warn">No indexed sources found — ingest URLs via the sidebar first.</div>', unsafe_allow_html=True)
        else:
            with st.spinner("Cross-encoder reranking…"):
                reranked = rerank_results(query, retrieved, top_k=top_k)

            answer_col, source_col = st.columns([3, 2], gap="large")

            # ── Left: Executive Answer ───────────────────────────────────────
            with answer_col:
                st.markdown('<div class="sec-label">Executive Briefing</div>', unsafe_allow_html=True)

                with st.spinner("Synthesising response…"):
                    answer = generate_answer(query, reranked)

                st.markdown(f'<div class="answer-card">{answer}</div>', unsafe_allow_html=True)

                # Citation validation
                validation = validate_citations(answer, reranked)
                if validation['has_citations']:
                    if validation['all_valid']:
                        st.markdown(
                            f'<div class="pill pill-ok">&#10003; {validation["total_citations"]} citation(s) verified — no hallucinations detected</div>',
                            unsafe_allow_html=True
                        )
                    else:
                        st.markdown(
                            f'<div class="pill pill-danger">&#10007; Hallucination flag — {validation["message"]}</div>',
                            unsafe_allow_html=True
                        )
                else:
                    st.markdown(
                        '<div class="pill pill-warn">— Response contains no inline source citations</div>',
                        unsafe_allow_html=True
                    )

                # Contradiction analysis
                if check_contradictions:
                    st.markdown("<div style='height:1.25rem'></div>", unsafe_allow_html=True)
                    st.markdown('<div class="sec-label">Contradiction Analysis</div>', unsafe_allow_html=True)

                    with st.spinner("Comparing sources for contradictions…"):
                        contradictions = detect_contradictions(query, reranked)

                    if contradictions:
                        for c in contradictions:
                            st.markdown(f"""
                            <div class="conflict-card">
                                <div class="names">{c['author_1']} <span class="vs">({c['source_1']})</span>
                                &nbsp;vs&nbsp;
                                {c['author_2']} <span class="vs">({c['source_2']})</span></div>
                                <div class="explain">{c['explanation']}</div>
                            </div>""", unsafe_allow_html=True)
                    else:
                        st.markdown(
                            '<div class="pill pill-ok">&#10003; No contradictions detected across top sources</div>',
                            unsafe_allow_html=True
                        )

            # ── Right: Source Intelligence ───────────────────────────────────
            with source_col:
                st.markdown('<div class="sec-label">Source Intelligence</div>', unsafe_allow_html=True)

                for i, chunk in enumerate(reranked):
                    score  = chunk.get('rerank_score', 0.0)
                    domain = chunk['metadata'].get('source_domain', 'Unknown')
                    author = chunk['metadata'].get('author', 'Unknown')
                    url    = chunk['metadata'].get('url', '')
                    art_id = chunk['metadata'].get('article_id', '')

                    with st.expander(f"#{i+1}  {domain}  ·  {score:.3f}"):
                        st.markdown(f"""
                        <div class="src-meta">
                            <div class="src-rank">Rank {i+1} &nbsp;·&nbsp; Score {score:.4f}</div>
                            <div class="src-domain">{domain}</div>
                            <div class="src-score">{author}</div>
                        </div>""", unsafe_allow_html=True)

                        if url:
                            st.markdown(f"[Open source ↗]({url})")

                        st.caption(f"ID: `{art_id}`")

                        st.markdown(
                            f'<div class="src-text">{chunk["text"][:480]}…</div>',
                            unsafe_allow_html=True
                        )
