# Market Analysis / Trading Research Agent

*A modular, autonomous system for market-data analysis, reasoning, and summarization.*

---

## 📘 Overview

This project implements a **self-governing market research agent** that:

- Ingests and stores raw market and contextual data (e.g., news, indices)
- Computes analytics (VWAP, volatility, momentum, etc.)
- Generates reasoned natural-language summaries
- Operates autonomously with idempotency and resilience

Observe → Analyze → Reason → Record → Learn

---

## 🧩 Core Components

| Component | Purpose |
|------------|----------|
| **Fetcher** | Collects market ticks or bars |
| **Preprocessor** | Cleans and normalizes incoming data |
| **Analytics Engine** | Computes metrics and detects events |
| **Reasoner** | Summarizes insights using LLMs or rules |
| **Storage Layer** | Persists structured data in PostgreSQL |
| **Coordinator** | Schedules, monitors, and recovers processes |

---

## 🧱 Project Structure

market_agent/  
├── config/           # Settings, logging, prompt templates  
├── data/             # Fixtures, migrations, schemas  
├── market_agent/     # Core source code (ingest, analytics, reasoner)  
├── scripts/          # Utility and maintenance scripts  
├── tests/            # Pytest-based tests  
└── docs/             # Architecture and operations documentation  

---

## ⚙️ Getting Started

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- `pip install -r requirements.txt`

### Setup
git clone https://github.com/cpranga/market-research-agent.git  
cd market-research-agent  
python -m venv venv  
source venv/bin/activate  
pip install -r requirements.txt  
cp .env.example .env  

### Run
python -m market_agent.main  

---

## 🧠 Tech Stack

- **Python** - Core logic and orchestration  
- **PostgreSQL** - Persistent storage and queue backend  
- **pandas / numpy** - Analytics computation  
- **asyncio / APScheduler** - Scheduling  
- **FastAPI** - Read-only API  
- **LLM Integration** - OpenAI / Anthropic / local vLLM  

---

## 🧪 Development

pytest -v  
black .  
isort .  

---

## 📜 License

MIT License © 2025

---

## 💬 Acknowledgments

Design inspired by high-reliability trading data systems and autonomous agent architectures.
