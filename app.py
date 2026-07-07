"""
LCOH Explorer — interactive techno-economic dashboard for on-site Hydrogen
Refueling Stations in Italy.  Built on the simplified model (Minutillo 2021, S1-S4).
Author: Kuhyar Saeedi | Engineering Management | Tor Vergata
"""
import os
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from model import (Params, SIZES, MIXES, MIX_LABEL, crf, efficiency,
                   comp_work_kj_per_kg, compute_config, compute_all)

# ---------- palette ----------
NAVY, TEAL, GREEN, AMBER, RED = "#16324F", "#0E8388", "#3E9E6E", "#E29A2E", "#C0504D"
MUTE = "#64748B"
MIX_COLORS = {"FG": NAVY, "HG": TEAL, "MG": GREEN, "LG": AMBER}
ASSETS = os.path.join(os.path.dirname(__file__), "assets")

st.set_page_config(page_title="LCOH Explorer — On-Site HRS", page_icon="⚡",
                   layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
.block-container {padding-top: 2rem; padding-bottom: 2rem;}
h1, h2, h3 {color: #16324F;}
[data-testid="stMetricValue"] {color: #16324F; font-weight: 700;}
.small {color:#64748B; font-size:0.9rem;}
</style>
""", unsafe_allow_html=True)

# ================= HEADER =================
c1, c2 = st.columns([0.75, 0.25])
with c1:
    st.markdown("## ⚡ Levelized Cost of Hydrogen — On-Site Refueling Stations")
    st.markdown('<span class="small">Interactive techno-economic model · '
                'simplified case study based on Minutillo et al. (2021)</span>',
                unsafe_allow_html=True)
with c2:
    st.markdown('<div style="text-align:right;padding-top:0.6rem">'
                '<b>Kuhyar Saeedi</b><br>'
                '<span class="small">Matricola 0384251 · Engineering Management<br>'
                'Clean Hydrogen Technologies · Tor Vergata<br>'
                '<b>Supervisor: Prof. Vesselin K. Krastev</b></span></div>',
                unsafe_allow_html=True)
st.divider()

# ================= SIDEBAR (inputs) =================
st.sidebar.header("Model inputs")
st.sidebar.caption("Drag any slider — every result updates live.")

price_mode = st.sidebar.radio("Grid electricity price",
                              ["Size-based tiers (129/119/109)", "Custom single price"],
                              index=0)
price_override = 0.0
if price_mode == "Custom single price":
    price_override = st.sidebar.slider("Electricity price (€/MWh)", 50, 200, 109, 1)

spec = st.sidebar.slider("Electrolyzer specific consumption (kWh/Nm³)",
                         3.8, 6.5, 5.1, 0.1,
                         help="Lower = more efficient. Alkaline ≈5.1, PEM ≈4.5, advanced ≈4.0")
elec_capex = st.sidebar.slider("Electrolyzer cost (€/kW)", 300, 1500, 1100, 10)
pv_capex = st.sidebar.slider("PV plant cost (€/kWp)", 400, 1200, 950, 10)
interest = st.sidebar.slider("Interest rate (%)", 1.0, 8.0, 3.0, 0.5) / 100.0

st.sidebar.markdown("**PVGIS annual yields (kWh/kWp/yr)**")
y_nap = st.sidebar.slider("Naples (South)", 1200, 1700, 1497, 1)
y_mil = st.sidebar.slider("Milan (North)", 1100, 1500, 1369, 1)

with st.sidebar.expander("Carbon factors (gCO₂/kWh)"):
    grid_ci = st.slider("Grid", 100, 400, 250, 5)
    pv_ci = st.slider("PV (life-cycle)", 10, 80, 35, 1)

p = Params(spec_cons=spec, elec_cost=elec_capex, pv_cost=pv_capex,
           interest=interest, yield_naples=float(y_nap), yield_milan=float(y_mil),
           price_override=price_override, grid_ci=float(grid_ci), pv_ci=float(pv_ci))

# baseline (defaults) for comparison
base = Params()

rows_n = compute_all(p, "Naples")
rows_m = compute_all(p, "Milan")
best = min(rows_n, key=lambda r: r["lcoh"])
worst = max(rows_n, key=lambda r: r["lcoh"])

# ================= TABS =================
t_over, t_expl, t_all, t_sens, t_loc, t_about, t_files = st.tabs(
    ["📊 Overview", "🔬 LCOH Explorer", "🗂️ All 12 configs",
     "📈 Sensitivity", "🗺️ Location & CO₂", "📖 Methodology", "📥 Downloads"])

# ---------- OVERVIEW ----------
with t_over:
    st.subheader("At a glance")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Best LCOH", f"{best['lcoh']:.2f} €/kg", best["config"])
    k2.metric("Worst LCOH", f"{worst['lcoh']:.2f} €/kg", worst["config"])
    k3.metric("Electrolyzer efficiency", f"{efficiency(p)*100:.1f} %")
    k4.metric("Capital Recovery Factor", f"{crf(p):.4f}")

    st.markdown("""
This dashboard models an **on-site hydrogen refueling station** that produces hydrogen
locally by **alkaline water electrolysis**, powered by a mix of **grid electricity** and a
**grid-connected PV plant**. It computes the **Levelized Cost of Hydrogen (LCOH)** — the
all-in lifetime cost per kilogram — across **12 configurations** (3 plant sizes × 4
electricity mixes) at two Italian sites.

Four instructor simplifications are applied: **S1** no PV export revenue · **S2** no water
cost · **S3** no storage CAPEX · **S4** a 90/10 electrolysis/compression energy split.
""")
    delta = best["lcoh"] - min(compute_all(base, "Naples"), key=lambda r: r["lcoh"])["lcoh"]
    if abs(delta) > 0.005:
        st.info(f"With your current slider settings, the best LCOH is "
                f"**{best['lcoh']:.2f} €/kg** — that is **{delta:+.2f} €/kg** versus the "
                f"baseline assumptions (6.50 €/kg).")
    else:
        st.success("Sliders are at the baseline assumptions — best LCOH **6.50 €/kg** "
                   "(Medium_LG, Naples), matching the report and Excel model.")

    # quick bar of best per size (Naples, current settings)
    fig = go.Figure()
    for m in MIXES:
        fig.add_bar(name=MIX_LABEL[m], x=list(SIZES.keys()),
                    y=[next(r for r in rows_n if r["size"] == s and r["mix"] == m)["lcoh"]
                       for s in SIZES], marker_color=MIX_COLORS[m])
    fig.update_layout(barmode="group", height=380, template="plotly_white",
                      yaxis_title="LCOH (€/kg H₂)", legend_title="",
                      margin=dict(t=30, b=10), title="LCOH by size and mix — Naples")
    st.plotly_chart(fig, width='stretch')

# ---------- EXPLORER ----------
with t_expl:
    st.subheader("Configuration explorer")
    e1, e2, e3 = st.columns(3)
    size = e1.selectbox("Plant size", list(SIZES.keys()), index=2)
    mix = e2.selectbox("Electricity mix", list(MIXES.keys()),
                       index=3, format_func=lambda m: MIX_LABEL[m])
    city = e3.selectbox("Site", ["Naples", "Milan"], index=0)

    r = compute_config(p, size, mix, city)
    rb = compute_config(base, size, mix, city)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("LCOH", f"{r['lcoh']:.2f} €/kg", f"{r['lcoh']-rb['lcoh']:+.2f} vs baseline")
    m2.metric("Annual H₂", f"{r['h2_yr']:,.0f} kg")
    m3.metric("Total annualised cost", f"{r['total']:,.1f} k€/yr")
    m4.metric("PV plant size", f"{r['pv_kwp']:,.0f} kWp")

    cc1, cc2 = st.columns([0.5, 0.5])
    with cc1:
        labels = ["Annualised CAPEX", "Grid electricity", "O&M", "Annualised REPLEX"]
        vals = [r["cinv_a"], r["elec_cost"], r["om"], r["crep_a"]]
        fig = go.Figure(go.Pie(labels=labels, values=vals, hole=0.55,
                               marker_colors=[NAVY, AMBER, GREEN, RED],
                               textinfo="percent"))
        fig.update_layout(height=360, template="plotly_white",
                          title="Annualised cost breakdown", margin=dict(t=40, b=10),
                          legend=dict(orientation="h", y=-0.1))
        st.plotly_chart(fig, width='stretch')
    with cc2:
        st.markdown("**CAPEX components (k€)**")
        capex_df = pd.DataFrame({
            "Component": ["Electrolyzer", "Compressor", "Refrigerator",
                          "Dispenser", "Water aux.", "PV plant", "TOTAL"],
            "k€": [r["cx_elec"], r["cx_comp"], r["cx_refrig"], r["cx_disp"],
                   r["cx_water"], r["cx_pv"], r["capex"]]})
        st.dataframe(capex_df.style.format({"k€": "{:,.1f}"}),
                     hide_index=True, width='stretch')
        st.markdown(f"<span class='small'>Energy: electrolyzer "
                    f"{r['e_elec']:,.0f} MWh/yr · total {r['e_total']:,.0f} MWh/yr · "
                    f"grid {r['e_grid']:,.0f} · PV {r['e_pv']:,.0f}. "
                    f"Grid price {r['price']:.0f} €/MWh.</span>",
                    unsafe_allow_html=True)

# ---------- ALL 12 ----------
with t_all:
    st.subheader("All 12 configurations")
    def matrix_df(rows):
        d = {}
        for s in SIZES:
            d[s] = {MIX_LABEL[m]: next(x for x in rows if x["size"] == s
                    and x["mix"] == m)["lcoh"] for m in MIXES}
        return pd.DataFrame(d).T[[MIX_LABEL[m] for m in MIXES]]
    ca, cb = st.columns(2)
    for col, rows, name in [(ca, rows_n, "Naples (South)"), (cb, rows_m, "Milan (North)")]:
        with col:
            st.markdown(f"**{name}** — LCOH €/kg")
            df = matrix_df(rows)
            st.dataframe(df.style.format("{:.2f}")
                         .background_gradient(cmap="RdYlGn_r", axis=None),
                         width='stretch')
    st.caption("Green = cheaper, red = costlier. Lowest overall is Medium · Low Grid, Naples.")

    fig = go.Figure()
    for m in MIXES:
        fig.add_bar(name=MIX_LABEL[m], x=list(SIZES.keys()),
                    y=[next(r for r in rows_n if r["size"] == s and r["mix"] == m)["lcoh"]
                       for s in SIZES], marker_color=MIX_COLORS[m],
                    text=[f"{next(r for r in rows_n if r['size']==s and r['mix']==m)['lcoh']:.2f}"
                          for s in SIZES], textposition="outside")
    fig.update_layout(barmode="group", height=420, template="plotly_white",
                      yaxis_title="LCOH (€/kg H₂)", title="Naples — LCOH by size and mix",
                      margin=dict(t=40, b=10))
    st.plotly_chart(fig, width='stretch')

# ---------- SENSITIVITY ----------
with t_sens:
    st.subheader("Sensitivity analysis")
    s1, s2 = st.columns(2)
    ref_size = s1.selectbox("Reference size", list(SIZES.keys()), index=2, key="rs")
    ref_mix = s2.selectbox("Reference mix", list(MIXES.keys()), index=2,
                           format_func=lambda m: MIX_LABEL[m], key="rm")
    st.caption(f"Reference configuration: {ref_size}_{ref_mix}, Naples.")

    g1, g2 = st.columns(2)
    with g1:
        specs = [4.0, 4.5, 4.8, 5.1, 5.5, 6.0]
        ys = []
        for sp in specs:
            pp = Params(**{**p.__dict__, "spec_cons": sp})
            ys.append(compute_config(pp, ref_size, ref_mix, "Naples")["lcoh"])
        fig = go.Figure(go.Scatter(x=specs, y=ys, mode="lines+markers+text",
                                   line=dict(color=TEAL, width=3),
                                   text=[f"{v:.2f}" for v in ys], textposition="top center"))
        fig.update_layout(height=360, template="plotly_white",
                          title="Electrolyzer efficiency (technical lever)",
                          xaxis_title="Specific consumption (kWh/Nm³)",
                          yaxis_title="LCOH (€/kg)", margin=dict(t=40, b=10))
        st.plotly_chart(fig, width='stretch')
    with g2:
        prices = [70, 90, 109, 130, 150, 180]
        yp = []
        for pr in prices:
            pp = Params(**{**p.__dict__, "price_override": float(pr)})
            yp.append(compute_config(pp, ref_size, ref_mix, "Naples")["lcoh"])
        fig = go.Figure(go.Scatter(x=prices, y=yp, mode="lines+markers+text",
                                   line=dict(color=AMBER, width=3),
                                   text=[f"{v:.2f}" for v in yp], textposition="top center"))
        fig.update_layout(height=360, template="plotly_white",
                          title="Grid electricity price (economic lever)",
                          xaxis_title="Price (€/MWh)", yaxis_title="LCOH (€/kg)",
                          margin=dict(t=40, b=10))
        st.plotly_chart(fig, width='stretch')
    st.info("Electrolyzer efficiency is the key **technical** lever; grid electricity "
            "price is the key **economic** lever. Combining a PEM electrolyzer with a "
            "favourable PPA can push LCOH below 6 €/kg.")

# ---------- LOCATION & CO2 ----------
with t_loc:
    st.subheader("Location comparison & carbon intensity")
    pv_cfgs = [(s, m) for s in SIZES for m in MIXES if m != "FG"]
    labels = [f"{s[:3]}_{m}" for s, m in pv_cfgs]
    nap = [compute_config(p, s, m, "Naples")["lcoh"] for s, m in pv_cfgs]
    mil = [compute_config(p, s, m, "Milan")["lcoh"] for s, m in pv_cfgs]
    fig = go.Figure()
    fig.add_bar(name=f"Naples ({y_nap})", x=labels, y=nap, marker_color=NAVY)
    fig.add_bar(name=f"Milan ({y_mil})", x=labels, y=mil, marker_color="#9FC3D6")
    fig.update_layout(barmode="group", height=380, template="plotly_white",
                      yaxis_title="LCOH (€/kg)", title="Naples vs Milan (PV-integrated configs)",
                      margin=dict(t=40, b=10))
    st.plotly_chart(fig, width='stretch')
    penalty = (compute_config(p, "Medium", "LG", "Milan")["lcoh"] /
               compute_config(p, "Medium", "LG", "Naples")["lcoh"] - 1) * 100
    st.caption(f"Milan penalty on the best config: {penalty:+.1f}% "
               f"(the two yields differ by ~{(y_nap/y_mil-1)*100:.0f}%).")

    st.markdown("**Carbon intensity by electricity mix** (kg CO₂ / kg H₂)")
    co2 = [compute_config(p, "Medium", m, "Naples")["co2"] for m in MIXES]
    fig = go.Figure(go.Bar(x=[MIX_LABEL[m] for m in MIXES], y=co2,
                           marker_color=[MIX_COLORS[m] for m in MIXES],
                           text=[f"{v:.1f}" for v in co2], textposition="outside"))
    fig.add_hline(y=10, line_dash="dash", line_color=MUTE,
                  annotation_text="grey H₂ ≈ 10")
    fig.update_layout(height=340, template="plotly_white", yaxis_title="kg CO₂ / kg H₂",
                      margin=dict(t=20, b=10))
    st.plotly_chart(fig, width='stretch')
    st.caption(f"Grid {grid_ci} gCO₂/kWh, PV {pv_ci} gCO₂/kWh. The least-cost mix "
               f"(Low Grid) is also the least-emitting.")

# ---------- ABOUT ----------
with t_about:
    st.subheader("Methodology")
    st.latex(r"\mathrm{LCOH} = \frac{C_{inv,a} + C_{rep,a} + C_{O\&M}}{M_{H_2}}\quad[\text{€/kg H}_2]")
    st.markdown("""
- **C_inv,a** = CRF × total CAPEX, with CRF = i(1+i)ⁿ / [(1+i)ⁿ − 1]
- **C_rep,a** = discounted mid-life replacements (electrolyzer/compressor/dispenser/water at year 10, refrigerator at year 15)
- **C_O&M** = component maintenance + annual grid-electricity purchase
- **M_H₂** = daily capacity × 365

**Simplifications (instructor brief):** S1 no PV export revenue · S2 no water cost ·
S3 no storage CAPEX · S4 90/10 energy split.
**PV yields** taken from PVGIS-SARAH3 (optimized tilt/azimuth, 14% loss):
Naples 1,497 · Milan 1,369 kWh/kWp/yr.
""")

# ---------- DOWNLOADS ----------
with t_files:
    st.subheader("Project files")
    st.markdown("All deliverables for this project are available for download below.")
    st.divider()
    rp = os.path.join(ASSETS, "LCOH_Report_Kuhyar_Saeedi.pdf")
    xl = os.path.join(ASSETS, "LCOH_Model_Kuhyar_Saeedi.xlsx")
    pp = os.path.join(ASSETS, "LCOH_Presentation_Kuhyar_Saeedi.pptx")

    f1, f2, f3 = st.columns(3)
    with f1:
        st.markdown("#### 📄 Report")
        st.caption("Full techno-economic report (13 pages) — methodology, all 12 configurations, "
                   "sensitivity analysis, location comparison, and CO₂ intensity.")
        if os.path.exists(rp):
            st.download_button("Download report (PDF)", open(rp, "rb").read(),
                               "LCOH_Report_Kuhyar_Saeedi.pdf", "application/pdf",
                               use_container_width=True)
    with f2:
        st.markdown("#### 📊 Excel model")
        st.caption("Live-formula workbook — every cell traces back to the Parameters sheet. "
                   "Change any input and the LCOH recalculates across all 12 configurations.")
        if os.path.exists(xl):
            st.download_button("Download Excel model", open(xl, "rb").read(),
                               "LCOH_Model_Kuhyar_Saeedi.xlsx",
                               use_container_width=True)
    with f3:
        st.markdown("#### 📽️ Presentation")
        st.caption("Slide deck for the oral exam — results, cost breakdown, sensitivity, "
                   "location comparison, and conclusions.")
        if os.path.exists(pp):
            st.download_button("Download presentation", open(pp, "rb").read(),
                               "LCOH_Presentation_Kuhyar_Saeedi.pptx",
                               use_container_width=True)

    st.divider()
    st.markdown("#### 📚 Source paper")
    st.markdown("Minutillo, M., Perna, A., Forcina, A., Di Micco, S., Jannelli, E. (2021). "
                "*Analyzing the levelized cost of hydrogen in refueling stations with on-site "
                "hydrogen production via water electrolysis in the Italian scenario.* "
                "International Journal of Hydrogen Energy, 46(26), 13667–13677.")
    st.markdown("[Open paper via DOI →](https://doi.org/10.1016/j.ijhydene.2020.11.110)")
    st.caption("The source paper is © Elsevier and is not redistributed here — "
               "the link points to the publisher via its DOI.")

st.divider()
st.caption("Built with Streamlit · model reimplemented in Python from the Excel workbook · "
           "Kuhyar Saeedi (Matricola 0384251) · Supervisor: Prof. Vesselin K. Krastev · "
           "Clean Hydrogen Technologies, Università degli Studi di Roma Tor Vergata · A.Y. 2025/2026.")
