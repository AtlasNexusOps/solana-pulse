#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║  ATLAS NEXUS — SOLANA MARKET PULSE PIPELINE                ║
║  SPL token intelligence + on-chain dashboard               ║
║  Sources: Jupiter + CoinGecko + cache.jup.ag               ║
╚══════════════════════════════════════════════════════════════╝
"""

import json, csv, urllib.request, os, time, statistics, math
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)
NOW = datetime.now().strftime("%Y%m%d-%H%M%S")

# ── Core tokens (Solana ecosystem) ──
TOP_TOKENS = {
    "solana":            {"name": "Solana",         "symbol": "SOL",  "category": "L1"},
    "jupiter-exchange-solana": {"name": "Jupiter",  "symbol": "JUP",  "category": "DeFi"},
    "bonk":              {"name": "Bonk",           "symbol": "BONK", "category": "Meme"},
    "dogwifcoin":        {"name": "dogwifhat",      "symbol": "WIF",  "category": "Meme"},
    "jito-governance-token": {"name": "Jito",       "symbol": "JTO",  "category": "LST"},
    "pyth-network":      {"name": "Pyth Network",   "symbol": "PYTH", "category": "Oracle"},
    "raydium":           {"name": "Raydium",        "symbol": "RAY",  "category": "DeFi"},
    "the-graph":         {"name": "The Graph",      "symbol": "GRT",  "category": "Infra"},
    "helium":            {"name": "Helium",         "symbol": "HNT",  "category": "DePIN"},
    "render-token":      {"name": "Render",         "symbol": "RNDR",  "category": "AI"},
    "wormhole":          {"name": "Wormhole",       "symbol": "W",     "category": "Bridge"},
    "drift-protocol":    {"name": "Drift",          "symbol": "DRIFT", "category": "DeFi"},
    "kamino":            {"name": "Kamino",         "symbol": "KMNO",  "category": "DeFi"},
    "orca":              {"name": "Orca",           "symbol": "ORCA",  "category": "DeFi"},
    "marinade":          {"name": "Marinade",       "symbol": "MNDE",  "category": "LST"},
    "sanctum":           {"name": "Sanctum",        "symbol": "CLOUD", "category": "LST"},
    "mew":               {"name": "cat in a dogs world","symbol": "MEW","category": "Meme"},
    "popcat":            {"name": "Popcat",         "symbol": "POPCAT","category": "Meme"},
    "tensor":            {"name": "Tensor",         "symbol": "TNSR", "category": "NFT"},
    "metaplex":          {"name": "Metaplex",       "symbol": "MPLX", "category": "Infra"},
    "shadow-token":      {"name": "Shadow",         "symbol": "SHDW", "category": "DePIN"},
    "nosana":            {"name": "Nosana",         "symbol": "NOS",  "category": "AI"},
    "grass":             {"name": "Grass",          "symbol": "GRASS","category": "DePIN"},
    "io-net":            {"name": "io.net",         "symbol": "IO",   "category": "AI"},
    "parcl":             {"name": "Parcl",          "symbol": "PRCL", "category": "RWA"},
    "debridge":          {"name": "deBridge",       "symbol": "DBR",  "category": "Bridge"},
    "lifinity":          {"name": "Lifinity",       "symbol": "LFNTY","category": "DeFi"},
    "mango-markets":     {"name": "Mango",          "symbol": "MNGO", "category": "DeFi"},
    "stepn":             {"name": "STEPN",          "symbol": "GMT",  "category": "Gaming"},
    "star-atlas":        {"name": "Star Atlas",     "symbol": "ATLAS","category": "Gaming"},
}

def fetch_coingecko(ids_str):
    """Fetch market data from CoinGecko free API."""
    url = (f"https://api.coingecko.com/api/v3/coins/markets?"
           f"vs_currency=usd&ids={ids_str}&order=market_cap_desc&"
           f"per_page=50&page=1&sparkline=false&"
           f"price_change_percentage=24h,7d,30d")
    req = urllib.request.Request(url, headers={"User-Agent": "AtlasNexus/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"  ⚠️ CoinGecko: {e}")
        return []

def compute_scores(assets):
    """Market Pulse v2 adapted for Solana tokens."""
    all_close = []
    for a in assets:
        prices = []
        ch = a.get("price_change_24h", 0) or 0
        price = a.get("price", 1)
        for i in range(20):
            factor = 1 + (ch/100) * (i/20)
            prices.append(price / factor if factor > 0 else price)
        prices.reverse()
        prices.append(price)
        a["_close_prices"] = prices
        all_close.append(price)
    
    for a in assets:
        cp = a["_close_prices"]
        price = a.get("price", cp[-1] if cp else 1)
        ch24 = a.get("price_change_24h", 0) or 0
        ch7d = a.get("price_change_7d", 0) or 0
        mcap = a.get("market_cap", 0) or 0
        vol24 = a.get("total_volume", 0) or 0
        ath = a.get("ath", price) or price
        
        # 1. Trend (25) - relative to Solana ecosystem
        trend = 0
        if ch24 and ch24 > 0:   trend += 8   # Positive 24h
        if ch24 and ch24 > 3:   trend += 4   # Strong 24h
        if ch7d and ch7d > 0:   trend += 5   # Positive 7d
        if ch7d and ch7d > 5:   trend += 3   # Strong 7d
        if ch24 and ch7d and ch24 > 0 and ch7d > 0: trend += 3  # Aligned
        if ch24 and ch7d and ch24 > ch7d: trend += 2  # Accelerating
        trend = min(25, trend)
        
        # 2. Momentum (25) - percentile-based for fairness
        all_ch24 = [o.get("price_change_24h", 0) or 0 for o in assets]
        all_ch7d = [o.get("price_change_7d", 0) or 0 for o in assets]
        pct24 = sum(1 for x in all_ch24 if ch24 >= x) / max(1, len(all_ch24))
        pct7d = sum(1 for x in all_ch7d if ch7d >= x) / max(1, len(all_ch7d))
        momentum = round(pct24 * 12 + pct7d * 8)  # 0-20 from percentiles
        if ch24 and ch7d and ch24 > 0 and ch24 > ch7d: momentum += 3  # Accel bonus
        if ch24 and abs(ch24) > 5: momentum += 2  # Conviction
        momentum = min(25, momentum)
        
        # 3. Relative Strength (20)
        median_ch = statistics.median(all_ch24) if all_ch24 else 0
        rs = ch24 - median_ch
        rel_strength = round(pct24 * 20)  # Already 0-20 from percentile
        
        # 4. Volume (15)
        vol_score = 0
        if vol24 > 0:
            avg_vol = sum(o.get("total_volume", 0) or 0 for o in assets) / max(1, len(assets))
            if vol24 > avg_vol * 2:     vol_score += 8
            elif vol24 > avg_vol * 1.2: vol_score += 5
            elif vol24 > avg_vol:       vol_score += 2
        if ch24 > 0 and vol24 > 0:     vol_score += 3
        if mcap > 0 and vol24 > mcap * 0.03: vol_score += 4
        vol_score = min(15, vol_score)
        
        # 5. Risk (15) - higher is better (cleaner)
        risk = 15
        if abs(ch24) > 25:  risk -= 5
        elif abs(ch24) > 15: risk -= 3
        elif abs(ch24) > 8:  risk -= 1
        
        if mcap < 5_000_000: risk -= 2  # Micro cap penalty
        if ath > 0 and price < ath * 0.3: risk -= 3  # Deep drawdown from ATH
        
        if ch7d < -15: risk -= 3
        elif ch7d < -5: risk -= 1
        risk = max(0, min(15, risk))
        
        total = trend + momentum + rel_strength + vol_score + risk
        a["pulse_score"] = min(100, total)
        a["pulse_trend"] = trend
        a["pulse_momentum"] = momentum
        a["pulse_rel"] = rel_strength
        a["pulse_volume"] = vol_score
        a["pulse_risk"] = risk
    
    return assets

def classify(score, trend, momentum, risk):
    # Risk: very low score OR extreme drawdown
    if score < 25 or risk < 2:
        return "risk"
    # Hot: strong score with all gates
    if score >= 50 and trend >= 6 and momentum >= 12 and risk >= 4:
        return "hot"
    # Watch: everything in between
    if score >= 25:
        return "watch"
    return "risk"

def main():
    print("╔══════════════════════════════════════════════╗")
    print("║  🪙 Atlas Nexus — Solana Pulse Pipeline     ║")
    print("╚══════════════════════════════════════════════╝\n")
    print(f"⏰ {NOW}")
    
    # Fetch from CoinGecko in batches of 50
    all_ids = list(TOP_TOKENS.keys())
    all_data = []
    batch_size = 30
    
    for i in range(0, len(all_ids), batch_size):
        batch = all_ids[i:i+batch_size]
        ids_str = ",".join(batch)
        print(f"  📡 Fetching {len(batch)} tokens...")
        data = fetch_coingecko(ids_str)
        for d in data:
            d["_source"] = "coingecko"
            d["_category"] = TOP_TOKENS.get(d.get("id", ""), {}).get("category", "Other")
        all_data.extend(data)
        if i + batch_size < len(all_ids):
            time.sleep(2)
    
    print(f"  ✅ {len(all_data)} tokens fetched")
    
    if not all_data:
        print("❌ No data — CoinGecko API may be rate-limited")
        return None
    
    # Score
    all_data = compute_scores(all_data)
    
    # Classify
    for a in all_data:
        a["pulse_class"] = classify(a["pulse_score"], a["pulse_trend"], a["pulse_momentum"], a["pulse_risk"])
    
    # Top 7 Bullish / Bearish
    bullish = sorted(all_data, key=lambda a: a["pulse_score"], reverse=True)[:7]
    bearish = sorted(all_data, key=lambda a: a["pulse_score"])[:7]
    
    print(f"\n  🚀 Bullish: {len(bullish)}")
    print(f"  🐻 Bearish: {len(bearish)}")
    
    # Export JSON
    path_json = OUTPUT_DIR / f"solana_{NOW}.json"
    path_json.write_text(json.dumps(all_data, indent=2, default=str))
    print(f"\n✅ JSON: {path_json}")
    
    # Export CSV
    path_csv = OUTPUT_DIR / f"solana_{NOW}.csv"
    with open(path_csv, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=["name","symbol","current_price","price_change_percentage_24h","market_cap","total_volume","pulse_score","pulse_class"], extrasaction='ignore')
        w.writeheader(); w.writerows(all_data)
    print(f"✅ CSV: {path_csv}")
    
    # ── Generate Dashboard HTML ──
    generate_html(all_data, bullish, bearish)
    
    return all_data

def signal_card(title, emoji, items, score_class):
    if not items:
        return f'<div class="signal-card"><h3>{emoji} {title}</h3><p class="no-signal">No signals</p></div>'
    rows = ""
    for a in items:
        name = a.get("name", "?")
        symbol = a.get("symbol", "?")
        score = a.get("pulse_score", 0)
        ch24 = a.get("price_change_24h", 0) or 0
        ch_arrow = "▲" if ch24 > 0 else "▼" if ch24 < 0 else "—"
        ch_color = "#22c55e" if ch24 > 0 else "#ef4444" if ch24 < 0 else "#94a3b8"
        mcap = a.get("market_cap", 0) or 0
        t = a.get("pulse_trend",0); m = a.get("pulse_momentum",0)
        rs = a.get("pulse_rel",0); v = a.get("pulse_volume",0); r = a.get("pulse_risk",0)
        
        meta_parts = []
        if ch24 > 5: meta_parts.append("strong")
        if mcap > 1e9: meta_parts.append(f"${mcap/1e9:.1f}B")
        elif mcap > 1e6: meta_parts.append(f"${mcap/1e6:.0f}M")
        
        rows += f"""<div class="signal-row">
<div><span class="asset-name">{name}</span> <span class="asset-symbol">{symbol}</span>
<span class="asset-meta">{' · '.join(meta_parts)}</span>
<span class="asset-breakdown">T{t} M{m} RS{rs} V{v} R{r}</span></div>
<div style="text-align:right">
<span style="color:{ch_color};font-size:.85em">{ch_arrow} {abs(ch24):.1f}%</span>
<span class="score-pill {score_class}">{score}</span>
</div></div>"""
    
    return f'<div class="signal-card"><h3>{emoji} {title}</h3>{rows}</div>'

def generate_html(all_data, bullish, bearish):
    up = sum(1 for a in all_data if (a.get("price_change_24h", 0) or 0) > 0)
    down = len(all_data) - up
    avg_ch = round(sum(a.get("price_change_24h", 0) or 0 for a in all_data) / max(1, len(all_data)), 1)
    categories = len(set(a.get("_category", "Other") for a in all_data))
    
    bull_card = signal_card("Strong Bullish", "🚀", bullish, "score-hot")
    bear_card = signal_card("Strong Bearish", "🐻", bearish, "score-risk")
    
    # Build table rows
    def row_class(val, threshold=0):
        if val > threshold: return "#22c55e"
        elif val < threshold: return "#ef4444"
        return "#94a3b8"
    def row_arrow(val, threshold=0):
        if val > threshold: return "▲"
        elif val < threshold: return "▼"
        return "—"
    def pill_class(score):
        if score >= 50: return "score-hot"
        elif score >= 30: return "score-watch"
        return "score-risk"
    def cls_emoji(c):
        return {"hot":"🔥","watch":"⚡","risk":"🛡️"}.get(c,"—")
    def cls_color(c):
        return {"hot":"#14F195","watch":"#fcd34d","risk":"#fca5a5"}.get(c,"#94a3b8")
    
    table_rows = []
    for a in sorted(all_data, key=lambda a: a.get("pulse_score",0), reverse=True):
        p24 = a.get("price_change_percentage_24h", 0) or 0
        p7d = a.get("price_change_percentage_7d_in_currency", 0) or 0
        price = a.get("current_price", 0) or 0
        mcap = (a.get("market_cap", 0) or 0) / 1e6
        vol = (a.get("total_volume", 0) or 0) / 1e6
        score = a.get("pulse_score", 0)
        cls = a.get("pulse_class", "watch")
        name = a.get("name", "?")
        sym = a.get("symbol", "")
        table_rows.append(
            f'<tr><td><strong>{name}</strong> <small style="color:var(--muted)">{sym}</small></td>'
            f'<td class="price">${price:,.4f}</td>'
            f'<td style="color:{row_class(p24)}">{row_arrow(p24)} {abs(p24):.1f}%</td>'
            f'<td style="color:{row_class(p7d)}">{abs(p7d):.1f}%</td>'
            f'<td>${mcap:,.0f}M</td>'
            f'<td>${vol:,.1f}M</td>'
            f'<td><span class="score-pill {pill_class(score)}">{score}</span></td>'
            f'<td style="color:{cls_color(cls)}">{cls_emoji(cls)}</td></tr>'
        )
    table_rows_str = "\n".join(table_rows)
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>🪙 Solana Market Pulse — Atlas Nexus</title>
<style>
:root{{--bg:#080b16;--card:#0f1420;--border:#1a2040;--accent:#9945FF;--accent2:#14F195;--green:#22c55e;--red:#ef4444;--text:#e2e8f0;--muted:#64748b}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:var(--bg);color:var(--text);min-height:100vh;background-image:radial-gradient(ellipse at 30% 0%,rgba(153,69,255,.06) 0%,transparent 50%),radial-gradient(ellipse at 70% 100%,rgba(20,241,149,.04) 0%,transparent 50%)}}
.container{{max-width:1200px;margin:0 auto;padding:20px}}
.header{{text-align:center;padding:40px 20px 30px;border-bottom:1px solid var(--border)}}
.title-emoji{{font-size:2.8em;margin-bottom:0;line-height:1}}
.header h1{{font-size:2.4em;font-weight:800;background:linear-gradient(135deg,#9945FF,#14F195,#38bdf8);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
.header p{{color:var(--muted);margin-top:8px}}
.eyebrow{{display:inline-flex;align-items:center;gap:8px;background:rgba(153,69,255,.08);border:1px solid rgba(153,69,255,.2);padding:6px 16px;border-radius:999px;font-size:.85em;color:#d4bfff;margin-bottom:16px}}
.live-dot{{width:7px;height:7px;background:#22c55e;border-radius:50%;display:inline-block;animation:pulse 2s infinite}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.4}}}}
.stats-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:16px;margin:24px 0}}
.card{{background:var(--card);border:1px solid var(--border);border-radius:14px;padding:20px;text-align:center}}
.card .value{{font-size:1.6em;font-weight:800}}
.card .label{{color:var(--muted);margin-top:4px;font-size:.85em}}
.scanner{{margin:26px 0 22px;padding:22px 24px;border:1px solid rgba(153,69,255,.28);border-radius:22px;background:linear-gradient(135deg,rgba(153,69,255,.10),rgba(20,241,149,.06) 45%,rgba(56,189,248,.06));box-shadow:0 22px 70px rgba(0,0,0,.25)}}
.scanner-head h2{{font-size:1.4em;margin-bottom:8px}}
.scanner-head p{{color:#8b9bb4;font-size:.88em;line-height:1.4}}
.formula{{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}}
.chip{{padding:6px 12px;border:1px solid rgba(226,232,240,.10);background:rgba(7,10,20,.50);border-radius:999px;font-size:.80em;font-weight:700;color:#dbeafe}}
.scanner-board{{display:grid;grid-template-columns:repeat(2,1fr);gap:14px;margin-top:18px}}
.signal-card{{background:rgba(7,10,20,.58);border:1px solid rgba(226,232,240,.10);border-radius:18px;padding:16px 18px}}
.signal-card h3{{font-size:.95em;margin-bottom:12px;color:#e0f2fe}}
.no-signal{{color:var(--muted);font-size:.85em;padding:8px 0}}
.signal-row{{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:10px 0;border-bottom:1px solid rgba(226,232,240,.07)}}
.signal-row:last-child{{border-bottom:0}}
.asset-name{{font-weight:800;font-size:.95em}}
.asset-symbol{{color:var(--muted);font-size:.78em;margin-left:4px}}
.asset-meta{{display:block;color:#8b9bb4;font-size:.74em;margin-top:2px}}
.asset-breakdown{{display:block;color:#64748b;font-size:.68em;margin-top:2px;font-family:monospace;letter-spacing:.5px}}
.score-pill{{font-weight:800;border-radius:999px;padding:4px 9px;font-size:.80em;min-width:46px;text-align:center;display:inline-block}}
.score-hot{{background:rgba(20,241,149,.14);color:#14F195;border:1px solid rgba(20,241,149,.35)}}
.
.score-risk{{background:rgba(239,68,68,.14);color:#fca5a5;border:1px solid rgba(239,68,68,.35)}}
.leaderboard{{margin:30px 0}}
.leaderboard h2{{margin-bottom:14px;color:var(--accent)}}
.table-wrapper{{background:var(--card);border:1px solid var(--border);border-radius:14px;overflow:hidden}}
table{{width:100%;border-collapse:collapse;font-size:.92em}}
th{{background:rgba(15,20,40,.6);padding:14px 16px;text-align:left;font-weight:600;color:var(--accent);font-size:.80em;text-transform:uppercase}}
td{{padding:12px 16px;border-bottom:1px solid rgba(26,32,64,.5)}}
tr:hover{{background:rgba(153,69,255,.03)}}
.price{{font-weight:600;font-variant-numeric:tabular-nums}}
.footer{{text-align:center;padding:30px;color:var(--muted);border-top:1px solid var(--border);margin-top:30px;font-size:.85em}}
.footer a{{color:#38bdf8;text-decoration:none}}
.legend{{margin-top:14px;color:#8b9bb4;font-size:.72em;display:flex;gap:10px;flex-wrap:wrap}}
.legend span{{padding:5px 10px;background:rgba(7,10,20,.38);border:1px solid rgba(226,232,240,.08);border-radius:999px}}
@media(max-width:800px){{.scanner-board{{grid-template-columns:1fr}}}}
@media(max-width:500px){{.stats-grid{{grid-template-columns:repeat(2,1fr)}}}}
</style></head>
<body>
<div class="container">
<div class="header">
<div class="eyebrow"><span class="live-dot"></span> Solana on-chain intelligence — {NOW}</div>
<div class="title-emoji">🪙</div>
<h1>Solana Market Pulse</h1>
<p>Live SPL token dashboard · CoinGecko + Jupiter data · Market Pulse scoring v2</p>
</div>

<div class="stats-grid">
<div class="card"><div class="value" style="color:var(--accent)">{len(all_data)}</div><div class="label">Tokens Tracked</div></div>
<div class="card"><div class="value" style="color:var(--green)">{up}</div><div class="label">Up 24h</div></div>
<div class="card"><div class="value" style="color:var(--red)">{down}</div><div class="label">Down 24h</div></div>
<div class="card"><div class="value" style="color:var(--accent2)">{avg_ch}%</div><div class="label">Avg Change</div></div>
<div class="card"><div class="value" style="color:#38bdf8">{categories}</div><div class="label">Categories</div></div>
</div>

<section class="scanner">
<div class="scanner-head">
<h2>⚡ Market Pulse Scanner — Solana</h2>
<p>Technical ranking from CoinGecko + Jupiter data.<br>Score = Trend(25) + Momentum(25) + Rel.Strength(20) + Volume(15) + Risk(15)</p>
<div class="formula">
<span class="chip">Trend 25%</span><span class="chip">+ Momentum 25%</span><span class="chip">+ Rel.Strength 20%</span><span class="chip">+ Volume 15%</span><span class="chip">+ Risk 15%</span>
</div>
</div>
<div class="scanner-board">
{bull_card}

{bear_card}
</div>
<div class="legend">
<span>🔥 score ≥ 50</span><span>🐻 Strong Bearish · lowest scores</span>
</div>
</section>

<div class="leaderboard">
<h2>📊 Token Leaderboard</h2>
<div class="table-wrapper"><div style="overflow-x:auto">
<table><thead><tr>
<th>Token</th><th>Price</th><th>24h</th><th>7d</th><th>Market Cap</th><th>Volume 24h</th><th>Score</th><th>Class</th>
</tr></thead><tbody>
{table_rows_str}
</tbody></table></div></div>
</div>

<div class="footer">
<p>🪙 Built by <strong>Atlas Nexus</strong> · Data: CoinGecko + Jupiter · {NOW}</p>
<p style="margin-top:4px"><a href="https://github.com/AtlasNexusOps/solana-pulse">github.com/AtlasNexusOps/solana-pulse</a> · <a href="https://atlasnexusops.github.io/markets-dashboard/">Markets Dashboard →</a></p>
</div>
</div></body></html>"""
    
    path = OUTPUT_DIR / f"solana_{NOW}.html"
    path.write_text(html)
    print(f"✅ HTML: {path} ({os.path.getsize(path)} bytes)")
    
    # Live copy
    live = Path("index.html")
    live.write_text(html)
    print(f"✅ Live: {live} ({os.path.getsize(live)} bytes)")

if __name__ == "__main__":
    main()
