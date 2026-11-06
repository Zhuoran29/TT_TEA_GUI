# LSRRO Model Documentation

## Scope

Low-salt-rejection reverse osmosis (LSRRO) for hypersaline produced water. The first stage is a
conventional high-pressure RO stage. The following low-salt-rejection stages partly desalinate the
concentrate and recycle their permeate, so brines above the osmotic limit of conventional RO can be
concentrated with pressures of 65-85 bar.

The model combines three parts:
- the NMSU recovery correlation;
- a design table generated with the WaterTAP LSRRO flowsheet (energy, design and equipment costs);
- the NMSU permeate water-quality model.

## Using the Model

### Inputs

| Input | Default | Set by |
|---|---|---|
| Recovery | 0 (uses the recovery correlation) | User; a positive value overrides the correlation |
| Clip negative permeate | 1 | User |

Feed TDS, hardness and silica come from the train stream.

### What the model calculates

- **Recovery** from the correlation, or the user value.
- **Specific energy consumption**, **stage count** and **membrane area** from the WaterTAP design
  table at the feed TDS and recovery.
- **Permeate and brine quality**.
- **Costs**.

### Recovery

```text
R (%) = -0.0002 TDS^2 - 0.3816 TDS + 84.01 - 3.69e-4 Hardness - 1e-4 Silica      TDS in g/L
```

- The first three terms are a fit (R² 0.997) to WaterTAP PBSE design points between 20 and 130 g/L.
- The hardness (mg/L as CaCO3) and silica (mg/L) terms are the NMSU correction for scaling ions and
  chemical addition.
- The result is limited to 1-90%.

### WaterTAP design table

`data/model_tables/lsrro_watertap_table.csv` holds WaterTAP LSRRO designs at feed TDS 20-150 g/L and
recovery 20-70%, with 1 to 8 stages. Each grid point has the lowest-LCOW design and the other stage
counts tried there.

The model interpolates linearly in TDS and recovery between designs with the same stage count:
- Only stage counts that are feasible at all neighboring grid points are considered.
- Of these, the stage count with the lowest interpolated WaterTAP LCOW is used.
- The reported stage count is therefore a whole number, and the design is a real WaterTAP design
  family. At low TDS a single stage reaches the 85 bar pump limit, so two stages are used between a
  feasible one-stage point and an infeasible one.

At the NAWI manuscript cases (90 g/L at 47%, 108 g/L at 38%, 135 g/L at 24%), the interpolated stage
count matches direct WaterTAP solves, and the SEC and equipment cost are within 3%.

| Quantity | Basis |
|---|---|
| SEC | kWh/m3 product, net of energy recovery |
| Stage count, membrane area | per m3/day product |
| Membrane, pump and energy recovery device equipment cost | 2018 $ per m3/day feed, without the WaterTAP TIC |
| Membrane replacement | 2018 $/yr per m3/day feed (WaterTAP: 15%/yr of membrane cost) |

A point outside the table is moved to the nearest table point, with a warning:
- a feed TDS below 20 g/L or above 150 g/L;
- a recovery outside the feasible range at that TDS. At high TDS the brine reaches NaCl saturation,
  so the highest feasible recovery falls as the TDS rises.

The table and the scripts that generate it are in `tools/lsrro_watertap/` (see its README).

### Energy

```text
energy = SEC (TDS, R) x R          kWh/m3 feed
```

### Permeate quality

- **Regressions on feed concentration:** chloride, calcium, alkalinity, ammonia nitrogen and BTEX:
  `Cp = a + b Cf + c Cf^2`.
- **Average pilot removals:** TDS 99.40%, hardness 99.41%, sodium 99.24%, boron 98.11%, TOC 91.55%,
  ammonia 98.38% (used when its regression is negative), and the other tracked constituents.
- Negative regression results are set to zero.
- The brine quality follows from the mass balance.

## Cost Model

### Capital

```text
c_eq      = membrane + pump + ERD equipment cost per m3/day feed        design table, 2018 $
C_bare    = c_eq x CEPCI factor x Q_ref x (Q / Q_ref)^0.81              Q_ref = 7,949 m3/day (50,000 bbl/day)
C_direct  = TIC x C_bare                                                TIC = 2 (WaterTAP)
CAPEX     = IF x C_direct                                               system-level investment factor
```

The WaterTAP unit prices behind the table are:
- membranes: 30 $/m2 in the first stage and 50 $/m2 in the LSR stages;
- high-pressure pumps: 1.908 $/W;
- pressure exchangers: 535 $/(m3/h);
- all in 2018 dollars.

Pumps are about two thirds of the equipment cost.

### Operating

```text
electricity = energy x Q x days x electricity price
membranes   = membrane replacement per m3/day feed x CEPCI factor x Q
maintenance = maintenance fraction x C_direct                           includes labor
antiscalant = dose x Q x days / density x price
CIP         = CIP rate x permeate
OPEX        = (1 + O&M contingency) x (electricity + membranes + maintenance + antiscalant + CIP)
```

The brine is reported for the system-level waste stream. Its disposal cost is not included in this
unit.

## Default Inputs

| Input | Default | Basis |
|---|---|---|
| Recovery | correlation | NMSU assumptions (SI Eq. B5-1) |
| Design table | WaterTAP 1.8.0 LSRRO flowsheet | Atia et al. 2023 settings (see tools/lsrro_watertap) |
| Reference flow | 7,949 m3/day | NMSU assumptions (50,000 bbl/day) |
| Scaling exponent | 0.81 | NMSU assumptions (SI Eq. B5-2) |
| TIC | 2 | WaterTAP LSRRO costing |
| Maintenance fraction | 0.02 /yr of C_direct, including labor | NMSU assumptions |
| Antiscalant | 3 mg/L at 61.40 $/gal, 1.10 kg/L | NMSU assumptions; Applied Membranes product information |
| CIP | 0.07 $/m3 product (2021 $) | Jafari et al. 2021 |
| O&M contingency | 0.20 of OPEX | NMSU assumptions; Wang et al. 2024 DWPR report |

## Assumptions and Limits

- **NaCl only.** The WaterTAP design is for NaCl solutions. Scaling ions affect only the recovery,
  through the hardness and silica correction.
- **Optimized designs.** WaterTAP optimizes the salt permeability of each stage and the stage count,
  so the costs are close to a lower bound for a well-designed plant.
- **Design table settings.** The product limit is 1,000 ppm NaCl. The permeate quality used by the
  train comes from the NMSU water-quality model, not from WaterTAP.
- **Regressions.** The water-quality regressions were fit to pilot feed and permeate pairs. They can
  give values that are not physical outside the fitted range. For example, calcium is zero for feeds
  of 600-3,100 mg/L.
- **Antiscalant.** Antiscalant is costed in this unit. When an antiscalant dosing unit is also in the
  train, set the dose here to zero.

## Sources

- NMSU assumptions: NMSU LSRRO model (recovery correlation, water-quality model, scaling exponent).
- Atia, A. A. et al. 2023. Cost optimization of low-salt-rejection reverse osmosis. Desalination.
  https://www.osti.gov/biblio/1963953
- WaterTAP LSRRO flowsheet and reverse osmosis costing (WaterTAP 1.8.0).
- Jafari et al. 2021 (CIP cost).
- Wang et al. 2024 DWPR report (O&M contingency).
