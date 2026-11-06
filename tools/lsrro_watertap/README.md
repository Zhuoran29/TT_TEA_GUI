# LSRRO lookup table from WaterTAP

These scripts generate `lsrro_table.csv`, the design table the LSRRO unit model reads. Each row is
one feasible WaterTAP LSRRO design at a feed TDS, recovery and stage count. `lowest_lcow = 1` marks the
lowest-LCOW design at each grid point. The app interpolates between designs with the same stage count.

## Environment

The app does not need WaterTAP. It is only needed to regenerate the table.

```bash
python -m venv venv
./venv/bin/pip install watertap==1.8.0      # installs idaes-pse 2.13 and pyomo 6.10
./venv/bin/idaes get-extensions             # Ipopt and the IDAES solver binaries
```

## Running

```bash
./venv/bin/python generate_table.py                               # full grid (resumable)
./venv/bin/python generate_table.py --tds 20 40 60 --raw a        # part of the grid
./venv/bin/python generate_table.py --build-table                 # write lsrro_table.csv
./venv/bin/python solve_point.py 3 0.378 108                      # one design: stages, recovery, TDS
```

Each solve takes about 15-200 s. Run grid parts in parallel with different `--raw` names. All
attempts, including failed solves, are kept in `raw_<name>.jsonl`, and an interrupted run resumes
from them.

## Method

- **Flowsheet:** `watertap.flowsheets.lsrro`, as in Atia et al. 2023. The settings are:
  - A fixed at 4.2e-12 m/s-Pa; B optimized per stage up to 3.5e-6 m/s.
  - NaCl solubility limit, calculated concentration polarization and pressure drop.
  - 1D RO with 10 elements.
  - Product limit 1,000 ppm.
  - Maximum pressure 85 bar in the first stage and 65 bar in the LSR stages (WaterTAP defaults).
  - These settings reproduce the published optima: 35 g/L, 70% recovery gives LCOW 0.71 $/m3 and
    SEC 3.9 kWh/m3.
- **Feed flow:** all cases are solved at the WaterTAP default feed flow of 1e-3 m3/s. WaterTAP sizes
  and costs LSRRO linearly with flow, so the per-flow results do not depend on the flow.
  - Solving at large flows needs re-tuned scaling factors and can fail (120 g/L at 0.092 m3/s did).
  - At 35 g/L, 0.092 m3/s gave the same SEC and LCOW as 1e-3 m3/s.
- **Grid:** TDS 20-150 g/L in 10 g/L steps × recovery 0.20-0.70 in 0.05 steps.
  - Points whose brine would exceed 320 g/L (NaCl solubility) are skipped.
- **Stage search:** stage counts from 1 to 8 are tried in order; the search stops when an added stage
  raises the LCOW. Failed solves are left out of the table.
- **Costs** are WaterTAP 2018 dollars with WaterTAP unit prices:
  - Membranes: 30 $/m2 in the first (RO) stage, 50 $/m2 in the LSR stages (WaterTAP "high-pressure"
    membrane cost); replacement 0.15 /yr of membrane cost.
  - WaterTAP applies TIC = 2 to unit capital costs; the table divides it out (equipment cost).
  - High-pressure pumps: 1.908 $/W.
  - Pressure exchanger: 535 $/(m3/h).
  - The app escalates these with CEPCI and applies its own installation, investment, financing and
    O&M factors. The WaterTAP LCOW column (TIC 2, CRF 0.10, 0.07 $/kWh, utilization 0.9) is kept
    for reference only.

## Table columns

| Column | Unit |
|---|---|
| feed_tds_g_l, recovery, stages | g/L NaCl, fraction, count |
| sec_kwh_m3_product, sec_kwh_m3_feed | kWh/m3 (net of energy recovery) |
| membrane_area_m2_per_m3d_product, first_stage_area_m2_per_m3d_product | m2 per m3/day product |
| membrane_capex_usd_per_m3d_feed, pump_capex_usd_per_m3d_feed, erd_capex_usd_per_m3d_feed, equipment_capex_usd_per_m3d_feed | 2018 $ per m3/day feed, equipment cost without the WaterTAP TIC of 2 |
| membrane_replacement_usd_yr_per_m3d_feed | 2018 $/yr per m3/day feed |
| watertap_lcow_usd_m3_product | 2018 $/m3 product (WaterTAP basis) |
| product_nacl_ppm, brine_g_l | mg/kg, g/L |
| lowest_lcow | 1 for the lowest-LCOW design at the grid point, else 0 |

## Sources

- Atia, A. A. et al. 2023. Cost optimization of low-salt-rejection reverse osmosis. Desalination.
  https://www.osti.gov/biblio/1963953
- WaterTAP LSRRO flowsheet:
  https://watertap.readthedocs.io/en/stable/technical_reference/flowsheets/lsrro.html
- WaterTAP reverse osmosis costing:
  https://watertap.readthedocs.io/en/1.5.0/technical_reference/costing/reverse_osmosis.html
