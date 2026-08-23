import re

def validate_citations(generated_text, reranked_chunks):
    """
    Checks if every [article_id] cited in the generated_text actually belongs to the 
    reranked_chunks context provided to the LLM.
    """
    valid_ids = {str(chunk['metadata'].get('article_id')) for chunk in reranked_chunks}
    
    # Find all strings matching UUIDs inside brackets
    citations = re.findall(r'\[([a-fA-F0-9\-]{36})\]', generated_text)
    
    if not citations:
        return {
            "has_citations": False,
            "all_valid": False,
            "invalid_citations": [],
            "message": "No valid UUID citations found in the text."
        }
        
    invalid_citations = [cite for cite in citations if cite not in valid_ids]
    
    return {
        "has_citations": True,
        "all_valid": len(invalid_citations) == 0,
        "invalid_citations": invalid_citations,
        "total_citations": len(citations),
        "message": f"Found {len(citations)} citations. {len(invalid_citations)} are invalid/hallucinated."
    }
