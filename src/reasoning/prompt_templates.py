"""
Prompt templates for summarizer stage.
"""

def build_prompt(bundle):
    # Simple template for MVP
    metrics = bundle.get("metrics", {})
    events = bundle.get("events", [])
    lines = []
    lines.append("Summary for window {} to {}:".format(bundle["window_start"], bundle["window_end"]))
    volatility = metrics.get("volatility", 0) or 0
    momentum = metrics.get("momentum", 0) or 0
    if float(volatility) > 2.0:
        lines.append("- Market showed elevated volatility.")
    if float(momentum) > 0:
        lines.append("- Momentum trended upward.")
    if events:
        for event in events:
            lines.append("- Event: {} ({}).".format(event.get("type"), event.get("severity", "n/a")))
    if not lines:
        lines.append("- No significant activity detected.")
    return "\n".join(lines)
