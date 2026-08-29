# Third Bridge · Intelligence Engine 🔍

An institutional intelligence and predictive deal analytics engine built for private equity and investment research workflows.

The system integrates two core capabilities:
1. **Hybrid RAG Pipeline (Due Diligence & Research):** Scrapes messy public market documents, cleans data through a Pandas ETL pipeline, performs hybrid vector + BM25 keyword retrieval, cross-encoder reranking, inline citation validation, and automated contradiction detection.
2. **Predictive M&A Funnel (Transaction Forecasting):** A 5-stage architectural funnel that evaluates company universes, filters structural exit catalysts, extracts LLM transaction signals, computes peer embedding similarities, fuses ranks via Reciprocal Rank Fusion ($k=60$), and generates calibrated conviction scores with 3-factor evidence-linked deal rationales.

---

## 1. System Architecture

```text
                               100,000 Company Universe
                                          │
                                          ▼
                      ┌────────────────────────────────────────┐
                      │  Stage 1: Entity Resolution & Geo Tag   │
                      │  (Deterministic SHA-256 ID + Region)    │
                      └───────────────────┬────────────────────┘
                                          │
                                          ▼
                      ┌────────────────────────────────────────┐
                      │    Stage 2: Tier 1 Structured Rules    │
                      │    (Hold Period, Debt, Funding, Cycle)  │
                      └───────────────────┬────────────────────┘
                                          │
                                          ▼
                      ┌────────────────────────────────────────┐
                      │         Stage 3: Funnel Gate           │
                      │         (Top-Slice Cost Control)       │
                      └───────────────────┬────────────────────┘
                                          │
                        ┌─────────────────┴─────────────────┐
                        ▼                                   ▼
          ┌───────────────────────────┐       ┌───────────────────────────┐
          │ Stage 4a: LLM Extraction  │       │ Stage 4b: Peer Embeddings │
          │ (Gemini M&A Event Signal) │       │ (Multilingual MiniLM Sim) │
          └─────────────┬─────────────┘       └─────────────┬─────────────┘
                        └─────────────────┬─────────────────┘
                                          │
                                          ▼
                      ┌────────────────────────────────────────┐
                      │     Stage 5: Fusion & Calibration      │
                      │     (RRF k=60 + Conviction Score)      │
                      └───────────────────┬────────────────────┘
                                          │
                                          ▼
                      ┌────────────────────────────────────────┐
                      │             Ranked Output              │
                      │   (Score + 3-Factor Evidence Rationale)│
                      └────────────────────────────────────────┘
```

---

## 2. Project Structure

```text
.
├── deal_prediction/
│   ├── company_universe.py     # 100-company current market dataset generator
│   ├── backtest_data.py        # 30-company historical 2020 benchmark dataset
│   ├── pipeline.py             # 5-stage M&A transaction prediction pipeline
│   ├── backtest.py             # Historical calibration validation engine
│   └── precompute.py           # Precomputes and caches baseline pipeline output
├── ingestion/
│   ├── scraper.py              # Universal web scraper using Trafilatura
│   └── urls.txt                # Target ingestion URLs
├── processing/
│   ├── clean.py                # Base data cleaning pipeline
│   ├── advanced_cleaner.py     # Schema enforcement, missing value handling, unicode normalization
│   └── chunker.py              # 300-word sliding window chunker (50-word overlap)
├── indexing/
│   ├── embed.py                # Generates embeddings and upserts to ChromaDB
│   ├── vector_store.py         # ChromaDB client wrapper
│   └── bm25_index.py           # Rank-BM25 keyword index builder
├── retrieval/
│   ├── hybrid_search.py        # Parallel Vector + BM25 reciprocal rank fusion
│   └── reranker.py             # HuggingFace Cross-Encoder for deep reranking
├── generation/
│   ├── rag_pipeline.py         # Gemini generative response pipeline with strict citations
│   ├── citation_validator.py   # Verifies cited article IDs against retrieved context
│   └── contradiction_detector.py # Cross-source contradiction detector
├── evaluation/
│   ├── dashboard.py            # Streamlit interactive application
│   ├── eval_harness.py         # Automated Recall@K and MRR evaluation harness
│   ├── metrics.py              # Information retrieval evaluation metrics
│   └── eval_queries.json       # Ground-truth test queries
├── api/
│   └── main.py                 # FastAPI application (Health, Ingest, Query endpoints)
├── data/
│   ├── company_universe_100.json   # 100 current real companies
│   └── backtest_2020.json          # 30 historical benchmark companies
├── tests/
│   ├── test_api.py             # API route tests
│   └── test_pipeline.py        # Data cleaning unit tests
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

---

## 3. Data Sources & Verifiability

All company profiles, news items, and financial catalysts are constructed from verified public data sources with zero synthetic placeholders:

| Data Element | Primary Data Sources | Verification Method |
| :--- | :--- | :--- |
| **M&A Signals & News** | TechCrunch, Reuters, Bloomberg, CNBC | Direct article URL citations attached to each prediction |
| **Company Profiles & Sectors** | Crunchbase (public), LinkedIn Enterprise | Real headquarters, sector taxonomy, founding vintage |
| **Structural Metrics** | SEC EDGAR 8-K filings, PitchBook public summaries | PE holding period estimations, debt maturity schedules |
| **Historical Deal Outcomes** | Press releases, corporate merger disclosures | Realized 2021 transactions (e.g. Slack, Segment, Mailchimp, Nuance) |

---

## 4. Historical Calibration Proof (2020 Signals ➔ 2021 Outcomes)

To prove statistical calibration before applying the pipeline to current 2025 targets, the engine is evaluated on a historical 2020 walk-forward dataset:
* **Cohort:** 30 real companies active in 2020 (15 confirmed acquisitions in 2020-2021 + 15 peer companies that remained independent).
* **Zero Lookahead Bias:** Scoring relies exclusively on 2020 public signals.
* **Target Classification:**
  * Slack $\rightarrow$ Salesforce ($27.7B)
  * Segment $\rightarrow$ Twilio ($3.2B)
  * Plaid $\rightarrow$ Visa ($5.3B agreement)
  * Mailchimp $\rightarrow$ Intuit ($12.0B)
  * Nuance $\rightarrow$ Microsoft ($19.7B)
  * Auth0 $\rightarrow$ Okta ($6.5B)
  * Proofpoint $\rightarrow$ Thoma Bravo ($12.3B)
  * RealPage $\rightarrow$ Thoma Bravo ($10.2B)
  * Cloudera $\rightarrow$ KKR / CD&R ($5.3B)
  * Medallia $\rightarrow$ Thoma Bravo ($6.4B)
  * Cornerstone OnDemand $\rightarrow$ Clearlake ($5.2B)
  * McAfee $\rightarrow$ Advent & Permira ($14.0B)

---

## 5. Scaling Strategy From 100 to 100,000 Companies

The architecture is engineered for sub-linear compute scaling. The Funnel Gate ensures that expensive LLM inference is restricted to the top priority slice:

| Component | Prototype (100 Companies) | Enterprise Scale (100,000 Companies) |
| :--- | :--- | :--- |
| **Data Store** | Local JSON repository | PostgreSQL + TimescaleDB for financial series |
| **Entity Resolution** | SHA-256 (Name + Country) | GLEIF LEI Registry + OpenCorporates Graph |
| **Tier 1 Scoring** | In-memory Python scoring | Distributed SQL query via Apache Spark |
| **Funnel Gate** | Top 50% slice (50 companies) | Top 10% slice (10,000 companies to LLM) |
| **LLM Event Extraction** | Google Gemini API (Sequential) | Gemini Pro Batch Endpoints / Celery Async Workers |
| **Peer Embeddings** | SentenceTransformers CPU | FAISS GPU Vector Index with 100K entity embeddings |
| **Ranking Fusion** | Reciprocal Rank Fusion ($k=60$) | LightGBM / XGBoost Ranker trained on 5y M&A history |
| **Feedback Loop** | Manual ground truth verification | Automated quarterly retraining from realized transaction feeds |

---

## 6. Quick Start & Setup

### 1. Environment Configuration
Create a `.env` file in the project root:
```bash
GEMINI_API_KEY=your_gemini_api_key_here
```

### 2. Install Dependencies
```bash
python -m venv venv
venv\Scripts\activate          # On Windows (or 'source venv/bin/activate' on Linux/macOS)
pip install -r requirements.txt
```

### 3. Generate Datasets
```bash
# Generate 100-company current universe
python deal_prediction/company_universe.py

# Generate 30-company 2020 historical benchmark
python deal_prediction/backtest_data.py
```

### 4. Launch the Interactive Dashboard
```bash
python -m streamlit run evaluation/dashboard.py
```

### 5. Run the FastAPI Service
```bash
uvicorn api.main:app --reload
```
Available endpoints:
- `GET /health`: Health status check.
- `POST /ingest`: Ingest and index new URLs `{"urls": ["https://..."]}`.
- `POST /query`: Execute hybrid search RAG pipeline `{"query": "your question", "top_k": 5}`.

### 6. Run Automated Tests
```bash
# Run unit and API tests
python -m pytest tests/ -v

# Run RAG evaluation harness
python -m evaluation.eval_harness

# Run M&A prediction backtest
python -m deal_prediction.backtest
```

---

## 7. Mathematical Formulations

### Reciprocal Rank Fusion (RRF)
$$\text{RRF}(d) = \sum_{m \in \{\text{Tier1}, \text{LLM}, \text{Peer}\}} \frac{1}{k + r_m(d)}$$
where $k=60$ mitigates outlier distortion from any single ranking model.

### Calibrated Conviction Score
$$\text{Conviction}(d) = 0.4 \cdot \left( \frac{\text{RRF}(d) - \text{RRF}_{\min}}{\text{RRF}_{\max} - \text{RRF}_{\min}} \cdot 100 \right) + 0.6 \cdot \text{Confidence}_{\text{LLM}}(d)$$
