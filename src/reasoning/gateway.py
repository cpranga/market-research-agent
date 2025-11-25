"""
Stub gateway for summarizer. Routes to rules.generate_text for MVP.
"""
from reasoning.rules import generate_text

def summarize(bundle):
    return generate_text(bundle)
