"""
Rules-based text generator for summarizer stage.
"""

def generate_text(bundle):
    # Deterministic summary based on metrics/events
    metrics = bundle.get("metrics", {})
    events = bundle.get("events", [])
    summary = []
    if metrics.get("volatility") and metrics["volatility"] > 2.0:
        summary.append("Market showed elevated volatility.")
    if metrics.get("momentum") and metrics["momentum"] > 0:
        summary.append("Momentum trended upward.")
    for event in events:
        summary.append("Event: {} ({}).".format(event.get("type"), event.get("severity", "n/a")))
    if not summary:
        summary.append("No significant activity detected.")
    return " ".join(summary)
