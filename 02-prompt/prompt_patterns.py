import json
import time
from typing import Any

from common import get_client, load_reviews

MODEL = "gpt-4o-mini"

def build_prompt(text: str, prompt_type: str) -> str:
    if prompt_type == "zero_shot":
        instructions = "Classify the review as POSITIVE, NEGATIVE or NEUTRAL"
    elif prompt_type == "few_shot":
        instructions = (
            "Use these examples: 'I love this product' = POSITIVE;"
            "'It arrived broken' = NEGATIVE; 'It is an ordinary product' = NEUTRAL"
            "Now classify the review as POSITIVE, NEGATIVE OR NEUTRAL"                
        )    
    else:
        instructions = (
            "Classify the review as POSITIVE, NEGATIVE OR NEUTRAL"
            "Briefly explain the working that led to the classification,"
            "including any sarcasm or irony"
        )

    print(f"instructions: {instructions}")
    
    return (
      
        f"{instructions}\n\nReview: {text}\n\n"
        'Return only JSON with this shape: {"label": "...", "reasoning": "..."}'
    )

def classify_sentiment(text: str, prompt_type: str, client: Any = None) -> dict[str, Any]:
    started = time.perf_counter()
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role" : "system", "content" :  "You clasify product reviews accurately"},
            {"role" : "user", "content" :  build_prompt(text, prompt_type)}
        ],
        temperature=0,
        response_format={"type" : "json_object"},
        max_tokens=120
    )

    content = response.choices[0].message.content or "{}"
    result = json.loads(content)
    label = str(result.get("label", "NEUTRAl")).upper()
    if label not in {"POSITIVE", "NEGATIVE" , "NEUTRAL"}:
        raise ValueError(f"Unexpected Sentinement label")

    return{
        "label" : label,
        "reasoning" : str(result.get("reasoning", "")),
        "latency_ms" : (time.perf_counter() -started) *1000
    }

def run_lab():
    reviews = load_reviews()
    client = get_client()
    results: list[dict[str, Any]] = []

    print("=== Lab : Prompt pattern comparison")

    for review in reviews:
        row = {
            "id" : review["id"],
            "text" : review["text"],
            "ground_truth" : review["label"]
        }

        for pattern in ["zero_shot", "few_shot", "cot"]:
            result = classify_sentiment(review["text"], pattern, client) 
            row[f"{pattern}_label"] = result["label"] 
            row[f"{pattern}_latency_ms"] = result["latency_ms"]
            if pattern == "cot":
                row["cot_reasoning"] = result.get("reasoning", "")
        
        results.append(row)  
    
    print(f"Classified {len(results)} reviews across 3 prompt patterns")          

    for pattern in ["zero_shot", "few_shot", "cot"]:
        col = f"{pattern}_label"            
        acc = sum(1 for row in results if row[col]== row["ground_truth"])/ len(results) 
        avg_lat = sum(row[f"{pattern}_latency_ms"] for row in results) / len(results)
        print(f"{pattern.upper():>12}: Accuracy={acc:.0%} | Avg Latency={avg_lat:.0f} ms")

print("\n --- Where patterns disagree ---")


              
 
if __name__ == "__main__":
    run_lab()