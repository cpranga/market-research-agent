"""
Prompt templates for summarizer stage.
"""

def build_prompt(bundle):
    metrics = bundle.get("metrics", {})
    events = bundle.get("events", [])
    news = bundle.get("news", [])
    sector = bundle.get("sector", None)
    market = bundle.get("market", None)
    window_start = bundle.get("window_start")
    window_end = bundle.get("window_end")
    lines = []
    lines.append("Summary for window {0} to {1}:".format(window_start, window_end))
    volatility = metrics.get("volatility", 0) or 0
    momentum = metrics.get("momentum", 0) or 0
    if float(volatility) > 2.0:
        lines.append("- Market showed elevated volatility.")
    elif float(volatility) > 0:
        lines.append("- Volatility was moderate.")
    else:
        lines.append("- Volatility was low.")

    if float(momentum) > 0:
        lines.append("- Momentum trended upward.")
    elif float(momentum) < 0:
        lines.append("- Momentum trended downward.")
    else:
        lines.append("- Momentum was neutral.")

    if events:
        for event in events:
            event_type = event.get("type", "unknown")
            severity = event.get("severity", "n/a")
            lines.append("- Event: {0} (Severity: {1})".format(event_type, severity))
    else:
        lines.append("- No major events detected.")

    if news:
        lines.append("- News count: {0}".format(len(news)))
    if sector:
        lines.append("- Sector context included.")
    if market:
        lines.append("- Market context included.")

    return "\n".join(lines)


def build_action_prompt(bundle):
    """
    Build a concise, instruction-following prompt to request a structured action decision.
    The model must return JSON: {"action":"Buy|Hold|Sell","justification":"...","confidence":0-1}
    """
    metrics = bundle.get("metrics", {}) or {}
    events = bundle.get("events", []) or []
    news = bundle.get("news", []) or []
    strategies = bundle.get("strategies", []) or []
    company = bundle.get("company", {}) or {}
    financials = bundle.get("financials", {}) or {}
    window_start = bundle.get("window_start")
    window_end = bundle.get("window_end")
    symbol = bundle.get("symbol")

    lines = []
    lines.append("You are an investment assistant. Decide Buy/Hold/Sell for {sym}.".format(sym=symbol))
    lines.append("Window: {0} to {1}".format(window_start, window_end))
    lines.append("Metrics: vwap={vwap}, vol={vol}, mom={mom}, liq={liq}".format(
        vwap=metrics.get("vwap"), vol=metrics.get("volatility"),
        mom=metrics.get("momentum"), liq=metrics.get("liquidity_ratio")
    ))
    if events:
        lines.append("Events:")
        for e in events:
            lines.append("- {t} (severity={s})".format(t=e.get("type"), s=e.get("severity")))
    if news:
        lines.append("News items in window: {0}".format(len(news)))
    if company:
        lines.append("Company: {name} ({sym}), industry={ind}, market_cap={mc}".format(
            name=company.get("name") or symbol,
            sym=symbol,
            ind=company.get("industry"),
            mc=company.get("market_cap"),
        ))
    if financials:
        lines.append("Financials: beta={beta}, 52wH={h}, 52wL={l}".format(
            beta=financials.get("beta"),
            h=financials.get("high_52w"),
            l=financials.get("low_52w"),
        ))
    if strategies:
        lines.append("User strategies:")
        for strat in strategies:
            lines.append("- {name}: {desc}".format(
                name=strat.get("name", "strategy"),
                desc=strat.get("description", "") or strat.get("rules", "") or "n/a"
            ))
    lines.append("Respond ONLY with JSON: {\"action\":\"Buy|Hold|Sell\",\"justification\":\"...\",\"confidence\":0.0-1.0}")
    return "\n".join(lines)
