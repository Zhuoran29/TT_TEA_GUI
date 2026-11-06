# GAC Model Documentation

## Scope

Granular activated carbon (GAC) adsorption in downflow steel pressure
contactors, used to remove organics. Bed life comes from the NMSU bed-life
relationship (NMSU assumptions); bed sizing and costs follow the WaterTAP 1.4
GAC costing method, whose cost equations were derived from the US EPA GAC cost
model.

## Using the Model

### Removal efficiencies

Open **Removal efficiencies** for the GAC unit:

| Constituent | Default | Set by |
|---|---|---|
| TOC | 75% | User |
| Oil and grease | 75% | User |
| BTEX | 75% | User |
| Naphthalene | 75% | User |
| Other constituents | 0% | User |

The 75% default is the TOC removal from one NMSU process simulation, applied
to all organics (NMSU assumptions). Removal does not change the bed life; bed
life depends on the inlet TOC (below).

### What the model calculates

- **Bed volume and vessels** from the flow and EBCT.
- **Bed life** (bed volumes and days between carbon changeouts) from the
  inlet TOC.
- **Carbon use**, spent carbon and the share that leaves as solid waste.
- **Electricity** for pumping through the contactors.

### Bed sizing

```text
V_bed    = Q x EBCT / 1440                bed volume in operation (m3), EBCT in min
N_op     = V_bed / 40, rounded up          vessels in parallel (max 40 m3 of bed each)
N_total  = N_op + 1                        one redundant vessel
M        = 400 x V_bed                     fresh carbon in the operating beds (kg)
```

The redundant vessel is costed but not filled with carbon.

### How bed life is determined

```text
BV        = 1.5e5 x TOC_in^-1.85           bed volumes to changeout (TOC in mg/L), limited to 1-150,000
t_change  = BV x EBCT / 1440               days between changeouts
carbon    = M x 365 / t_change             spent carbon (kg/year)
```

At the default EBCT of 10 min:

| Inlet TOC (mg/L) | Bed volumes | Days between changeouts |
|---|---|---|
| 1 | 150,000 (upper limit) | 1,042 |
| 5 | 7,638 | 53 |
| 10 | 2,119 | 15 |
| 30 | 278 | 2 |

A warning appears when inlet TOC is outside 0.4-250 mg/L. High inlet TOC makes
the carbon change very often; pretreatment that lowers TOC ahead of GAC
lengthens bed life sharply.

### Spent carbon

Spent carbon is regenerated off site. The regenerated share (default 80%)
returns to service; the rest leaves as solid waste and is replaced with
makeup carbon. Disposal cost is not included in this unit; the solid-waste
amount is reported for the system level.

### Energy

```text
energy = rho x g x H / pump efficiency / 3.6e6      kWh per m3 feed
```

H is the head through the contactors and piping (default 10 m).

## Cost Model

### Capital

All cost equations are in 2020 dollars and escalated with CEPCI. v is the bed
volume per vessel (m3) and V_total the total contactor volume.

```text
contactors   = N_total x (10010.9 + 2204.95 v - 15.9378 v^2 + 0.110592 v^3)
carbon       = 4.58342 x exp(-1.25311e-5 x min(M, 18,143.7)) x M          initial carbon charge
other        = 16660.7 x V_total^0.552207                                  piping, valves, instrumentation, controls
C_bare       = contactors + carbon + other
C_direct     = TIC x C_bare                                                TIC = 1.15
CAPEX        = IF x C_direct                                               system-level investment factor
```

The EPA equipment costs already include transportation and installation, so
TIC is 1.15; it covers remaining direct items such as site work, yard piping
and electrical.

### Operating

Carbon quantities scale with operating days; maintenance does not.

```text
regeneration = regenerated share x carbon x days/365 x regeneration price
makeup       = (1 - regenerated share) x carbon x days/365 x makeup carbon price
electricity  = energy x Q x days x electricity price
maintenance  = maintenance fraction x C_direct                 includes labor
OPEX         = (1 + O&M contingency) x (regeneration + makeup + electricity + maintenance)
```

The off-site regeneration price includes the regeneration energy.

## Default Inputs

| Input | Default | Basis |
|---|---|---|
| Organics removal | 75% | NMSU assumptions (removal table) |
| EBCT | 10 min | WaterTAP reference design; EPA typical 5-25 min for organics |
| Maximum bed volume per vessel | 40 m3 | EPA vessel limits (14 ft diameter x 14 ft, 50% bed expansion) |
| Redundant vessels | 1 | WaterTAP default |
| Bulk density | 400 kg/m3 | NMSU assumptions |
| Bed-life coefficients | 1.5e5, -1.85 | NMSU assumptions (pilot data) |
| Pump head, efficiency | 10 m, 0.70 | Engineering estimate |
| TIC | 1.15 | Engineering estimate on an installed-cost basis |
| Regenerated share | 0.80 | NMSU assumptions |
| Regeneration price | 4.28352 $/kg (2020 $) | WaterTAP 1.4 GAC costing |
| Makeup carbon price | 4.58223 $/kg (2020 $) | WaterTAP 1.4 GAC costing |
| Maintenance fraction | 0.03 /yr of C_direct, including labor | WaterTAP maintenance-labor-chemical factor |
| O&M contingency | 0.20 of OPEX | NMSU assumptions; Wang et al. 2024 DWPR report |

## Assumptions and Limits

- Single-stage parallel operation; lead-lag (series) operation is not modeled.
- The bed-life relationship was fitted to limited pilot data; bed life outside
  the fitted TOC range, and its dependence on EBCT, are not captured.
- Removal is a fixed fraction per constituent and is not linked to bed life.
- Steel pressure contactors only; gravity basins are not included.
- Spent carbon is assumed regenerable. Carbon from produced water may carry
  NORM or metals that rule out regeneration.

## Sources

- NMSU assumptions: bed-life relationship fitted to pilot data, default
  removal and regenerated share.
- WaterTAP 1.4 GAC unit model and costing method,
  https://watertap.readthedocs.io/en/1.4.0/technical_reference/costing/gac.html
- US EPA 2021. Work Breakdown Structure-Based Cost Model for Granular Activated
  Carbon Drinking Water Treatment.
- Lugo et al. 2025, Journal of Environmental Chemical Engineering 13, 117026.
- Wang et al. 2024 DWPR report (O&M contingency).
