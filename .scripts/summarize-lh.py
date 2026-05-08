"""Summarize a Lighthouse JSON report — score, CWV, and the top failing
audits with their savings estimate. Throwaway one-shot."""
import json, sys
from pathlib import Path

p = Path(__file__).parent / (sys.argv[1] if len(sys.argv) > 1 else 'lh-mobile.json')
data = json.loads(p.read_text(encoding='utf-8'))

score = data.get('categories', {}).get('performance', {}).get('score')
print(f"Performance score: {round((score or 0) * 100)}/100")
print()

audits = data.get('audits', {})
metrics_keys = ['first-contentful-paint', 'largest-contentful-paint',
                'total-blocking-time', 'cumulative-layout-shift',
                'speed-index', 'interactive', 'server-response-time']
print("Core metrics:")
for k in metrics_keys:
    a = audits.get(k, {})
    val = a.get('displayValue', '—')
    sc = a.get('score')
    sc_pct = round((sc or 0) * 100) if sc is not None else None
    print(f"  {k:30s}  {val:14s}  score={sc_pct}")

print()
print("Top opportunities (potential savings):")
opps = []
for k, a in audits.items():
    details = a.get('details', {}) or {}
    if details.get('type') == 'opportunity':
        ms = details.get('overallSavingsMs', 0)
        bytes_ = details.get('overallSavingsBytes', 0)
        if ms > 0 or bytes_ > 0:
            opps.append((ms, bytes_, k, a.get('title', ''), a.get('displayValue', '')))
opps.sort(reverse=True)
for ms, bytes_, k, title, dv in opps[:10]:
    print(f"  [{ms:5d}ms / {bytes_//1024:4d} KB]  {title}")
    if dv: print(f"             {dv}")

print()
print("Diagnostic warnings (where score < 1):")
diag = []
for k, a in audits.items():
    if (a.get('score') is not None and a.get('score') < 1
        and a.get('scoreDisplayMode') in ('binary', 'numeric')
        and not a.get('details', {}).get('type') == 'opportunity'
        and k not in metrics_keys):
        diag.append((a.get('score') or 0, k, a.get('title', ''), a.get('displayValue', '')))
diag.sort()
for sc, k, title, dv in diag[:10]:
    print(f"  [score {sc:.2f}]  {title}")
    if dv: print(f"             {dv}")
