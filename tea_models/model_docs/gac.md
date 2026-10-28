# GAC Model Documentation

## Scope

Granular activated carbon (GAC) adsorption in downflow steel pressure
contactors. The unit treats the inlet stream passed from upstream units.
Bed life comes from the NMSU empirical bed-volume model; bed sizing, capital
cost, carbon replacement and maintenance follow the WaterTAP 1.4 GAC costing
method, whose capital correlations were regressed from the US EPA Work
Breakdown Structure (WBS) GAC cost model.

## Technical Model

### Water quality

Constituent removal comes from the removal-efficiency table. The default for
TOC, oil, BTEX and PAHs is the removal from one WaterTAP CPHSDM run (NMSU
assumption):

```text
R = 1 - 0.28773 / 1.15 = 0.7498
```

### Bed sizing

```text
V_bed      = Q x EBCT                      bed volume of operating vessels (m3)
N_op       = ceil(V_bed / V_max)           operating vessels in parallel
v          = V_bed / N_op                  bed volume per vessel (m3)
N_total    = N_op + N_redundant
V_total    = N_total x v                   total contactor volume (m3)
M          = rho_b x V_bed                 fresh GAC mass in operating beds (kg)
```

Q is the GAC inlet flow (m3/day, with EBCT in days). Redundant vessels are
costed as contactors but are not charged with carbon (WaterTAP convention).

### Bed life (NMSU empirical model)

```text
BV         = A x TOC_in^b                  bed volumes to changeout, 1 <= BV <= 150,000
t_change   = BV x EBCT                     changeout interval (days)
usage      = M x 365 / t_change            spent GAC (kg/year, continuous operation)
CUR        = rho_b / BV                    carbon usage rate (kg per m3 treated)
```

Defaults are A = 1.5e5 and b = -1.85 (TOC in mg/L). Carbon use per m3 treated
depends only on BV and bulk density, not on bed size. A warning appears when
feed TOC is outside 0.4-250 mg/L.

### Pump energy

```text
energy_intensity = rho x g x H / eta / 3.6e6     kWh per m3 feed
pump_power       = energy_intensity x Q / 24     kW
```

H is the total dynamic head through the contactors and piping and eta the
pump wire-to-water efficiency. This is the same flow-head-efficiency method
the EPA WBS models use for booster pumps.

### Solid waste

```text
spent GAC generated     = usage                         (technical output)
spent GAC to solid waste = (1 - f_regen) x usage x days/365   (cost output)
```

Disposal cost is not included in this unit; it is left to the system level.

## Cost Model

### Capital

All correlations are in USD_2020 and are escalated to the project base year
with CEPCI.

```text
C_contactor = N_total x (10010.9 + 2204.95 v - 15.9378 v^2 + 0.110592 v^3)
c_GAC       = 4.58342 x exp(-1.25311e-5 x min(M, 18,143.7))      USD/kg
C_GAC       = c_GAC x M                                         initial carbon charge
C_other     = 16660.7 x V_total^0.552207                        piping, valves, instrumentation, controls
C_bare      = C_contactor + C_GAC + C_other
C_direct    = TIC x C_bare                                      unit-level installation factor
CAPEX       = IF x C_direct                                     system-level investment factor
```

The EPA WBS equipment costs already include transportation and installation,
so the default TIC is 1.15; it covers direct items such as site work, yard
piping and electrical that the EPA model treats separately. IF is the
system-level investment factor shared by all units.

### Operating

Carbon quantities scale with operating days; maintenance does not.

```text
usage_op     = usage x days / 365
C_regen      = f_regen x usage_op x c_regen
C_makeup     = (1 - f_regen) x usage_op x c_makeup
C_elec       = energy_intensity x Q x days x electricity price
C_maint      = f_maint x C_direct
OPEX         = (1 + f_cont) x (C_regen + C_makeup + C_elec + C_maint)
```

Regeneration is off site; its unit cost includes the regeneration energy, so
no separate regeneration electricity is charged.

## Default Inputs

| Input | Default | Basis |
|---|---|---|
| EBCT | 10 min (600 s) | WaterTAP reference design; EPA WBS typical 5-25 min for organics |
| Maximum bed volume per vessel | 40 m3 | EPA WBS vertical vessels up to 14 ft diameter x 14 ft, 50% bed expansion |
| Redundant vessels | 1 | WaterTAP GAC costing default |
| Bulk density | 400 kg/m3 | WaterTAP reference design and NMSU assumptions |
| BV coefficients A, b | 1.5e5, -1.85 | NMSU assumptions (fit to pilot data) |
| Pump head, efficiency | 10 m, 0.70 | Engineering estimate |
| TIC | 1.15 | Engineering estimate on an installed-cost basis |
| Regeneration fraction | 0.80 | NMSU assumptions (WaterTAP default 0.70; EPA off-site makeup 30%/yr) |
| Regeneration cost | 4.28352 USD_2020/kg | WaterTAP 1.4 GAC costing |
| Makeup GAC cost | 4.58223 USD_2020/kg | WaterTAP 1.4 GAC costing |
| Maintenance fraction | 0.03 /yr of C_direct | WaterTAP maintenance-labor-chemical factor |
| O&M contingency | 0.20 | NMSU assumptions; Wang et al. 2024 DWPR report |

## Assumptions and Limits

- Single-stage parallel operation; lead-lag (series) operation is not modeled.
- The BV law was fitted to two pilot points; bed life outside the fitted TOC
  range, and its dependence on EBCT, are not captured.
- Removal is a fixed fraction per constituent and is not linked to bed life.
- Steel pressure contactors only; gravity basins are not included.
- Spent GAC is assumed regenerable. GAC from produced water may carry NORM or
  metals, which can rule out regeneration (EPA WBS lists radioactive and
  hazardous disposal options).

## Sources

- WaterTAP 1.4 GAC unit model and costing method,
  https://watertap.readthedocs.io/en/1.4.0/technical_reference/costing/gac.html
- US EPA 2021, Work Breakdown Structure-Based Cost Model for Granular Activated
  Carbon Drinking Water Treatment.
- NMSU assumptions: empirical bed-life model fitted to pilot BV data, default
  removal fraction and spent-GAC regeneration split.
- Lugo et al. 2025, Journal of Environmental Chemical Engineering 13, 117026.
- Wang et al. 2024 DWPR report (O&M contingency).
