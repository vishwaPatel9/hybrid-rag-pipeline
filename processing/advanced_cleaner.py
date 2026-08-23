import pandas as pd
import numpy as np
import os
import re

def advanced_clean_pipeline(df: pd.DataFrame) -> pd.DataFrame:
    """
    Advanced Pandas cleaning pipeline designed for messy, real-world scraped data.
    Demonstrates handling of edge cases, data imputation, and strict schemas.
    """
    if df.empty:
        return df

    # 1. Structural Validation
    required_cols = ['url', 'body']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"CRITICAL: Missing required column {col}")

    # 2. Strict Deduplication
    initial_count = len(df)
    df = df.drop_duplicates(subset=['url'], keep='last')
    
    # 3. Missing Value Imputation
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
    else:
        df['date'] = pd.NaT

    if 'author' in df.columns:
        df['author'] = df['author'].fillna("Unknown Analyst")
    else:
        df['author'] = "Unknown Analyst"

    if 'title' in df.columns:
        df['title'] = df['title'].fillna("Untitled Document")
    else:
        df['title'] = "Untitled Document"

    # 4. Text Normalization (The core complexity)
    df = df.dropna(subset=['body'])
    
    def clean_text(text):
        if not isinstance(text, str):
            return ""
        # Remove massive whitespace gaps
        text = re.sub(r'\s+', ' ', text)
        # Strip invisible unicode characters
        text = text.replace('\u200b', '').replace('\u200e', '')
        return text.strip()

    df['body'] = df['body'].apply(clean_text)
    
    # Filter out statistically meaningless documents
    df = df[df['body'].str.len() > 100]

    # 5. Schema Enforcement
    columns_order = [
        'article_id', 'title', 'author', 'date',
        'body', 'url', 'source_domain'
    ]
    
    for col in columns_order:
        if col not in df.columns:
            df[col] = np.nan
            
    df = df[columns_order]
    
    final_count = len(df)
    print(f"Data Quality Report: Started with {initial_count} records, dropped {initial_count - final_count} anomalous records.")
    return df

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_json = os.path.join(base_dir, "ingestion", "raw_articles.json")
    output_parquet = os.path.join(base_dir, "processing", "cleaned_articles.parquet")
    
    if os.path.exists(input_json):
        df_raw = pd.read_json(input_json)
        df_clean = advanced_clean_pipeline(df_raw)
        df_clean.to_parquet(output_parquet, index=False)
        print(f"Advanced cleaned dataset saved to {output_parquet}")
    else:
        print("Raw JSON not found.")
