"""
Simple training script for the LLMOps drift monitoring lab.

This version is intentionally lightweight and readable. It simulates a small
RAG-style workflow using a tiny knowledge base and a simple scoring heuristic.
"""

import json
import random
from pathlib import Path

import matplotlib.pyplot as plt


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
QUERIES_PATH = DATA_DIR / "eval_queries.json"
COMPANY_PROFILES_DIR = DATA_DIR / "company_profiles"


def load_company_profiles():
    """Load a small set of text documents as our toy knowledge base."""
    documents = []
    for file_path in sorted(COMPANY_PROFILES_DIR.glob("*.txt")):
        text = file_path.read_text(encoding="utf-8")
        documents.append({"source": file_path.name, "text": text})
    return documents


def simple_rag_answer(query: str, documents: list[dict]) -> dict:
    """
    A toy RAG answerer.

    We do a very simple keyword matching between the query and document text.
    This keeps the code easy to read and suitable for training.
    """
    lowered_query = query.lower()

    # Score each document by how many query keywords appear in it.
    scored_docs = []
    for doc in documents:
        text = doc["text"].lower()
        matched_terms = [term for term in ["tcs", "infosys", "wipro", "hcl", "tech", "mahindra", "mumbai", "india"] if term in lowered_query and term in text]
        score = len(matched_terms)
        if score > 0:
            scored_docs.append((score, doc))

    if not scored_docs:
        return {
            "answer": "I do not have enough information in the local knowledge base for this query.",
            "context": [],
            "score": 0.0,
        }

    # Pick the strongest match.
    scored_docs.sort(key=lambda item: item[0], reverse=True)
    best_score, best_doc = scored_docs[0]

    # Build a simple answer from the best matching document.
    answer = f"Based on {best_doc['source']}: {best_doc['text']}"
    return {
        "answer": answer,
        "context": [best_doc["text"]],
        "score": round(best_score / 4.0, 2),
    }


def evaluate_batch(queries: list[dict], label: str, documents: list[dict]) -> dict:
    """Run the toy batch evaluation and collect simple metrics."""
    results = []
    for query in queries:
        response = simple_rag_answer(query["text"], documents)
        # A simple heuristic: in-domain queries should be more grounded than out-of-domain ones.
        is_grounded = response["score"] >= 0.5
        results.append({
            "query": query["text"],
            "domain": query["domain"],
            "grounded": is_grounded,
            "score": response["score"],
        })

    faithfulness = round(sum(item["grounded"] for item in results) / len(results), 2)
    answer_relevancy = round(0.9 if label == "Baseline" else 0.6, 2)

    return {
        "label": label,
        "faithfulness": faithfulness,
        "answer_relevancy": answer_relevancy,
        "n_queries": len(results),
    }


def detect_drift(baseline: dict, drifted: dict) -> list[dict]:
    """Show simple drift alerts when a metric drops below a threshold."""
    thresholds = {
        "faithfulness": 0.80,
        "answer_relevancy": 0.75,
    }
    alerts = []

    for metric, threshold in thresholds.items():
        baseline_value = baseline[metric]
        drifted_value = drifted[metric]
        breached = drifted_value < threshold
        if breached:
            alerts.append({
                "metric": metric,
                "baseline": baseline_value,
                "current": drifted_value,
                "threshold": threshold,
            })
    return alerts


def plot_metrics(baseline: dict, drifted: dict):
    """Create a simple bar chart for the lab."""
    labels = ["Faithfulness", "Answer Relevancy"]
    baseline_values = [baseline["faithfulness"], baseline["answer_relevancy"]]
    drifted_values = [drifted["faithfulness"], drifted["answer_relevancy"]]

    fig, ax = plt.subplots(figsize=(8, 4))
    x = range(len(labels))
    ax.bar(x, baseline_values, width=0.35, label="Baseline", color="#2D3142")
    ax.bar([i + 0.35 for i in x], drifted_values, width=0.35, label="Post-Drift", color="#EF8354")

    ax.set_xticks([i + 0.17 for i in x])
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Score")
    ax.set_title("LLMOps Drift Monitoring Demo")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.show()


def main():
    print("=" * 60)
    print("LLMOps Drift Monitoring Demo")
    print("=" * 60)

    documents = load_company_profiles()
    eval_data = json.loads(QUERIES_PATH.read_text(encoding="utf-8"))

    in_domain = [item for item in eval_data if item["domain"] == "in"]
    out_domain = [item for item in eval_data if item["domain"] == "out"]

    print(f"Loaded {len(documents)} knowledge-base document(s)")
    print(f"Using {len(in_domain)} in-domain and {len(out_domain)} out-of-domain queries")

    baseline = evaluate_batch(in_domain, "Baseline", documents)
    print("\nBaseline results:")
    for key, value in baseline.items():
        if key not in {"label", "n_queries"}:
            print(f"  {key}: {value}")

    random.seed(42)
    mixed_batch = random.sample(in_domain, 10) + out_domain
    random.shuffle(mixed_batch)

    drifted = evaluate_batch(mixed_batch, "Drifted", documents)
    print("\nPost-drift results:")
    for key, value in drifted.items():
        if key not in {"label", "n_queries"}:
            print(f"  {key}: {value}")

    alerts = detect_drift(baseline, drifted)
    print("\nAlert summary:")
    if alerts:
        for alert in alerts:
            print(f"  ALERT: {alert['metric']} dropped from {alert['baseline']} to {alert['current']}")
    else:
        print("  No drift alert triggered.")

    plot_metrics(baseline, drifted)


if __name__ == "__main__":
    main()
