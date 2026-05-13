# 🪙 Solana Market Pulse

Live SPL token intelligence dashboard for the Solana ecosystem.
Built for the Superteam Agentic Engineering Grant.

**Live**: https://atlasnexusops.github.io/solana-pulse/

## Features
- **27 SPL tokens** tracked across 7 categories (L1, DeFi, Meme, LST, AI, Gaming, DePIN)
- **Market Pulse Scanner v2**: 5-component scoring (Trend, Momentum, Relative Strength, Volume, Risk)
- **7|7|7 classification**: Top Momentum / Breakout Watch / Risk Flags
- **CoinGecko + Jupiter** data sources
- Auto-generated HTML, zero backend, GitHub Pages hosted

## Scoring
```
Score = Trend(25) + Momentum(25) + Rel.Strength(20) + Volume(15) + Risk(15)
```
- **Trend**: Price > EMA, multi-timeframe alignment
- **Momentum**: Percentile-based ROC ranking within Solana ecosystem
- **Rel. Strength**: Performance vs class median
- **Volume**: Relative volume vs ecosystem average
- **Risk**: Volatility, drawdown, market cap stability

## Architecture
```
solana_pipeline.py → CoinGecko API → compute_scores() → generate_html() → index.html
```

## Run
```bash
python3 solana_pipeline.py
```

## Built by Atlas Nexus
- GitHub: [AtlasNexusOps](https://github.com/AtlasNexusOps)
- Markets Dashboard: [atlasnexusops.github.io/markets-dashboard](https://atlasnexusops.github.io/markets-dashboard/)
