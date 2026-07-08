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

# ================= TRANSLATIONS =================
TR = {
# -- page / header --
"page_title":           {"en": "LCOH Explorer — On-Site HRS",              "it": "LCOH Explorer — Stazione di Rifornimento H₂"},
"main_title":           {"en": "## ⚡ Levelized Cost of Hydrogen — On-Site Refueling Stations",
                         "it": "## ⚡ Costo Livellato dell'Idrogeno — Stazioni di Rifornimento On-Site"},
"main_subtitle":        {"en": "Interactive techno-economic model · simplified case study based on Minutillo et al. (2021)",
                         "it": "Modello tecno-economico interattivo · caso studio semplificato basato su Minutillo et al. (2021)"},
# -- sidebar --
"lang_label":           {"en": "Language / Lingua",                        "it": "Language / Lingua"},
"model_inputs":         {"en": "Model inputs",                             "it": "Parametri del modello"},
"sidebar_hint":         {"en": "Drag any slider — every result updates live.", "it": "Trascina un cursore — ogni risultato si aggiorna in tempo reale."},
"price_label":          {"en": "Grid electricity price",                   "it": "Prezzo elettricità dalla rete"},
"price_tiers":          {"en": "Size-based tiers (129/119/109)",           "it": "Fasce per dimensione (129/119/109)"},
"price_custom":         {"en": "Custom single price",                      "it": "Prezzo personalizzato"},
"price_slider":         {"en": "Electricity price (€/MWh)",                "it": "Prezzo elettricità (€/MWh)"},
"spec_label":           {"en": "Electrolyzer specific consumption (kWh/Nm³)", "it": "Consumo specifico elettrolizzatore (kWh/Nm³)"},
"spec_help":            {"en": "Lower = more efficient. Alkaline ≈5.1, PEM ≈4.5, advanced ≈4.0",
                         "it": "Più basso = più efficiente. Alcalino ≈5.1, PEM ≈4.5, avanzato ≈4.0"},
"elec_cost_label":      {"en": "Electrolyzer cost (€/kW)",                 "it": "Costo elettrolizzatore (€/kW)"},
"pv_cost_label":        {"en": "PV plant cost (€/kWp)",                    "it": "Costo impianto FV (€/kWp)"},
"interest_label":       {"en": "Interest rate (%)",                        "it": "Tasso di interesse (%)"},
"pvgis_label":          {"en": "**PVGIS annual yields (kWh/kWp/yr)**",     "it": "**Resa annuale PVGIS (kWh/kWp/anno)**"},
"naples_label":         {"en": "Naples (South)",                           "it": "Napoli (Sud)"},
"milan_label":          {"en": "Milan (North)",                            "it": "Milano (Nord)"},
"carbon_label":         {"en": "Carbon factors (gCO₂/kWh)",               "it": "Fattori di carbonio (gCO₂/kWh)"},
"grid_label":           {"en": "Grid",                                     "it": "Rete"},
"pv_lca_label":         {"en": "PV (life-cycle)",                          "it": "FV (ciclo di vita)"},
# -- tab names --
"tab_overview":         {"en": "📊 Overview",                              "it": "📊 Panoramica"},
"tab_explorer":         {"en": "🔬 LCOH Explorer",                         "it": "🔬 Esploratore LCOH"},
"tab_all":              {"en": "🗂️ All 12 configs",                        "it": "🗂️ Tutte le 12 configurazioni"},
"tab_sensitivity":      {"en": "📈 Sensitivity",                           "it": "📈 Analisi di sensitività"},
"tab_location":         {"en": "🗺️ Location & CO₂",                       "it": "🗺️ Località e CO₂"},
"tab_method":           {"en": "📖 Methodology",                           "it": "📖 Metodologia"},
"tab_downloads":        {"en": "📥 Downloads",                             "it": "📥 Scarica file"},
# -- overview --
"at_a_glance":          {"en": "At a glance",                              "it": "In sintesi"},
"best_lcoh":            {"en": "Best LCOH",                                "it": "LCOH migliore"},
"worst_lcoh":           {"en": "Worst LCOH",                               "it": "LCOH peggiore"},
"elec_eff":             {"en": "Electrolyzer efficiency",                  "it": "Efficienza elettrolizzatore"},
"crf_label":            {"en": "Capital Recovery Factor",                  "it": "Fattore di recupero del capitale"},
"overview_text":        {"en": """This dashboard models an **on-site hydrogen refueling station** that produces hydrogen
locally by **alkaline water electrolysis**, powered by a mix of **grid electricity** and a
**grid-connected PV plant**. It computes the **Levelized Cost of Hydrogen (LCOH)** — the
all-in lifetime cost per kilogram — across **12 configurations** (3 plant sizes × 4
electricity mixes) at two Italian sites.

Four instructor simplifications are applied: **S1** no PV export revenue · **S2** no water
cost · **S3** no storage CAPEX · **S4** a 90/10 electrolysis/compression energy split.""",
                         "it": """Questa dashboard modella una **stazione di rifornimento di idrogeno on-site** che produce
idrogeno localmente tramite **elettrolisi alcalina**, alimentata da un mix di **elettricità dalla rete** e un
**impianto fotovoltaico connesso alla rete**. Calcola il **Costo Livellato dell'Idrogeno (LCOH)** — il
costo complessivo per chilogrammo lungo l'intera vita dell'impianto — per **12 configurazioni** (3 dimensioni × 4
mix elettrici) in due siti italiani.

Quattro semplificazioni del docente sono applicate: **S1** nessun ricavo dall'esportazione FV · **S2** nessun costo
dell'acqua · **S3** nessun CAPEX per lo stoccaggio · **S4** ripartizione energetica 90/10 elettrolisi/compressione."""},
"slider_info":          {"en": "With your current slider settings, the best LCOH is **{best:.2f} €/kg** — that is **{delta:+.2f} €/kg** versus the baseline assumptions (6.50 €/kg).",
                         "it": "Con le impostazioni attuali, il miglior LCOH è **{best:.2f} €/kg** — ovvero **{delta:+.2f} €/kg** rispetto ai valori base (6,50 €/kg)."},
"slider_default":       {"en": "Sliders are at the baseline assumptions — best LCOH **6.50 €/kg** (Medium_LG, Naples), matching the report and Excel model.",
                         "it": "I cursori sono ai valori predefiniti — LCOH migliore **6,50 €/kg** (Medium_LG, Napoli), coerente con il report e il modello Excel."},
"chart_naples":         {"en": "LCOH by size and mix — Naples",            "it": "LCOH per dimensione e mix — Napoli"},
# -- explorer --
"config_explorer":      {"en": "Configuration explorer",                   "it": "Esploratore configurazioni"},
"plant_size":           {"en": "Plant size",                               "it": "Dimensione impianto"},
"elec_mix":             {"en": "Electricity mix",                          "it": "Mix elettrico"},
"site":                 {"en": "Site",                                     "it": "Sito"},
"annual_h2":            {"en": "Annual H₂",                               "it": "H₂ annuo"},
"total_ann_cost":       {"en": "Total annualised cost",                    "it": "Costo annualizzato totale"},
"pv_size":              {"en": "PV plant size",                            "it": "Dimensione impianto FV"},
"vs_baseline":          {"en": "vs baseline",                              "it": "vs base"},
"cost_breakdown":       {"en": "Annualised cost breakdown",                "it": "Ripartizione costi annualizzati"},
"ann_capex":            {"en": "Annualised CAPEX",                         "it": "CAPEX annualizzato"},
"grid_elec":            {"en": "Grid electricity",                         "it": "Elettricità dalla rete"},
"om":                   {"en": "O&M",                                      "it": "O&M"},
"ann_replex":           {"en": "Annualised REPLEX",                        "it": "REPLEX annualizzato"},
"capex_comp":           {"en": "**CAPEX components (k€)**",                "it": "**Componenti CAPEX (k€)**"},
"comp_electrolyzer":    {"en": "Electrolyzer",                             "it": "Elettrolizzatore"},
"comp_compressor":      {"en": "Compressor",                               "it": "Compressore"},
"comp_refrigerator":    {"en": "Refrigerator",                             "it": "Refrigeratore"},
"comp_dispenser":       {"en": "Dispenser",                                "it": "Dispensatore"},
"comp_water":           {"en": "Water aux.",                               "it": "Sist. acqua"},
"comp_pv":              {"en": "PV plant",                                 "it": "Impianto FV"},
"comp_total":           {"en": "TOTAL",                                    "it": "TOTALE"},
# -- all 12 --
"all_12":               {"en": "All 12 configurations",                    "it": "Tutte le 12 configurazioni"},
"naples_south":         {"en": "Naples (South)",                           "it": "Napoli (Sud)"},
"milan_north":          {"en": "Milan (North)",                            "it": "Milano (Nord)"},
"heatmap_caption":      {"en": "Green = cheaper, red = costlier. Lowest overall is Medium · Low Grid, Naples.",
                         "it": "Verde = più economico, rosso = più costoso. Il minimo è Medium · Low Grid, Napoli."},
"naples_chart":         {"en": "Naples — LCOH by size and mix",            "it": "Napoli — LCOH per dimensione e mix"},
# -- sensitivity --
"sensitivity":          {"en": "Sensitivity analysis",                     "it": "Analisi di sensitività"},
"ref_size":             {"en": "Reference size",                           "it": "Dimensione di riferimento"},
"ref_mix":              {"en": "Reference mix",                            "it": "Mix di riferimento"},
"ref_config":           {"en": "Reference configuration: {size}_{mix}, Naples.", "it": "Configurazione di riferimento: {size}_{mix}, Napoli."},
"tech_lever":           {"en": "Electrolyzer efficiency (technical lever)", "it": "Efficienza elettrolizzatore (leva tecnica)"},
"econ_lever":           {"en": "Grid electricity price (economic lever)",  "it": "Prezzo elettricità dalla rete (leva economica)"},
"sens_info":            {"en": "Electrolyzer efficiency is the key **technical** lever; grid electricity price is the key **economic** lever. Combining a PEM electrolyzer with a favourable PPA can push LCOH below 6 €/kg.",
                         "it": "L'efficienza dell'elettrolizzatore è la principale leva **tecnica**; il prezzo dell'elettricità è la principale leva **economica**. Combinando un elettrolizzatore PEM con un PPA favorevole si può portare il LCOH sotto 6 €/kg."},
# -- location & CO2 --
"loc_co2":              {"en": "Location comparison & carbon intensity",   "it": "Confronto località e intensità di carbonio"},
"naples_vs_milan":      {"en": "Naples vs Milan (PV-integrated configs)",  "it": "Napoli vs Milano (configurazioni con FV)"},
"milan_penalty":        {"en": "Milan penalty on the best config: {pen:+.1f}% (the two yields differ by ~{gap:.0f}%).",
                         "it": "Penalità Milano sulla migliore configurazione: {pen:+.1f}% (le rese differiscono di ~{gap:.0f}%)."},
"co2_title":            {"en": "**Carbon intensity by electricity mix** (kg CO₂ / kg H₂)",
                         "it": "**Intensità di carbonio per mix elettrico** (kg CO₂ / kg H₂)"},
"co2_caption":          {"en": "Grid {grid} gCO₂/kWh, PV {pv} gCO₂/kWh. The least-cost mix (Low Grid) is also the least-emitting.",
                         "it": "Rete {grid} gCO₂/kWh, FV {pv} gCO₂/kWh. Il mix più economico (Low Grid) è anche il meno inquinante."},
# -- methodology --
"methodology":          {"en": "Methodology",                              "it": "Metodologia"},
"method_text":          {"en": """- **C_inv,a** = CRF × total CAPEX, with CRF = i(1+i)ⁿ / [(1+i)ⁿ − 1]
- **C_rep,a** = discounted mid-life replacements (electrolyzer/compressor/dispenser/water at year 10, refrigerator at year 15)
- **C_O&M** = component maintenance + annual grid-electricity purchase
- **M_H₂** = daily capacity × 365

**Simplifications (instructor brief):** S1 no PV export revenue · S2 no water cost ·
S3 no storage CAPEX · S4 90/10 energy split.
**PV yields** taken from PVGIS-SARAH3 (optimized tilt/azimuth, 14% loss):
Naples 1,497 · Milan 1,369 kWh/kWp/yr.""",
                         "it": """- **C_inv,a** = CRF × CAPEX totale, con CRF = i(1+i)ⁿ / [(1+i)ⁿ − 1]
- **C_rep,a** = costi di sostituzione a metà vita attualizzati (elettrolizzatore/compressore/dispensatore/sistema acqua all'anno 10, refrigeratore all'anno 15)
- **C_O&M** = manutenzione componenti + acquisto annuale di elettricità dalla rete
- **M_H₂** = capacità giornaliera × 365

**Semplificazioni (indicazioni del docente):** S1 nessun ricavo export FV · S2 nessun costo acqua ·
S3 nessun CAPEX stoccaggio · S4 ripartizione energetica 90/10.
**Rese FV** da PVGIS-SARAH3 (inclinazione/azimut ottimizzati, 14% perdite):
Napoli 1.497 · Milano 1.369 kWh/kWp/anno."""},
# -- downloads --
"project_files":        {"en": "Project files",                            "it": "File del progetto"},
"files_intro":          {"en": "All deliverables for this project are available for download below.",
                         "it": "Tutti i materiali del progetto sono scaricabili qui sotto."},
"report_title":         {"en": "#### 📄 Report",                           "it": "#### 📄 Relazione"},
"report_desc":          {"en": "Full techno-economic report (13 pages) — methodology, all 12 configurations, sensitivity analysis, location comparison, and CO₂ intensity.",
                         "it": "Relazione tecno-economica completa (13 pagine) — metodologia, tutte le 12 configurazioni, analisi di sensitività, confronto località e intensità CO₂."},
"report_btn":           {"en": "Download report (PDF)",                    "it": "Scarica relazione (PDF)"},
"excel_title":          {"en": "#### 📊 Excel model",                      "it": "#### 📊 Modello Excel"},
"excel_desc":           {"en": "Live-formula workbook — every cell traces back to the Parameters sheet. Change any input and the LCOH recalculates across all 12 configurations.",
                         "it": "Foglio di calcolo con formule attive — ogni cella è collegata al foglio Parametri. Modifica qualsiasi input e il LCOH si ricalcola per tutte le 12 configurazioni."},
"excel_btn":            {"en": "Download Excel model",                     "it": "Scarica modello Excel"},
"pptx_title":           {"en": "#### 📽️ Presentation",                     "it": "#### 📽️ Presentazione"},
"pptx_desc":            {"en": "Slide deck for the oral exam — results, cost breakdown, sensitivity, location comparison, and conclusions.",
                         "it": "Presentazione per l'esame orale — risultati, ripartizione costi, sensitività, confronto località e conclusioni."},
"pptx_btn":             {"en": "Download presentation",                    "it": "Scarica presentazione"},
"paper_title":          {"en": "#### 📚 Source paper",                      "it": "#### 📚 Articolo di riferimento"},
"paper_link":           {"en": "[Open paper via DOI →]",                   "it": "[Apri articolo tramite DOI →]"},
"paper_copyright":      {"en": "The source paper is © Elsevier and is not redistributed here — the link points to the publisher via its DOI.",
                         "it": "L'articolo di riferimento è © Elsevier e non è ridistribuito qui — il link punta all'editore tramite DOI."},
# -- footer --
"footer":               {"en": "Built with Streamlit · model reimplemented in Python from the Excel workbook · Kuhyar Saeedi (Matricola 0384251) · Supervisor: Prof. Vesselin K. Krastev · Clean Hydrogen Technologies, Università degli Studi di Roma Tor Vergata · A.Y. 2025/2026.",
                         "it": "Realizzato con Streamlit · modello reimplementato in Python dal foglio Excel · Kuhyar Saeedi (Matricola 0384251) · Relatore: Prof. Vesselin K. Krastev · Clean Hydrogen Technologies, Università degli Studi di Roma Tor Vergata · A.A. 2025/2026."},
}

# ================= APP START =================
st.set_page_config(page_title="LCOH Explorer", page_icon="⚡",
                   layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
.block-container {padding-top: 2rem; padding-bottom: 2rem;}
h1, h2, h3 {color: #16324F;}
[data-testid="stMetricValue"] {color: #16324F; font-weight: 700;}
.small {color:#64748B; font-size:0.9rem;}
</style>
""", unsafe_allow_html=True)

# -- language toggle (very top of sidebar) --
lang = st.sidebar.radio(TR["lang_label"]["en"], ["🇬🇧 English", "🇮🇹 Italiano"],
                        index=0, horizontal=True)
L = "it" if "Italiano" in lang else "en"
def T(key, **kw):
    s = TR[key][L]
    return s.format(**kw) if kw else s

# ================= HEADER =================
c1, c2 = st.columns([0.75, 0.25])
with c1:
    st.markdown(T("main_title"))
    st.markdown(f'<span class="small">{T("main_subtitle")}</span>', unsafe_allow_html=True)
with c2:
    st.markdown('<div style="text-align:right;padding-top:0.6rem">'
                '<b>Kuhyar Saeedi</b><br>'
                '<span class="small">Matricola 0384251 · Engineering Management<br>'
                'Clean Hydrogen Technologies · Tor Vergata<br>'
                '<b>Supervisor: Prof. Vesselin K. Krastev</b></span></div>',
                unsafe_allow_html=True)
st.divider()

# ================= SIDEBAR (inputs) =================
st.sidebar.header(T("model_inputs"))
st.sidebar.caption(T("sidebar_hint"))

price_mode = st.sidebar.radio(T("price_label"),
                              [T("price_tiers"), T("price_custom")], index=0)
price_override = 0.0
if price_mode == T("price_custom"):
    price_override = st.sidebar.slider(T("price_slider"), 50, 200, 109, 1)

spec = st.sidebar.slider(T("spec_label"), 3.8, 6.5, 5.1, 0.1, help=T("spec_help"))
elec_capex = st.sidebar.slider(T("elec_cost_label"), 300, 1500, 1100, 10)
pv_capex = st.sidebar.slider(T("pv_cost_label"), 400, 1200, 950, 10)
interest = st.sidebar.slider(T("interest_label"), 1.0, 8.0, 3.0, 0.5) / 100.0

st.sidebar.markdown(T("pvgis_label"))
y_nap = st.sidebar.slider(T("naples_label"), 1200, 1700, 1497, 1)
y_mil = st.sidebar.slider(T("milan_label"), 1100, 1500, 1369, 1)

with st.sidebar.expander(T("carbon_label")):
    grid_ci = st.slider(T("grid_label"), 100, 400, 250, 5)
    pv_ci = st.slider(T("pv_lca_label"), 10, 80, 35, 1)

p = Params(spec_cons=spec, elec_cost=elec_capex, pv_cost=pv_capex,
           interest=interest, yield_naples=float(y_nap), yield_milan=float(y_mil),
           price_override=price_override, grid_ci=float(grid_ci), pv_ci=float(pv_ci))
base = Params()

rows_n = compute_all(p, "Naples")
rows_m = compute_all(p, "Milan")
best = min(rows_n, key=lambda r: r["lcoh"])
worst = max(rows_n, key=lambda r: r["lcoh"])

# ================= TABS =================
t_over, t_expl, t_all, t_sens, t_loc, t_about, t_files = st.tabs(
    [T("tab_overview"), T("tab_explorer"), T("tab_all"),
     T("tab_sensitivity"), T("tab_location"), T("tab_method"), T("tab_downloads")])

# ---------- OVERVIEW ----------
with t_over:
    st.subheader(T("at_a_glance"))
    k1, k2, k3, k4 = st.columns(4)
    k1.metric(T("best_lcoh"), f"{best['lcoh']:.2f} €/kg", best["config"])
    k2.metric(T("worst_lcoh"), f"{worst['lcoh']:.2f} €/kg", worst["config"])
    k3.metric(T("elec_eff"), f"{efficiency(p)*100:.1f} %")
    k4.metric(T("crf_label"), f"{crf(p):.4f}")
    st.markdown(T("overview_text"))
    delta = best["lcoh"] - min(compute_all(base, "Naples"), key=lambda r: r["lcoh"])["lcoh"]
    if abs(delta) > 0.005:
        st.info(T("slider_info", best=best["lcoh"], delta=delta))
    else:
        st.success(T("slider_default"))
    fig = go.Figure()
    for m in MIXES:
        fig.add_bar(name=MIX_LABEL[m], x=list(SIZES.keys()),
                    y=[next(r for r in rows_n if r["size"] == s and r["mix"] == m)["lcoh"]
                       for s in SIZES], marker_color=MIX_COLORS[m])
    fig.update_layout(barmode="group", height=380, template="plotly_white",
                      yaxis_title="LCOH (€/kg H₂)", legend_title="",
                      margin=dict(t=30, b=10), title=T("chart_naples"))
    st.plotly_chart(fig, use_container_width=True)

# ---------- EXPLORER ----------
with t_expl:
    st.subheader(T("config_explorer"))
    e1, e2, e3 = st.columns(3)
    size = e1.selectbox(T("plant_size"), list(SIZES.keys()), index=2)
    mix = e2.selectbox(T("elec_mix"), list(MIXES.keys()),
                       index=3, format_func=lambda m: MIX_LABEL[m])
    city = e3.selectbox(T("site"), ["Naples", "Milan"], index=0)
    r = compute_config(p, size, mix, city)
    rb = compute_config(base, size, mix, city)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("LCOH", f"{r['lcoh']:.2f} €/kg", f"{r['lcoh']-rb['lcoh']:+.2f} {T('vs_baseline')}")
    m2.metric(T("annual_h2"), f"{r['h2_yr']:,.0f} kg")
    m3.metric(T("total_ann_cost"), f"{r['total']:,.1f} k€/yr")
    m4.metric(T("pv_size"), f"{r['pv_kwp']:,.0f} kWp")
    cc1, cc2 = st.columns([0.5, 0.5])
    with cc1:
        labels = [T("ann_capex"), T("grid_elec"), T("om"), T("ann_replex")]
        vals = [r["cinv_a"], r["elec_cost"], r["om"], r["crep_a"]]
        fig = go.Figure(go.Pie(labels=labels, values=vals, hole=0.55,
                               marker_colors=[NAVY, AMBER, GREEN, RED],
                               textinfo="percent"))
        fig.update_layout(height=360, template="plotly_white",
                          title=T("cost_breakdown"), margin=dict(t=40, b=10),
                          legend=dict(orientation="h", y=-0.1))
        st.plotly_chart(fig, use_container_width=True)
    with cc2:
        st.markdown(T("capex_comp"))
        capex_df = pd.DataFrame({
            "Component": [T("comp_electrolyzer"), T("comp_compressor"), T("comp_refrigerator"),
                          T("comp_dispenser"), T("comp_water"), T("comp_pv"), T("comp_total")],
            "k€": [r["cx_elec"], r["cx_comp"], r["cx_refrig"], r["cx_disp"],
                   r["cx_water"], r["cx_pv"], r["capex"]]})
        st.dataframe(capex_df.style.format({"k€": "{:,.1f}"}),
                     hide_index=True, use_container_width=True)
        st.markdown(f"<span class='small'>Energy: electrolyzer "
                    f"{r['e_elec']:,.0f} MWh/yr · total {r['e_total']:,.0f} MWh/yr · "
                    f"grid {r['e_grid']:,.0f} · PV {r['e_pv']:,.0f}. "
                    f"Grid price {r['price']:.0f} €/MWh.</span>",
                    unsafe_allow_html=True)

# ---------- ALL 12 ----------
with t_all:
    st.subheader(T("all_12"))
    def matrix_df(rows):
        d = {}
        for s in SIZES:
            d[s] = {MIX_LABEL[m]: next(x for x in rows if x["size"] == s
                    and x["mix"] == m)["lcoh"] for m in MIXES}
        return pd.DataFrame(d).T[[MIX_LABEL[m] for m in MIXES]]
    ca, cb = st.columns(2)
    for col, rows, name in [(ca, rows_n, T("naples_south")), (cb, rows_m, T("milan_north"))]:
        with col:
            st.markdown(f"**{name}** — LCOH €/kg")
            df = matrix_df(rows)
            st.dataframe(df.style.format("{:.2f}")
                         .background_gradient(cmap="RdYlGn_r", axis=None),
                         use_container_width=True)
    st.caption(T("heatmap_caption"))
    fig = go.Figure()
    for m in MIXES:
        fig.add_bar(name=MIX_LABEL[m], x=list(SIZES.keys()),
                    y=[next(r for r in rows_n if r["size"] == s and r["mix"] == m)["lcoh"]
                       for s in SIZES], marker_color=MIX_COLORS[m],
                    text=[f"{next(r for r in rows_n if r['size']==s and r['mix']==m)['lcoh']:.2f}"
                          for s in SIZES], textposition="outside")
    fig.update_layout(barmode="group", height=420, template="plotly_white",
                      yaxis_title="LCOH (€/kg H₂)", title=T("naples_chart"),
                      margin=dict(t=40, b=10))
    st.plotly_chart(fig, use_container_width=True)

# ---------- SENSITIVITY ----------
with t_sens:
    st.subheader(T("sensitivity"))
    s1, s2 = st.columns(2)
    ref_size = s1.selectbox(T("ref_size"), list(SIZES.keys()), index=2, key="rs")
    ref_mix = s2.selectbox(T("ref_mix"), list(MIXES.keys()), index=2,
                           format_func=lambda m: MIX_LABEL[m], key="rm")
    st.caption(T("ref_config", size=ref_size, mix=ref_mix))
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
                          title=T("tech_lever"),
                          xaxis_title="kWh/Nm³", yaxis_title="LCOH (€/kg)",
                          margin=dict(t=40, b=10))
        st.plotly_chart(fig, use_container_width=True)
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
                          title=T("econ_lever"),
                          xaxis_title="€/MWh", yaxis_title="LCOH (€/kg)",
                          margin=dict(t=40, b=10))
        st.plotly_chart(fig, use_container_width=True)
    st.info(T("sens_info"))

# ---------- LOCATION & CO2 ----------
with t_loc:
    st.subheader(T("loc_co2"))
    pv_cfgs = [(s, m) for s in SIZES for m in MIXES if m != "FG"]
    labels = [f"{s[:3]}_{m}" for s, m in pv_cfgs]
    nap = [compute_config(p, s, m, "Naples")["lcoh"] for s, m in pv_cfgs]
    mil = [compute_config(p, s, m, "Milan")["lcoh"] for s, m in pv_cfgs]
    fig = go.Figure()
    fig.add_bar(name=f"{T('naples_label')} ({y_nap})", x=labels, y=nap, marker_color=NAVY)
    fig.add_bar(name=f"{T('milan_label')} ({y_mil})", x=labels, y=mil, marker_color="#9FC3D6")
    fig.update_layout(barmode="group", height=380, template="plotly_white",
                      yaxis_title="LCOH (€/kg)", title=T("naples_vs_milan"),
                      margin=dict(t=40, b=10))
    st.plotly_chart(fig, use_container_width=True)
    penalty = (compute_config(p, "Medium", "LG", "Milan")["lcoh"] /
               compute_config(p, "Medium", "LG", "Naples")["lcoh"] - 1) * 100
    st.caption(T("milan_penalty", pen=penalty, gap=(y_nap/y_mil-1)*100))
    st.markdown(T("co2_title"))
    co2 = [compute_config(p, "Medium", m, "Naples")["co2"] for m in MIXES]
    fig = go.Figure(go.Bar(x=[MIX_LABEL[m] for m in MIXES], y=co2,
                           marker_color=[MIX_COLORS[m] for m in MIXES],
                           text=[f"{v:.1f}" for v in co2], textposition="outside"))
    fig.add_hline(y=10, line_dash="dash", line_color=MUTE,
                  annotation_text="grey H₂ ≈ 10")
    fig.update_layout(height=340, template="plotly_white", yaxis_title="kg CO₂ / kg H₂",
                      margin=dict(t=20, b=10))
    st.plotly_chart(fig, use_container_width=True)
    st.caption(T("co2_caption", grid=grid_ci, pv=pv_ci))

# ---------- METHODOLOGY ----------
with t_about:
    st.subheader(T("methodology"))
    st.latex(r"\mathrm{LCOH} = \frac{C_{inv,a} + C_{rep,a} + C_{O\&M}}{M_{H_2}}\quad[\text{€/kg H}_2]")
    st.markdown(T("method_text"))

# ---------- DOWNLOADS ----------
with t_files:
    st.subheader(T("project_files"))
    st.markdown(T("files_intro"))
    st.divider()
    rp = os.path.join(ASSETS, "LCOH_Report_Kuhyar_Saeedi.pdf")
    xl = os.path.join(ASSETS, "LCOH_Model_Kuhyar_Saeedi.xlsx")
    pp = os.path.join(ASSETS, "LCOH_Presentation_Kuhyar_Saeedi.pptx")
    f1, f2, f3 = st.columns(3)
    with f1:
        st.markdown(T("report_title"))
        st.caption(T("report_desc"))
        if os.path.exists(rp):
            st.download_button(T("report_btn"), open(rp, "rb").read(),
                               "LCOH_Report_Kuhyar_Saeedi.pdf", "application/pdf",
                               use_container_width=True)
    with f2:
        st.markdown(T("excel_title"))
        st.caption(T("excel_desc"))
        if os.path.exists(xl):
            st.download_button(T("excel_btn"), open(xl, "rb").read(),
                               "LCOH_Model_Kuhyar_Saeedi.xlsx",
                               use_container_width=True)
    with f3:
        st.markdown(T("pptx_title"))
        st.caption(T("pptx_desc"))
        if os.path.exists(pp):
            st.download_button(T("pptx_btn"), open(pp, "rb").read(),
                               "LCOH_Presentation_Kuhyar_Saeedi.pptx",
                               use_container_width=True)
    st.divider()
    st.markdown(T("paper_title"))
    st.markdown("Minutillo, M., Perna, A., Forcina, A., Di Micco, S., Jannelli, E. (2021). "
                "*Analyzing the levelized cost of hydrogen in refueling stations with on-site "
                "hydrogen production via water electrolysis in the Italian scenario.* "
                "International Journal of Hydrogen Energy, 46(26), 13667–13677.")
    st.markdown(f"{T('paper_link')}(https://doi.org/10.1016/j.ijhydene.2020.11.110)")
    st.caption(T("paper_copyright"))

st.divider()
st.caption(T("footer"))
