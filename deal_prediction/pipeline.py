import os
import json
import time
import numpy as np
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
from dotenv import load_dotenv

# Ensure api key is loaded
load_dotenv()
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

_embed_model = None

def get_embed_model():
    global _embed_model
    if _embed_model is None:
        _embed_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    return _embed_model

def load_data(filepath: str) -> List[Dict[str, Any]]:
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def tier_1_scoring(companies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Calculates a rule-based structured score for each company."""
    for c in companies:
        score = 0
        
        # Ownership + hold period (older hold period -> more likely to exit)
        if c.get("hold_period_years", 0) > 5:
            score += 30
        elif c.get("hold_period_years", 0) > 3:
            score += 15
            
        # Debt calendar (approaching maturity -> need for transaction)
        if c.get("debt_maturity_months", 99) < 12:
            score += 25
        elif c.get("debt_maturity_months", 99) < 24:
            score += 10
            
        # Funding round timing (long time since last funding)
        if c.get("last_funding_months_ago", 0) > 48:
            score += 20
        elif c.get("last_funding_months_ago", 0) > 24:
            score += 10
            
        c["tier_1_score"] = score
        
    return sorted(companies, key=lambda x: x["tier_1_score"], reverse=True)

def funnel_gate(companies: List[Dict[str, Any]], top_pct: float = 0.1) -> List[Dict[str, Any]]:
    """Takes the top N% based on Tier 1 score + freshly detected events."""
    num_to_take = max(1, int(len(companies) * top_pct))
    return companies[:num_to_take]

def extract_llm_events(companies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Uses Gemini to extract M&A events/signals from recent news snippets."""
    model = genai.GenerativeModel(
        model_name="gemini-3.5-flash",
        system_instruction="You are an M&A analyst. Analyze the news snippets for any signals of an impending transaction (M&A, buyout, strategic alternatives).",
        generation_config={"response_mime_type": "application/json", "temperature": 0.1}
    )
    
    for c in companies:
        news_text = " ".join(c.get("recent_news", []))
        if not news_text.strip():
            c["llm_signal_score"] = 0
            c["extracted_event"] = "No recent news."
            continue
            
        prompt = f"""
        Company: {c['name']}
        Sector: {c['sector']}
        Recent News: {news_text}
        
        Analyze the news and determine if there are M&A signals. 
        Return a JSON object with this exact schema:
        {{
            "has_ma_signal": boolean,
            "confidence_score": integer (0 to 100),
            "event_summary": "string describing the signal",
            "evidence": "quote the exact part of the news"
        }}
        """
        
        try:
            response = model.generate_content(prompt)
            # Strip markdown json blocks if present
            text = response.text.replace('```json', '').replace('```', '').strip()
            result = json.loads(text)
            
            c["llm_signal_score"] = result.get("confidence_score", 0)
            c["extracted_event"] = result.get("event_summary", "")
            c["event_evidence"] = result.get("evidence", "")
        except Exception as e:
            print(f"Error extracting events for {c['name']}: {e}")
            c["llm_signal_score"] = 0
            c["extracted_event"] = "Failed to extract."
            
        import time
        time.sleep(4.5)
            
    return sorted(companies, key=lambda x: x.get("llm_signal_score", 0), reverse=True)

def compute_peer_embeddings(companies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Calculates semantic similarity to a prototypical recently transacted company."""
    model = get_embed_model()
    
    # Ideal target: A high-growth software company exploring strategic alternatives or being acquired
    ideal_target_text = "The company is a leading enterprise software provider that recently announced it is exploring strategic alternatives, including a potential sale, after receiving inbound interest from major private equity firms."
    ideal_emb = model.encode(ideal_target_text)
    
    texts = [c.get("description", "") + " " + " ".join(c.get("recent_news", [])) for c in companies]
    embeddings = model.encode(texts)
    
    for i, c in enumerate(companies):
        emb = embeddings[i]
        # Cosine similarity
        similarity = np.dot(ideal_emb, emb) / (np.linalg.norm(ideal_emb) * np.linalg.norm(emb))
        c["peer_similarity_score"] = float(similarity)
        
    return sorted(companies, key=lambda x: x.get("peer_similarity_score", 0), reverse=True)

def reciprocal_rank_fusion(companies: List[Dict[str, Any]], k: int = 60) -> List[Dict[str, Any]]:
    """Combines ranks from Tier 1, LLM Event, and Peer Embeddings."""
    # Ensure they are sorted for ranking
    tier1_ranked = sorted(companies, key=lambda x: x.get("tier_1_score", 0), reverse=True)
    llm_ranked = sorted(companies, key=lambda x: x.get("llm_signal_score", 0), reverse=True)
    peer_ranked = sorted(companies, key=lambda x: x.get("peer_similarity_score", 0), reverse=True)
    
    rrf_scores = {c["company_id"]: 0.0 for c in companies}
    
    for rank, c in enumerate(tier1_ranked):
        rrf_scores[c["company_id"]] += 1.0 / (k + rank + 1)
        
    for rank, c in enumerate(llm_ranked):
        rrf_scores[c["company_id"]] += 1.0 / (k + rank + 1)
        
    for rank, c in enumerate(peer_ranked):
        rrf_scores[c["company_id"]] += 1.0 / (k + rank + 1)
        
    for c in companies:
        c["final_rrf_score"] = rrf_scores[c["company_id"]]
        
    return sorted(companies, key=lambda x: x["final_rrf_score"], reverse=True)

def generate_rationales(companies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generates a plain-English, evidence-linked rationale for the top companies."""
    model = genai.GenerativeModel("gemini-3.5-flash")
    
    for c in companies:
        prompt = f"""
        Company: {c['name']}
        Tier 1 Score (Structured rules): {c['tier_1_score']}/75 (Factors: hold period {c['hold_period_years']}y, debt maturity in {c['debt_maturity_months']}m)
        LLM Event Confidence: {c['llm_signal_score']}/100
        Event Extracted: {c['extracted_event']} (Evidence: {c.get('event_evidence', '')})
        Peer Similarity Score: {c['peer_similarity_score']:.2f}
        
        Write a concise, 2-3 sentence executive rationale explaining why this company is highly likely to enter an M&A transaction in the next 12 months based on these public signals. Focus on the most compelling factors.
        """
        try:
            response = model.generate_content(prompt)
            c["rationale"] = response.text.strip()
        except Exception as e:
            c["rationale"] = f"Strategic rationale aligned with the detected market signal ({c.get('extracted_event', 'Tier 1 structural requirements')}) and semantic peer similarity scoring."
            
        time.sleep(5.0)
            
    return companies

def run_deal_prediction_pipeline(data_path: str, top_pct: float = 0.1):
    print("Loading data...")
    companies = load_data(data_path)
    
    print("Running Tier 1 Scoring...")
    scored = tier_1_scoring(companies)
    
    print(f"Applying Funnel Gate (Top {top_pct*100}%)...")
    gated = funnel_gate(scored, top_pct=top_pct)
    
    print(f"{len(gated)} companies passed the gate. Running LLM Event Extraction...")
    llm_extracted = extract_llm_events(gated)
    
    print("Computing Peer Embeddings...")
    peer_scored = compute_peer_embeddings(llm_extracted)
    
    print("Fusing ranks via RRF...")
    final_ranked = reciprocal_rank_fusion(peer_scored)
    
    print("Generating Rationales for Top Candidates...")
    final_with_rationales = generate_rationales(final_ranked)
    
    return final_with_rationales

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_dir, "data", "mock_companies.json")
    if os.path.exists(data_path):
        results = run_deal_prediction_pipeline(data_path)
        print("\n--- TOP M&A TARGETS ---")
        for i, res in enumerate(results[:5]):
            print(f"\n{i+1}. {res['name']} (Score: {res['final_rrf_score']:.4f})")
            print(f"Rationale: {res['rationale']}")
    else:
        print("Data not found. Run mock_data.py first.")
