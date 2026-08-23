import os
import json
import google.generativeai as genai
from itertools import combinations
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# Gemini 1.5 Flash supports a native JSON mode via response_mime_type, making this extremely robust
model = genai.GenerativeModel(
    model_name="gemini-3.5-flash",
    system_instruction="You are a strict JSON-outputting contradiction detector. Evaluate excerpts for contradictions and output valid JSON.",
    generation_config={"response_mime_type": "application/json", "temperature": 0.0}
)

def detect_contradictions(query, reranked_chunks):
    # Get unique chunks by article
    chunks_by_article = {}
    for c in reranked_chunks:
        aid = c['metadata'].get('article_id')
        if aid not in chunks_by_article:
            chunks_by_article[aid] = c

    unique_chunks = list(chunks_by_article.values())
    
    # We only need to check the top 4 distinct articles to stay well within token limits and keep it fast
    unique_chunks = unique_chunks[:4]
    
    if len(unique_chunks) < 2:
        return []

    print(f"Checking {len(unique_chunks)} distinct sources for contradictions in a single API call...")

    # Build a single prompt containing all excerpts
    excerpts_text = ""
    for i, c in enumerate(unique_chunks):
        author = c['metadata'].get('author', 'Unknown')
        source = c['metadata'].get('source_domain', 'Unknown')
        excerpts_text += f"\n--- Excerpt {i+1} ---\nAuthor: {author}\nSource: {source}\nText: {c['text']}\n"

    prompt = f"""You are analyzing multiple excerpts from different web sources on the topic: "{query}".

Here are the excerpts:
{excerpts_text}

Analyze these excerpts and identify if there are any fundamental disagreements or contradictions between any two specific excerpts.
Reply with ONLY a valid JSON array of objects matching this exact schema:
[
  {{
    "author_1": "Name of first author",
    "source_1": "Name of first source",
    "author_2": "Name of conflicting author",
    "source_2": "Name of conflicting source",
    "explanation": "Brief 1-sentence explanation of the specific disagreement."
  }}
]
If there are no contradictions, return an empty array: []
"""

    try:
        response = model.generate_content(prompt)
        result = json.loads(response.text)
        return result
    except Exception as e:
        print(f"Error detecting contradiction: {e}")
        return []

