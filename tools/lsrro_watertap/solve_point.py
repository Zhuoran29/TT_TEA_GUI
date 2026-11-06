"""Solve one WaterTAP LSRRO case and print one JSON line.

Usage: python solve_point.py STAGES RECOVERY FEED_TDS_G_L

The flowsheet is solved at the WaterTAP default feed flow (Qin = 1e-3 m3/s). WaterTAP sizes and costs
LSRRO linearly with flow, so all intensive results (SEC, area and cost per unit flow) are independent of
the flow, and solving at the default flow avoids the scaling problems seen at large flows.
Settings follow Atia et al. 2023 (A fixed at 4.2e-12 m/s-Pa, B optimized per stage up to 3.5e-6 m/s,
NaCl solubility limit, calculated concentration polarization and pressure drop, 1D RO, 10 elements,
product limit 1,000 ppm).
"""
import sys, io, contextlib, json, time
from pyomo.environ import value, check_optimal_termination
from watertap.flowsheets.lsrro import lsrro
stages, rec, cin = int(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3])
QIN = 1e-3
t = time.time(); out = {"stages": stages, "recovery": rec, "cin_g_l": cin, "ok": False}
try:
    with contextlib.redirect_stdout(io.StringIO()):
        m, res = lsrro.run_lsrro_case(stages, water_recovery=rec, Cin=cin, Qin=QIN,
            A_case=lsrro.ACase.fixed, B_case=lsrro.BCase.optimize, AB_tradeoff=lsrro.ABTradeoff.none,
            has_NaCl_solubility_limit=True, has_calculated_concentration_polarization=True,
            has_calculated_ro_pressure_drop=True, permeate_quality_limit=1000e-6, B_max=3.5e-6,
            number_of_RO_finite_elements=10)
    if check_optimal_termination(res):
        c = m.fs.costing
        pumps = list(m.fs.PrimaryPumps.values()) + list(m.fs.BoosterPumps.values())
        out.update(ok=True, LCOW=value(c.LCOW), SEC=value(c.specific_energy_consumption),
            prod_m3_s=value(m.fs.product.properties[0].flow_vol_phase["Liq"]),
            area_m2=sum(value(u.area) for u in m.fs.ROUnits.values()),
            area_hp_m2=value(m.fs.ROUnits[1].area),
            mem_capex=sum(value(u.costing.capital_cost) for u in m.fs.ROUnits.values()),
            mem_opex=sum(value(u.costing.fixed_operating_cost) for u in m.fs.ROUnits.values()),
            pump_capex=sum(value(p.costing.capital_cost) for p in pumps if hasattr(p, "costing")),
            erd_capex=sum(value(e.costing.capital_cost) for e in m.fs.EnergyRecoveryDevices.values() if hasattr(e, "costing")),
            direct_capex=value(c.aggregate_capital_cost), total_opex=value(c.total_operating_cost),
            product_ppm=value(m.fs.product.properties[0].mass_frac_phase_comp["Liq", "NaCl"]) * 1e6,
            brine_g_l=value(m.fs.disposal.properties[0].conc_mass_phase_comp["Liq", "NaCl"]),
            feed_m3_s=QIN,
            pressures_bar=[value(p.control_volume.properties_out[0].pressure) / 1e5 for p in m.fs.PrimaryPumps.values()],
            electricity_price=value(c.electricity_cost), utilization_factor=value(c.utilization_factor),
            TIC=value(c.TIC), capital_recovery_factor=value(c.capital_recovery_factor))
except Exception as e:
    out["error"] = str(e)[:200]
out["seconds"] = round(time.time() - t, 1)
print(json.dumps(out))
