# /// script
# requires-python = ">=3.10"
# dependencies = ["pandas", "numpy", "yfinance", "lxml", "requests"]
# ///
"""
Reclaim-Scanner (Methode A) ueber S&P500 + Nasdaq Composite + STOXX 600.
Liquiditaetsfilter -> aktueller Methode-A-Status je Wert -> results.json + dashboard.html.
"""
import json, sys, pathlib
from io import StringIO
import numpy as np, pandas as pd, requests
import yfinance as yf

BASE = pathlib.Path(__file__).resolve().parent

H = {"User-Agent": "Mozilla/5.0"}
MIN_PRICE = 5.0
MIN_DOLLAR_VOL = 3_000_000      # Median 30T Dollar-Volumen
MIN_LEG = 0.08                  # Downtrend mind. 8%
N = 5                           # Pivot-Staerke
SUFFIX = {"Switzerland":".SW","Germany":".DE","France":".PA","Netherlands":".AS","Spain":".MC",
          "Italy":".MI","United Kingdom":".L","Sweden":".ST","Denmark":".CO","Finland":".HE",
          "Belgium":".BR","Norway":".OL","Ireland":".IR","Portugal":".LS","Austria":".VI","Poland":".WA"}


def universe():
    tk = {}
    try:
        h = requests.get("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies", headers=H, timeout=30).text
        for s in pd.read_html(StringIO(h))[0]['Symbol'].astype(str):
            tk[s.replace('.', '-')] = "US"
    except Exception as e: print("S&P500:", e, file=sys.stderr)
    try:
        t = requests.get("https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt", headers=H, timeout=30).text
        nd = pd.read_csv(StringIO(t), sep='|')
        nd = nd[(nd['Test Issue'] == 'N') & (nd['ETF'] == 'N')]
        for s in nd['Symbol'].astype(str):
            if s.isalpha() and 1 <= len(s) <= 5: tk[s] = "US"
    except Exception as e: print("Nasdaq:", e, file=sys.stderr)
    try:
        h = requests.get("https://en.wikipedia.org/wiki/STOXX_Europe_600", headers=H, timeout=30).text
        for t in pd.read_html(StringIO(h)):
            if 'Ticker' in t.columns and 'Country' in t.columns:
                for _, r in t.iterrows():
                    suf = SUFFIX.get(str(r['Country']).strip())
                    base = str(r['Ticker']).strip().split('.')[0].split(':')[-1]
                    if suf and base and base != 'nan':
                        tk[base + suf] = "EU"
                break
    except Exception as e: print("STOXX600:", e, file=sys.stderr)
    return tk


def fractals(h, l, n):
    raw = []
    for i in range(n, len(h) - n):
        if h[i] >= h[i-n:i].max() and h[i] >= h[i+1:i+n+1].max(): raw.append((i, h[i], 'H'))
        elif l[i] <= l[i-n:i].min() and l[i] <= l[i+1:i+n+1].min(): raw.append((i, l[i], 'L'))
    piv = []
    for p in raw:
        if piv and piv[-1][2] == p[2]:
            if (p[2]=='H' and p[1]>piv[-1][1]) or (p[2]=='L' and p[1]<piv[-1][1]): piv[-1] = p
        else: piv.append(p)
    return piv


def analyze(df):
    """Aktuellen Methode-A-Status + Levels bestimmen."""
    h = df['high'].values; l = df['low'].values; c = df['close'].values; n = len(df)
    if n < 60: return None
    piv = fractals(h, l, N)
    # letztes H->L (aktueller Downtrend)
    pair = None
    for k in range(len(piv) - 1):
        if piv[k][2] == 'H' and piv[k+1][2] == 'L': pair = (k, k+1)
    if not pair: return None
    ai, A, _ = piv[pair[0]]; bi, B, _ = piv[pair[1]]
    # Tief 1 = tiefstes Tief seit A (Downtrend kann sich verlaengern)
    seg_lo = bi + int(np.argmin(l[bi:])); B = l[seg_lo]; bi = seg_lo
    if A <= 0 or (A - B) / A < MIN_LEG: return None
    mid = (A + B) / 2.0; entry = (B + mid) / 2.0; stop = B; target = A
    price = c[-1]
    after = c[bi+1:]
    reclaimed = bool(len(after)) and bool((after > mid).any())
    # Pullback nach Reclaim bereits erreicht?
    pulled = False
    if reclaimed:
        ridx = bi + 1 + int(np.argmax(after > mid))
        pulled = bool((l[ridx:] <= entry).any())
    if price > target: status = "vorbei"
    elif not reclaimed: status = "DOWNTREND"
    elif pulled and price <= entry * 1.03 and price > stop: status = "ENTRY"
    elif pulled: status = "GEFUELLT"
    else: status = "BEOBACHTUNG"
    dist = (price - entry) / entry * 100
    rr = (target - entry) / (entry - stop) if entry > stop else 0
    return dict(status=status, price=round(price,2), A=round(A,2), tief1=round(B,2),
                reclaim=round(mid,2), entry=round(entry,2), stop=round(stop,2),
                target=round(target,2), dist=round(dist,1), rr=round(rr,2),
                drop=round((A-B)/A*100,1))


def main():
    tk = universe()
    print(f"Universum: {len(tk)} Ticker", file=sys.stderr)
    syms = list(tk)
    rows = []
    CHUNK = 400
    for i in range(0, len(syms), CHUNK):
        part = syms[i:i+CHUNK]
        try:
            data = yf.download(part, period="600d", interval="1d", auto_adjust=True,
                               progress=False, threads=True, group_by='ticker')
        except Exception as e:
            print("chunk err", e, file=sys.stderr); continue
        for s in part:
            try:
                d = data[s] if len(part) > 1 else data
                d = d.rename(columns=str.lower)[['open','high','low','close','volume']].dropna()
                if len(d) < 60: continue
                price = d['close'].iloc[-1]
                dvol = (d['close'] * d['volume']).tail(30).median()
                if price < MIN_PRICE or dvol < MIN_DOLLAR_VOL: continue
                r = analyze(d)
                if r: r.update(ticker=s, region=tk[s]); rows.append(r)
            except Exception: continue
        print(f"  {min(i+CHUNK,len(syms))}/{len(syms)} verarbeitet, {len(rows)} Treffer", file=sys.stderr)
    order = {"ENTRY":0,"BEOBACHTUNG":1,"GEFUELLT":2,"DOWNTREND":3,"vorbei":4}
    rows.sort(key=lambda r: (order.get(r['status'],9), abs(r['dist'])))
    out = dict(rows=rows, n_scanned=len(syms))
    json.dump(out, open(BASE / "results.json", "w"))
    from collections import Counter
    cnt = Counter(r['status'] for r in rows)
    print("STATUS:", dict(cnt), "| handelbar/Beobachtung:", cnt['ENTRY']+cnt['BEOBACHTUNG'], file=sys.stderr)
    print(f"GESAMT analysiert (liquide): {len(rows)}")


if __name__ == '__main__':
    main()
