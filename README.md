# LCOH Explorer — On-Site Hydrogen Refueling Stations

An interactive techno-economic dashboard that computes the **Levelized Cost of
Hydrogen (LCOH, €/kg)** for on-site Hydrogen Refueling Stations in Italy, based on
alkaline electrolysis integrated with a grid-connected PV plant.

Simplified case study based on **Minutillo et al. (2021)** with four instructor
simplifications (S1 no PV revenue · S2 no water cost · S3 no storage CAPEX ·
S4 90/10 energy split). The model is reimplemented in pure Python and reproduces
the accompanying Excel workbook to the decimal.

**Author:** Kuhyar Saeedi · Matricola 0384251 · Engineering Management ·
Clean Hydrogen Technologies · Università degli Studi di Roma Tor Vergata · A.Y. 2025/2026

## Features
- **LCOH Explorer** — live sliders (electricity price, electrolyzer efficiency,
  CAPEX, PV cost, interest rate, PVGIS yields) recompute the LCOH instantly
- All 12 configurations (3 sizes × 4 mixes) for Naples and Milan, as heatmap + chart
- Interactive sensitivity analysis (efficiency & electricity price)
- Location comparison and carbon-intensity estimate
- Methodology tab with formula, assumptions and downloads

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy (Streamlit Community Cloud)
Push this repo to GitHub, then create a new app at https://share.streamlit.io
pointing at `app.py` on the `main` branch.

## Files
| File | Purpose |
|------|---------|
| `app.py` | Streamlit dashboard (UI) |
| `model.py` | Pure-Python LCOH model (all formulas) |
| `assets/` | Report PDF and Excel model (downloadable in-app) |

## Reference
Minutillo, M., Perna, A., Forcina, A., Di Micco, S., Jannelli, E. (2021).
*Analyzing the levelized cost of hydrogen in refueling stations with on-site
hydrogen production via water electrolysis in the Italian scenario.*
International Journal of Hydrogen Energy, 46(26), 13667–13677.
https://doi.org/10.1016/j.ijhydene.2020.11.110
