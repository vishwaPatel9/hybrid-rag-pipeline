import os
import pandas as pd
from sentence_transformers import SentenceTransformer
from indexing.vector_store import add_to_chroma


def embed_and_store(chunked_file):
    print(f"Loading chunks from {chunked_file}...")
    df = pd.read_parquet(chunked_file)

    print("Loading multilingual embedding model...")
    # Multilingual model: works on any language (Spanish, English, French, etc.)
    model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

    texts = df['text'].tolist()
    print(f"Embedding {len(texts)} chunks...")
    embeddings = model.encode(texts, show_progress_bar=True)

    # Build metadata for filtering and citations (includes source_domain)
    metadatas = []
    for _, row in df.iterrows():
        metadatas.append({
            "article_id": str(row['article_id']),
            "title": str(row['title']),
            "author": str(row['author']),
            "url": str(row['url']),
            "source_domain": str(row.get('source_domain', ''))
        })

    ids = df['chunk_id'].tolist()
    add_to_chroma(ids, embeddings.tolist(), metadatas, texts)


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    chunked_file = os.path.join(base_dir, "processing", "chunked_articles.parquet")
    embed_and_store(chunked_file)
