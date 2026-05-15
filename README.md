# Solana Market Pulse

Live SPL token intelligence dashboard for the Solana ecosystem.

**Live demo:** https://atlasnexusops.github.io/solana-pulse/

Solana Market Pulse consolidates the useful parts of the former `crypto-dashboard` prototype into a stronger Atlas Nexus Solana dashboard: static GitHub Pages hosting, generated JSON/CSV/HTML outputs, Jupiter/CoinGecko market data notes, and a cleaner README for portfolio review.

## What it does

- Tracks SPL tokens across Solana ecosystem categories.
- Produces a static dashboard with no visitor-side backend.
- Generates JSON, CSV and HTML snapshots under `output/`.
- Combines token price movement, relative strength, volume and risk signals.
- Presents a compact Market Pulse scanner for manual review workflows.

## Features

- **SPL token coverage** across L1, DeFi, meme, LST, AI, gaming and DePIN categories.
- **Market Pulse Scanner v2** with 5 scoring components: trend, momentum, relative strength, volume and risk.
- **7/7/7 classification**: top momentum, breakout watch and risk flags.
- **Public data sources**: CoinGecko plus Jupiter-oriented token intelligence patterns inherited from the earlier crypto-dashboard prototype.
- **Static deployment**: pure HTML/CSS/JS output on GitHub Pages.
- **Automation-ready**: the pipeline can be refreshed by cron and committed back to GitHub.

## Data sources

The current Solana Pulse pipeline is centered on CoinGecko market data and keeps the earlier `crypto-dashboard` design notes for Jupiter integration:

- Jupiter Price API patterns for live Solana token prices;
- Jupiter Tokens API patterns for metadata, verification and organic-score enrichment;
- CoinGecko market data for broad token coverage and historical fields.

The dashboard should be treated as an informational market-intelligence surface, not as an execution system.

## Scoring model

```text
Score = Trend(25) + Momentum(25) + Relative Strength(20) + Volume(15) + Risk(15)
```

- **Trend** — price/EMA and multi-timeframe alignment when available.
- **Momentum** — percentile-based rate-of-change ranking inside the Solana set.
- **Relative Strength** — token behavior versus category or ecosystem median.
- **Volume** — participation proxy versus ecosystem average.
- **Risk** — volatility, drawdown and market-cap stability checks.

## Repository structure

```text
.
├── index.html              # Live static dashboard
├── solana_pipeline.py      # Data fetch, scoring and HTML generation
└── output/                 # Generated JSON/CSV/HTML snapshots
```

## Run locally

```bash
python3 solana_pipeline.py
python3 -m http.server 8000
```

Open:

```text
http://localhost:8000/
```

## Refresh workflow

A refresh typically runs:

```bash
python3 solana_pipeline.py
git add index.html output/
git commit -m "data: refresh solana pulse YYYYMMDD-HHMMSS"
git push origin main
```

For scheduled refreshes, use a lock and a clean checkout so overlapping cron jobs do not create duplicate or stale output artifacts.

## Atlas Nexus context

This repository is part of the Atlas Nexus public portfolio. It demonstrates:

- static market dashboards;
- generated data artifacts;
- crypto/Solana data ingestion;
- lightweight scoring models;
- GitHub Pages publishing.

Main Atlas Nexus site:

https://atlasnexusops.github.io/

## Superseded source

The older `crypto-dashboard` repository has been consolidated here. Its useful README concepts — Jupiter API references, zero-backend static dashboard model, JSON data artifact and automation notes — are preserved in this Solana Pulse README.

## Disclaimer

This project is for technical demonstration and market-monitoring research only. Market data can be delayed, incomplete or inaccurate. Nothing here is financial advice or an execution recommendation.
