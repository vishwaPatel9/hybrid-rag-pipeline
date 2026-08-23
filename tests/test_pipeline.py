import pytest
import pandas as pd
import numpy as np
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from processing.advanced_cleaner import advanced_clean_pipeline

def test_cleaner_handles_missing_required_cols():
    # Missing 'body'
    df = pd.DataFrame({"url": ["http://test.com"]})
    with pytest.raises(ValueError, match="CRITICAL: Missing required column body"):
        advanced_clean_pipeline(df)

def test_cleaner_imputes_missing_values():
    df = pd.DataFrame({
        "url": ["http://test.com"],
        "body": ["This is a valid long enough body to bypass the length filter. " * 5],
        "date": [np.nan]  # missing author, missing title
    })
    
    cleaned = advanced_clean_pipeline(df)
    
    # Assert defaults were applied
    assert cleaned.iloc[0]['author'] == "Unknown Analyst"
    assert cleaned.iloc[0]['title'] == "Untitled Document"
    assert pd.isna(cleaned.iloc[0]['date'])

def test_cleaner_text_normalization():
    messy_text = "   This   has\n\n\nweird   spacing \u200band unicode.  " * 5
    df = pd.DataFrame({
        "url": ["http://test.com"],
        "body": [messy_text]
    })
    
    cleaned = advanced_clean_pipeline(df)
    
    # Assert whitespace normalized and unicode stripped
    assert "  " not in cleaned.iloc[0]['body']
    assert "\u200b" not in cleaned.iloc[0]['body']
