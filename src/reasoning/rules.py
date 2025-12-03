"""
Rules-based text generator for summarizer stage.
Adds basic analysis and a deterministic recommendation (Buy/Hold/Sell) based on metrics and events.
"""

def _build_recommendation(metrics, events):
    """
    Derive a deterministic recommendation:
    - Buy: positive momentum, low/moderate volatility, no critical events
    - Sell: negative momentum with critical/abnormal events
    - Hold: otherwise (including volatility spikes or mixed signals)
    """
    momentum = float(metrics.get("momentum") or 0.0)
    volatility = float(metrics.get("volatility") or 0.0)
    has_critical = any(e.get("severity") == "critical" for e in events)
    has_abnormal = any(e.get("type") == "abnormal_price_change" for e in events)
    if momentum > 0 and volatility < 2.0 and not has_critical and not has_abnormal:
        return "Buy", "Positive momentum with contained volatility and no critical events."
    if momentum < 0 and (has_critical or has_abnormal or volatility > 2.5):
        return "Sell", "Negative momentum combined with critical or abnormal signals."
    return "Hold", "Mixed or cautious signals; maintain position."


def generate_action(bundle):
    """
    Return a structured action dict with action and rationale based on metrics/events.
    """
    metrics = bundle.get("metrics", {}) or {}
    events = bundle.get("events", []) or []
    action, rationale = _build_recommendation(metrics, events)
    return {
        "action": action,
        "justification": rationale,
    }


def generate_text(bundle):
    metrics = bundle.get("metrics", {}) or {}
    events = bundle.get("events", []) or []
    news = bundle.get("news", []) or []
    sector = bundle.get("sector", None)
    market = bundle.get("market", None)
    company = bundle.get("company", None)
    financials = bundle.get("financials", None)
    strategies = bundle.get("strategies", []) or []

    # Header
    lines = ["Summary and Recommendation:"]

    # Metrics snapshot
    lines.append("Metrics: VWAP={vwap}, Volatility={vol}, Momentum={mom}, Liquidity={liq}".format(
        vwap=metrics.get("vwap"),
        vol=metrics.get("volatility"),
        mom=metrics.get("momentum"),
        liq=metrics.get("liquidity_ratio"),
    ))

    # Events
    if events:
        for event in events:
            lines.append("Event: {0} (Severity: {1})".format(
                event.get("type", "unknown"), event.get("severity", "n/a")))
    else:
        lines.append("Event: none detected.")

    # Context counts
    if news:
        lines.append("News: {0} items in window.".format(len(news)))
    if sector:
        lines.append("Sector context available.")
    if market:
        lines.append("Market context available.")
    if company:
        lines.append("Company: {0} ({1}) in {2}".format(
            company.get("name") or company.get("symbol"), company.get("symbol"), company.get("industry")))
    if financials:
        lines.append("Financials: beta={beta}, 52wH={h}, 52wL={l}".format(
            beta=financials.get("beta"),
            h=financials.get("high_52w"),
            l=financials.get("low_52w"),
        ))
    if strategies:
        lines.append("Applied strategies:")
        for strat in strategies:
            lines.append("- {name}: {desc}".format(
                name=strat.get("name", "strategy"),
                desc=strat.get("description", "").strip() or "No description"
            ))

    # Volatility narrative
    volatility = float(metrics.get("volatility") or 0.0)
    if volatility > 2.0:
        lines.append("Volatility assessment: elevated.")
    elif volatility > 0:
        lines.append("Volatility assessment: moderate.")
    else:
        lines.append("Volatility assessment: low.")

    # Momentum narrative
    momentum = float(metrics.get("momentum") or 0.0)
    if momentum > 0:
        lines.append("Momentum assessment: upward.")
    elif momentum < 0:
        lines.append("Momentum assessment: downward.")
    else:
        lines.append("Momentum assessment: neutral.")

    # Recommendation
    rec, rationale = _build_recommendation(metrics, events)
    lines.append("Recommendation: {0}".format(rec))
    lines.append("Rationale: {0}".format(rationale))

    return "\n".join(lines)
