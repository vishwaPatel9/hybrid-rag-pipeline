import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

system_prompt = """You are a Senior Investment Research Analyst at Third Bridge.
You provide precise, executive-level briefings based on the retrieved intelligence provided, seamlessly supplemented by your own vast expert knowledge.
Your audience consists of institutional investors and private equity partners who have zero tolerance for fluff, generic AI filler, or hallucinatory claims.

CRITICAL RULES:
1. No AI pleasantries (e.g., "Based on the provided documents...", "Here is the information..."). Dive straight into the facts immediately.
2. Be extremely precise. Use bullet points for readability. Highlight key metrics, strategic shifts, and expert perspectives.
3. You MUST cite your sources inline using the exact [Article ID] provided, but ONLY when referencing facts from the provided context. 
4. If the provided context is insufficient to fully answer the query, seamlessly fallback to your own vast general knowledge. Do NOT mention the lack of context. Just deliver the answer with executive precision.
"""

# We use Gemini 1.5 Flash which is insanely fast, free, and great at RAG
model = genai.GenerativeModel(
    model_name="gemini-3.5-flash",
    system_instruction=system_prompt
)

def generate_answer(query, reranked_chunks):

    context_text = ""
    for i, chunk in enumerate(reranked_chunks):
        article_id = chunk['metadata'].get('article_id', 'Unknown')
        author = chunk['metadata'].get('author', 'Unknown')
        title = chunk['metadata'].get('title', 'Unknown')
        source = chunk['metadata'].get('source_domain', 'Unknown')

        context_text += f"\n--- Excerpt {i + 1} ---\n"
        context_text += f"Article ID: [{article_id}]\n"
        context_text += f"Source: {source}\n"
        context_text += f"Author: {author}\n"
        context_text += f"Title: {title}\n"
        context_text += f"Text:\n{chunk['text']}\n"

    user_prompt = f"""User Query: {query}

Here are the retrieved excerpts from various web sources:
{context_text}

Please provide a thorough, well-structured answer with strict inline citations using [Article ID]."""

    print("Sending prompt to Gemini 1.5 Flash...")

    try:
        response = model.generate_content(
            user_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.2,
            )
        )
        return response.text
    except Exception as e:
        return f"**API Quota Exceeded.** Please wait 60 seconds for the free tier limit to reset, then try again.\n\n*(Error: {str(e)[:100]}...)*"
