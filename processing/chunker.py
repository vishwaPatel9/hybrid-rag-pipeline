import os
import pandas as pd


def chunk_text(text, chunk_size=300, overlap=50):
    words = str(text).split()
    chunks = []
    i = 0
    while i < len(words):
        chunk_words = words[i:i + chunk_size]
        chunks.append(" ".join(chunk_words))
        i += chunk_size - overlap
    return chunks


def process_chunks(parquet_file, output_file):
    print(f"Loading {parquet_file}...")
    df = pd.read_parquet(parquet_file)

    all_chunks = []
    for _, row in df.iterrows():
        body = row['body']
        if not body:
            continue

        chunks = chunk_text(body, chunk_size=300, overlap=50)
        for i, chunk in enumerate(chunks):
            all_chunks.append({
                "chunk_id": f"{row['article_id']}_chunk_{i}",
                "article_id": row['article_id'],
                "title": row['title'],
                "author": row['author'],
                "date": str(row['date']),
                "url": row['url'],
                "source_domain": row.get('source_domain', ''),
                "text": chunk
            })

    chunk_df = pd.DataFrame(all_chunks)
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    chunk_df.to_parquet(output_file, index=False)
    print(f"Created {len(chunk_df)} chunks from {len(df)} articles.")
    print(f"Saved chunks to {output_file}")


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_parquet = os.path.join(base_dir, "processing", "cleaned_articles.parquet")
    output_parquet = os.path.join(base_dir, "processing", "chunked_articles.parquet")
    process_chunks(input_parquet, output_parquet)
