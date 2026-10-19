"""
Training-friendly debugging lab for the broken-agent evaluation exercise.

This script includes:
- a deliberately broken agent with four simple failure modes
- a small evaluation set
- a fixed agent implementation that students can compare against
"""

import json
import re
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
EVAL_PATH = DATA_DIR / "broken_agent_eval_set.json"
ATTACKS_PATH = DATA_DIR / "red_team_attacks.json"

ORDERS = {
    "ORD-1234": {"status": "SHIPPED", "items": ["Laptop Stand"], "ship_date": "2024-04-10"},
    "ORD-5678": {"status": "PROCESSING", "items": ["USB Hub"], "ship_date": None},
}

POLICIES = {
    "return_policy": "Products can be returned within 30 days of purchase with receipt.",
    "refund_policy": "Refunds are processed within 7-10 business days after return receipt.",
}


def broken_get_order_details(order_id: str) -> dict:
    """Simple order lookup that may hallucinate if the order ID is missing."""
    if not order_id:
        return {"error": "No order id was provided."}
    order = ORDERS.get(order_id)
    if order:
        return {"order_id": order_id, **order}
    return {"error": f"Order {order_id} not found"}


def broken_agent_respond(query: str, conversation_history: list[dict], max_iterations: int = 5) -> dict:
    """Broken agent: contains 4 training bugs."""
    # Bug 1: it may infer a delivery date from generic assumptions.
    if "delivery date" in query.lower() and "ord-" in query.lower():
        order_id = re.search(r"ord-\d+", query.lower())
        if order_id:
            order_info = broken_get_order_details(order_id.group(0).upper())
            if order_info.get("ship_date"):
                return {"answer": f"The expected delivery date is {order_info['ship_date']}.", "iterations": 1}
            return {"answer": "The delivery date is estimated to be 3-5 business days after shipment.", "iterations": 1}

    # Bug 2: policy queries may loop because the retrieval threshold is too strict.
    if "return" in query.lower() or "policy" in query.lower():
        return {"answer": "I am still checking the return policy. Please wait.", "iterations": 5}

    # Bug 3: if no order ID is present, the agent may fabricate one.
    if "order" in query.lower():
        return {"answer": "I found order ORD-9999 in your history and will use that.", "iterations": 1}

    # Bug 4: context is not managed well, so a prior order reference is lost.
    if "10 turns ago" in query.lower():
        return {"answer": "I do not have the earlier context in this conversation.", "iterations": 1}

    return {"answer": "I can help with that general support question.", "iterations": 1}


def fixed_agent_respond(query: str, conversation_history: list[dict], entity_store: dict | None = None, max_iterations: int = 5) -> dict:
    """Fixed agent implementing the four bug fixes in a simple way."""
    entity_store = entity_store or {}

    # Bug 1 fix: stop inferring dates and report when unavailable.
    if "delivery date" in query.lower() and "ord-" in query.lower():
        match = re.search(r"ord-\d+", query.lower())
        if match:
            order_id = match.group(0).upper()
            order_info = broken_get_order_details(order_id)
            if order_info.get("ship_date"):
                return {"answer": f"The delivery date for {order_id} is {order_info['ship_date']}.", "iterations": 1}
            return {"answer": "The delivery date is not yet available.", "iterations": 1}

    # Bug 2 fix: avoid loops and provide a fallback answer.
    if "return" in query.lower() or "policy" in query.lower():
        return {"answer": "The return policy allows returns within 30 days of purchase with a receipt.", "iterations": 1}

    # Bug 3 fix: validate the order ID format instead of hallucinating.
    if "order" in query.lower():
        match = re.search(r"ord-\d+", query.lower())
        if match:
            order_id = match.group(0).upper()
            return {"answer": f"I can look up {order_id} if you provide it explicitly.", "iterations": 1}
        return {"answer": "Could you please provide your order ID in the format ORD-XXXX?", "iterations": 1}

    # Bug 4 fix: preserve context from the entity store.
    if "10 turns ago" in query.lower():
        if entity_store.get("order_id"):
            return {"answer": f"I remember the earlier order {entity_store['order_id']}.", "iterations": 1}
        return {"answer": "I do not have the earlier context in this conversation.", "iterations": 1}

    return {"answer": "I can help with that general support question.", "iterations": 1}


def run_eval_suite():
    """Run the broken agent against the evaluation set."""
    eval_set = json.loads(EVAL_PATH.read_text(encoding="utf-8"))
    print("Running broken agent evaluation...")
    for case in eval_set:
        result = broken_agent_respond(case["query"], conversation_history=[])
        print(f"{case['id']}. {case['query']} -> {result['answer']}")


def run_red_team_suite():
    """Run the fixed agent against a small set of attack prompts."""
    attacks = json.loads(ATTACKS_PATH.read_text(encoding="utf-8"))
    print("\nRunning fixed agent red-team check...")
    for attack in attacks:
        result = fixed_agent_respond(attack["prompt"], conversation_history=[])
        print(f"{attack['id']}. {attack['prompt']} -> {result['answer']}")


def main():
    print("=" * 60)
    print("Broken Agent Debugging Lab")
    print("=" * 60)
    run_eval_suite()
    run_red_team_suite()


if __name__ == "__main__":
    main()
