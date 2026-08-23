import os
import chromadb

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROMA_DB_DIR = os.path.join(BASE_DIR, "data", "chroma_db")


def get_chroma_client():
    os.makedirs(CHROMA_DB_DIR, exist_ok=True)
    return chromadb.PersistentClient(path=CHROMA_DB_DIR)


def get_collection():
    client = get_chroma_client()
    # Generic collection name — not tied to any single website
    return client.get_or_create_collection(name="universal_articles")


def add_to_chroma(ids, embeddings, metadatas, documents):
    collection = get_collection()

    batch_size = 5000
    for i in range(0, len(ids), batch_size):
        print(f"Adding batch {i} to {i + batch_size} to ChromaDB...")
        collection.upsert(
            ids=ids[i:i + batch_size],
            embeddings=embeddings[i:i + batch_size],
            metadatas=metadatas[i:i + batch_size],
            documents=documents[i:i + batch_size]
        )
    print("Successfully added all chunks to ChromaDB.")
