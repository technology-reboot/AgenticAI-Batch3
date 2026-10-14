import json
import os
import time
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent   
DATA_DIR = PROJECT_ROOT / "data"

def load_environments() -> Optional[str]:
    load_dotenv(PROJECT_ROOT / ".env")
    return os.getenv("OPENAI_API_KEY")

def get_client():
    api_key = load_environments()
    if not api_key:
        return None

    from openai import OpenAI
    return OpenAI(api_key = api_key)

def load_reviews() -> list[dict[str, Any]]:
    reviews_path = DATA_DIR / "product_reviews.json"
    return json.loads(reviews_path.read_text(encoding="utf-8"))