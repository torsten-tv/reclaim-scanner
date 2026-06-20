# Reclaim-Scanner — Methode A

Täglicher Long-Reversal-Scanner über **S&P 500 + Nasdaq Composite + STOXX 600** (mit Liquiditätsfilter).
Das Dashboard wird automatisch per GitHub Action erzeugt und auf GitHub Pages veröffentlicht.

## Die Strategie (Methode A)

Long-Reversal auf dem **Daily**-Chart:

1. **Downtrend** bestimmen: letztes markantes Hoch **A** → tiefstes Tief **Tief 1**.
2. **Reclaim-Linie** = 50 % des Downtrends = (A + Tief 1) / 2.
3. **Trigger:** ein **Daily-Schluss über der Reclaim-Linie** → Wert kommt auf Beobachtung.
4. **Entry:** Pullback auf die **50 %-Marke des Aufwärtsbeins** = (Tief 1 + Reclaim-Linie) / 2 (Limit).
5. **Stop:** = Tief 1.
6. **Ziel:** = altes Hoch A → ergibt mathematisch **RR 3:1**.

Kein Pullback nach dem Trigger = Trade verpasst (kein Nachlaufen).

### Validierung (Equity-Backtest, 12 Assets inkl. Gold/Silber, 1 % Risiko/Trade, 2015–2026)
- Profitabel auf allen getesteten Assets; Ziel „altes Hoch": **+402 %, MaxDD 14 %, Ertrag/DD 28,7**.
- **Out-of-Sample 2022–heute:** PF 1,90. **Bärenmarkt 2022:** PF 2,68 — Edge übersteht OOS und Bär.
- Reale Erwartung ~PF 1,9. Caveat: idealisierte Fills, ohne Gebühren/Slippage.

## Status-Kategorien im Dashboard
- 🟢 **ENTRY** — Reclaim erfolgt, Kurs am Pullback-Entry (jetzt handelbar)
- 🟡 **BEOBACHTUNG** — Reclaim erfolgt, Pullback abwarten
- ⚪ **DOWNTREND** — 50 %-Linie noch nicht zurückerobert
- 🔵 **GEFÜLLT** — Pullback gefüllt, läuft Richtung Ziel

## Dateien
- `scanner.py` — Universum laden, Liquiditätsfilter, Methode-A-Status je Wert → `results.json`
- `build_dashboard.py` — baut `dashboard.html`
- `.github/workflows/scan.yml` — tägliche Cloud-Automatik + Pages-Deploy

## Lokal ausführen
```bash
python scanner.py && python build_dashboard.py   # erzeugt dashboard.html
```

## Hinweise / Caveats
- EU-Abdeckung (STOXX 600) ist über Yahoo-Suffixe noch lückenhaft; US ist vollständig.
- Die Signale sind **Kandidaten** (mechanischer Filter) — finale Chart-Prüfung beim Trader.
- Keine Anlageberatung.
