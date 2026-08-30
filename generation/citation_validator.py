import re

def validate_citations(generated_text, reranked_chunks):
    """
    Checks if every [article_id] or [comp_*] cited in the generated_text
    actually belongs to the reranked_chunks context provided to the LLM.
    Returns a tuple (is_valid: bool, hallucinated_ids: list).
    """
    valid_ids = set()
    for chunk in reranked_chunks:
        meta = chunk.get('metadata', {})
        for key in ('article_id', 'chunk_id', 'company_id', 'id'):
            val = meta.get(key)
            if val:
                valid_ids.add(str(val))
        # also accept partial prefix matches (first 12 chars of any id)
        for vid in list(valid_ids):
            valid_ids.add(vid[:12])

    # Match [uuid], [comp_hexhex], or any [word_word] citation pattern
    citations = re.findall(r'\[([a-zA-Z0-9_\-]{8,40})\]', generated_text)

    if not citations:
        return (True, [])

    invalid_citations = [c for c in citations if c not in valid_ids]
    is_valid = len(invalid_citations) == 0
    return (is_valid, invalid_citations)
