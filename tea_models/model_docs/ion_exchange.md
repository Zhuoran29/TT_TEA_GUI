# Ion Exchange Model Documentation

## Scope

Selective ion exchange (IX) for post-treatment, used to bring specific
constituents to their limits. The resins are regenerated with NaCl:

- **Cation bed**: Na-form strong acid cation (SAC) resin, a softener. It
  removes hardness, calcium, magnesium, barium, strontium, manganese and
  radium, and releases Na+ in exchange.
- **Anion bed**: Cl-form strong base anion (SBA) resin. It removes sulfate,
  alkalinity (bicarbonate), arsenic, selenium and uranium, and releases Cl- in
  exchange.

Because each removed ion is exchanged for Na+ or Cl-, selective IX does not
lower TDS, sodium or chloride. To remove those, use **Ion exchange
(demineralization)** or BWRO. Sizing and regeneration follow the US EPA WBS
cation exchange and anion exchange models.

## Using the Model

### Removal efficiencies

The targets entered in **Removal efficiencies** decide which beds are built:

| Constituent | Default | Bed |
|---|---|---|
| Hardness, calcium, magnesium, barium, strontium, manganese | 95% | Cation |
| Radium-226, radium-228, gross alpha | 95% | Cation |
| Sulfate | 0% | Anion |
| Alkalinity, bicarbonate | 0% | Anion |
| Arsenic, selenium, uranium | 0% | Anion |
| Sodium, chloride, TDS, conductivity, boron, ammonia, fluoride, silica, lithium | not removed | |

- A bed is built when any of its constituents has a removal above 0. Set all
  cation entries to 0 for an anion-only unit.
- All constituents of a bed are removed at the same fraction, the largest
  value entered for that bed. For example, the cation resin takes up all
  divalent cations together, so calcium cannot be removed at 95% while
  magnesium passes.
- In the anion bed, sulfate is always removed, because the resin prefers it
  to the other anions. Alkalinity is removed only when it is a target.
- An entry for a constituent that selective IX does not remove is ignored,
  and a warning is shown.

### What the model calculates

- **Treated fraction and bypass** for each bed.
- **Run length** (bed volumes between regenerations) from the resin capacity
  and the ionic load.
- **NaCl use** and the **spent regenerant** volume, which sets the water
  recovery.
- **Product water**: removed ions, plus the Na+ and Cl- released.
- **Spent regenerant quality**, by mass balance.
- **Resin volume**, **electricity** for pumping, and costs.

### Treated fraction and bypass

Water passing through a bed loses 99% of the bed's target ions (bed removal,
an input). A lower removal is met by sending only part of the flow through
the bed and blending the rest back:

```text
f      = removal / bed removal          treated fraction (at most 1)
Q_bed  = f x Q
V_bed  = Q_bed x EBCT / 1440            resin volume (m3); EBCT 2.5 min cation, 2.0 min anion
```

At the default 95% removal, f = 0.96.

### Ionic load and run length

```text
cation load = max(Ca/20.04 + Mg/12.15, hardness/50.04) + Ba/68.66 + Sr/43.81 + Mn/27.47      meq/L
anion load  = SO4/48.03 + max(HCO3/61.02, alkalinity/50.04) [only when alkalinity is a target]   meq/L
BV          = min(1000 x capacity / (bed removal x load), BV_max)                           bed volumes per cycle
t_cycle     = BV x EBCT / 1440                                                              days
```

| Bed | Capacity | BV_max |
|---|---|---|
| Cation (SAC, Na form) | 1.24 eq/L resin at 240 g NaCl/L | 1,000 |
| Anion (SBA, Cl form) | 0.8 eq/L resin at 128 g NaCl/L | 3,000 |

A warning is shown when the run length reaches BV_max before the capacity is
used, and when the bed is exhausted in fewer than 50 bed volumes, which means
the load is too high for IX.

### Product water

```text
removed ions        x (1 - removal)
Na added            = cation removal x cation load x 22.99           mg/L
Cl added            = anion removal x anion load x 35.45             mg/L
TDS                 = TDS_in - removed ion mass + Na added + Cl added
conductivity        scaled with TDS
```

For example, softening water with 250 mg/L hardness (as CaCO3, all calcium)
at 95% adds about 109 mg/L Na and raises TDS by about 14 mg/L.

### Regeneration and recovery

Each regeneration uses the regenerant dose, then a slow and fast rinse and a
backwash:

```text
NaCl          = dose x V_bed x cycles per year                     kg/year
waste per cycle = dose / regenerant concentration + rinse + backwash   bed volumes
spent regenerant = waste per cycle x V_bed x cycles per year          m3/year
recovery      = 1 - spent regenerant / feed
```

| Bed | Dose | Concentration | Regenerant | Rinse | Backwash | Waste per cycle |
|---|---|---|---|---|---|---|
| Cation | 240 g/L | 108 g/L | 2.2 BV | 12 BV | 3.0 BV | 17.2 BV |
| Anion | 128 g/L | 60 g/L | 2.1 BV | 7 BV | 1.2 BV | 10.3 BV |

At the EPA design point the cation bed uses 3.3 times the stoichiometric NaCl
(194 g NaCl per equivalent removed). When the run length is capped at BV_max,
the full dose is still applied, so the NaCl per equivalent is higher.

The spent regenerant carries the removed ions and the excess NaCl. It is
reported for the system-level waste stream; its disposal cost is not included
in this unit.

### Energy

```text
energy = rho x g x H / pump efficiency / 3.6e6 x f       kWh per m3 feed
```

H is the head through the beds and piping (default 10 m), as for GAC and
zeolite.

## Cost Model

### Capital

```text
C_bed     = a x Q_bed^b                    2021 dollars, escalated with CEPCI; excludes resin
C_resin   = V_bed x resin price
C_direct  = TIC x (C_bed + C_resin)        summed over the beds; TIC = 1.15
CAPEX     = IF x C_direct                  system-level investment factor
```

| Bed | a | b |
|---|---|---|
| Cation | 698.35 | 0.7478 |
| Anion | 673.45 | 0.7282 |

The curves come from the EPA cation and anion exchange models, run at NMSU
for standard designs 2-7 (0.124-22.6 MGD) with automatic vessel sizing:
- **Cation**: SAC resin, EBCT 2.5 min.
- **Anion**: nitrate standard designs with SBA Type I gel resin, EBCT 2.0 min.

They cover pressure vessels, piping, valves, instrumentation, brine and
backwash tanks and building. The fit is within 30% (cation) and 34% (anion).
The largest deviations are around 1 MGD, where the EPA models switch from
small-system to medium-system components.

### Operating

```text
NaCl        = NaCl use x days / 365 x salt price
resin       = sum of V_bed x resin price x (1 / resin life + annual loss)
electricity = energy x Q x days x electricity price
maintenance = maintenance fraction x C_direct           includes labor
OPEX        = (1 + O&M contingency) x (NaCl + resin + electricity + maintenance)
```

## Default Inputs

| Input | Default | Basis |
|---|---|---|
| Target removal | 95% (cation constituents) | NMSU assumptions |
| Bed removal | 0.99 | NMSU assumptions |
| Cation EBCT | 2.5 min | EPA cation exchange model |
| Cation capacity | 1.24 eq/L (27 kgr/ft3) | EPA cation exchange model |
| Cation NaCl dose | 240 g/L (15 lb/ft3) | EPA cation exchange model |
| Cation brine concentration | 108 g/L (0.9 lb/gal) | EPA cation exchange model |
| Cation rinse, backwash | 12 BV, 3.0 BV | EPA cation exchange model |
| Cation BV_max | 1,000 | EPA cation exchange model (100-1,000 BV) |
| Anion EBCT | 2.0 min | EPA anion exchange model |
| Anion capacity | 0.8 eq/L | EPA anion exchange model: bed life BV = -606 ln(SO4) + 3150 (Chen et al. 1999) gives 0.75-0.81 eq/L at 50-100 mg/L sulfate |
| Anion NaCl dose | 128 g/L (8 lb/ft3) | EPA anion exchange model |
| Anion brine concentration | 60 g/L (0.5 lb/gal) | EPA anion exchange model |
| Anion rinse, backwash | 7 BV, 1.2 BV | EPA anion exchange model |
| Anion BV_max | 3,000 | EPA anion exchange model (300-3,000 BV) |
| Pump head, efficiency | 10 m, 0.70 | Engineering estimate (same as GAC and zeolite) |
| Cost curves | see above (2021 $) | EPA cation and anion exchange models |
| TIC | 1.15 | Same basis as GAC and zeolite |
| Cation resin price | 8,175 $/m3 (231 $/ft3, 2021 $) | EPA cost data, SAC macroporous |
| Anion resin price | 8,198 $/m3 (232 $/ft3, 2021 $) | EPA cost data, SBA Type I gel |
| Resin life, annual loss | 7 years, 4.5% | EPA cation and anion exchange models |
| NaCl price | 230 $/t (2021 $) | EPA cost data, large quantity |
| Maintenance fraction | 0.02 /yr of C_direct, including labor | NMSU assumptions (same as zeolite) |
| O&M contingency | 0.20 of OPEX | NMSU assumptions; Wang et al. 2024 DWPR report |

## Assumptions and Limits

- Removal is a fixed fraction; leakage, breakthrough curves and competition
  between ions within a bed are not modeled.
- The cation bed counts only divalent cations in its load. Monovalent cations
  (K+, NH4+) are close to Na+ in selectivity and are not removed.
- The anion capacity is derived from the EPA bed-life relation for sulfate,
  which was developed for Type II resin in drinking water.
- High feed sodium reduces softener capacity and raises hardness leakage. The
  model is meant for low-TDS water after desalination.
- The cost curves are for the EPA default EBCTs. Changing the EBCT changes
  the resin volume and resin cost, but not the vessel cost.
- Spent-regenerant disposal is not included in this unit.

## Sources

- US EPA 2023. Work Breakdown Structure (WBS) Model for Cation Exchange
  Treatment, and Work Breakdown Structure (WBS) Model for Anion Exchange
  Treatment (2021 dollars). Drinking Water Treatment Technology Unit Cost
  Models. Workbooks and documentation; standard designs rerun at NMSU for the
  cost curves.
- Chen et al. 1999, as cited in the EPA anion exchange model documentation
  (sulfate bed-life relation).
- Wang et al. 2024 DWPR report (O&M contingency).
