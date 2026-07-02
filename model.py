"""
LCOH model for on-site Hydrogen Refueling Stations (HRS).
Pure-Python reimplementation of the Excel techno-economic model.
Based on Minutillo et al. (2021), with instructor simplifications S1-S4.
Author: Kuhyar Saeedi
"""
from dataclasses import dataclass, field, asdict

# ----- default parameters (baseline = report headline numbers) -----
@dataclass
class Params:
    lifetime: int = 20            # years
    interest: float = 0.03        # nominal interest rate
    days: int = 365
    hours: int = 8760
    kg_per_module: float = 50.0   # kg/day
    flow_nm3h: float = 23.0       # Nm3/h per module
    power_module: float = 118.0   # kW per module (baseline, spec=5.1)
    spec_cons: float = 5.1        # kWh/Nm3  (slider)
    density: float = 0.089        # kg/Nm3
    lhv: float = 33.0             # kWh/kg
    # electrolyzer
    elec_cost: float = 1100.0     # EUR/kW   (slider)
    om_elec: float = 0.02
    rep_factor_elec: float = 0.405
    # compression
    k: float = 1.4
    R: float = 4.12
    Tin: float = 298.0
    p_in: float = 10.0
    p_out: float = 820.0
    eta_s: float = 0.80
    eta_m: float = 0.98
    eta_g: float = 0.96
    comp_c: float = 43872.0
    comp_e: float = 0.5861
    om_comp: float = 0.08
    # refrigeration
    dh: float = 976.8             # kJ/kg
    disp_flow: float = 0.0167     # kg/s
    cop: float = 1.0
    refrig_cost: float = 5374.0
    om_refrig: float = 0.03
    # dispenser
    disp_cost: float = 65000.0
    om_disp: float = 0.03
    # water aux
    water_cost: float = 8.47
    om_water: float = 0.02
    # PV & electricity
    pv_cost: float = 950.0        # EUR/kWp  (slider)
    om_pv: float = 0.0158
    yield_naples: float = 1497.0  # kWh/kWp/yr  (slider)
    yield_milan: float = 1369.0   # kWh/kWp/yr  (slider)
    price_micro: float = 129.0    # EUR/MWh (<1 GWh tier)
    price_small: float = 119.0    # EUR/MWh (<2.5 GWh tier)
    price_medium: float = 109.0   # EUR/MWh (<5 GWh tier)
    price_override: float = 0.0   # if >0, use this for ALL sizes (price slider)
    share: float = 0.90           # 90/10 rule
    # carbon
    grid_ci: float = 250.0        # gCO2/kWh
    pv_ci: float = 35.0           # gCO2/kWh

SIZES = {"Micro": (1, 1, 50), "Small": (2, 2, 100), "Medium": (4, 2, 200)}
MIXES = {"FG": 1.00, "HG": 0.75, "MG": 0.50, "LG": 0.25}
MIX_LABEL = {"FG": "Full Grid 100%", "HG": "High Grid 75%",
             "MG": "Mid Grid 50%", "LG": "Low Grid 25%"}

def crf(p: Params) -> float:
    i, n = p.interest, p.lifetime
    return i * (1 + i) ** n / ((1 + i) ** n - 1)

def comp_work_kj_per_kg(p: Params) -> float:
    return (p.k / (p.k - 1) * p.R * p.Tin *
            ((p.p_out / p.p_in) ** ((p.k - 1) / p.k) - 1) /
            (p.eta_s * p.eta_m * p.eta_g))

def efficiency(p: Params) -> float:
    return p.lhv / (p.spec_cons / p.density)

def price_for_size(p: Params, size: str) -> float:
    if p.price_override and p.price_override > 0:
        return p.price_override
    return {"Micro": p.price_micro, "Small": p.price_small,
            "Medium": p.price_medium}[size]

def compute_config(p: Params, size: str, mix: str, city: str = "Naples") -> dict:
    N, D, kgday = SIZES[size]
    gf = MIXES[mix]
    yld = p.yield_naples if city == "Naples" else p.yield_milan
    # electrolyzer power scales with specific consumption (baseline 5.1 -> 118 kW)
    power = p.power_module * (p.spec_cons / 5.1)
    CRF = crf(p)

    h2_yr = kgday * p.days
    e_elec = N * power * p.hours / 1000.0            # MWh/yr
    e_total = e_elec / p.share
    e_grid = e_total * gf
    e_pv = e_total * (1 - gf)
    pv_kwp = e_pv * 1000.0 / yld if yld > 0 else 0.0

    comp_kw = N * (p.kg_per_module / 86400.0) * comp_work_kj_per_kg(p)
    refrig_kw = D * p.disp_flow * p.dh / p.cop

    cx_elec = N * power * p.elec_cost / 1000.0
    cx_comp = p.comp_c * comp_kw ** p.comp_e / 1000.0
    cx_refrig = refrig_kw * p.refrig_cost / 1000.0
    cx_disp = D * p.disp_cost / 1000.0
    cx_water = N * power * p.water_cost / 1000.0
    cx_pv = pv_kwp * p.pv_cost / 1000.0
    capex = cx_elec + cx_comp + cx_refrig + cx_disp + cx_water + cx_pv

    price = price_for_size(p, size)
    elec_cost = e_grid * price / 1000.0
    om = (cx_elec * p.om_elec + cx_comp * p.om_comp + cx_refrig * p.om_refrig +
          cx_disp * p.om_disp + cx_water * p.om_water + cx_pv * p.om_pv)
    opex = elec_cost + om

    cinv_a = capex * CRF
    i = p.interest
    crep_a = CRF * ((p.rep_factor_elec * cx_elec + cx_comp + cx_disp + cx_water)
                    / (1 + i) ** 10 + cx_refrig / (1 + i) ** 15)
    total = cinv_a + crep_a + opex
    lcoh = total * 1000.0 / h2_yr

    co2 = (e_grid * p.grid_ci + e_pv * p.pv_ci) / h2_yr  # kg CO2 / kg H2

    return dict(size=size, mix=mix, city=city, config=f"{size}_{mix}",
                kgday=kgday, h2_yr=h2_yr, e_elec=e_elec, e_total=e_total,
                e_grid=e_grid, e_pv=e_pv, pv_kwp=pv_kwp,
                comp_kw=comp_kw, refrig_kw=refrig_kw,
                cx_elec=cx_elec, cx_comp=cx_comp, cx_refrig=cx_refrig,
                cx_disp=cx_disp, cx_water=cx_water, cx_pv=cx_pv, capex=capex,
                price=price, elec_cost=elec_cost, om=om, opex=opex,
                cinv_a=cinv_a, crep_a=crep_a, total=total, lcoh=lcoh, co2=co2)

def compute_all(p: Params, city: str = "Naples") -> list:
    return [compute_config(p, s, m, city) for s in SIZES for m in MIXES]

def lcoh_matrix(p: Params, city: str = "Naples") -> dict:
    return {(r["size"], r["mix"]): r["lcoh"] for r in compute_all(p, city)}

if __name__ == "__main__":
    p = Params()
    print(f"CRF={crf(p):.5f}  eff={efficiency(p)*100:.1f}%  "
          f"comp_work={comp_work_kj_per_kg(p):.0f} kJ/kg")
    rows = compute_all(p, "Naples")
    best = min(rows, key=lambda r: r["lcoh"])
    worst = max(rows, key=lambda r: r["lcoh"])
    print("\nNaples LCOH matrix (EUR/kg):")
    for s in SIZES:
        vals = [next(r for r in rows if r["size"] == s and r["mix"] == m)["lcoh"]
                for m in MIXES]
        print(f"  {s:7s} " + "  ".join(f"{v:5.2f}" for v in vals))
    print(f"\nBest  : {best['config']} = {best['lcoh']:.2f}")
    print(f"Worst : {worst['config']} = {worst['lcoh']:.2f}")
    mL = compute_config(p, "Medium", "LG", "Milan")
    print(f"Milan Medium_LG = {mL['lcoh']:.2f}")
    b = best
    print(f"\nMedium_LG breakdown: Cinv={b['cinv_a']:.1f} Crep={b['crep_a']:.1f} "
          f"OPEX={b['opex']:.1f} total={b['total']:.1f}")
    print(f"CO2 FG={compute_config(p,'Medium','FG')['co2']:.1f}  "
          f"LG={compute_config(p,'Medium','LG')['co2']:.1f} kgCO2/kgH2")
