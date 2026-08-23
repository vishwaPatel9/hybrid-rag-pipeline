import os
import pandas as pd


def clean_data(input_file, output_file):
    print(f"Loading raw data from {input_file}...")
    try:
        df = pd.read_json(input_file)
    except ValueError:
        print("Raw JSON not found or invalid.")
        return

    print(f"Initial shape: {df.shape}")

    # 1. Drop articles with missing body
    df = df.dropna(subset=['body'])
    df = df[df['body'].str.strip() != ""]

    # 2. Dedup by URL
    df = df.drop_duplicates(subset=['url'])

    # 3. Normalize whitespace in body
    df['body'] = df['body'].apply(lambda x: ' '.join(str(x).split()))

    # 4. Standardize dates
    df['date'] = pd.to_datetime(df['date'], errors='coerce')

    # 5. Force strict schema order (generic, no language-specific columns)
    columns_order = [
        'article_id', 'title', 'author', 'date',
        'body', 'url', 'source_domain', 'image_path'
    ]

    for col in columns_order:
        if col not in df.columns:
            df[col] = None

    df = df[columns_order]

    print(f"Cleaned shape: {df.shape}")

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    df.to_parquet(output_file, index=False)
    print(f"Saved cleaned dataset to {output_file}")


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_json = os.path.join(base_dir, "ingestion", "raw_articles.json")
    output_parquet = os.path.join(base_dir, "processing", "cleaned_articles.parquet")
    clean_data(input_json, output_parquet)
