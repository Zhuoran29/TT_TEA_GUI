# Zeolite Model Documentation

## Scope

Fixed-bed zeolite (clinoptilolite) ion exchange for NH3-N polishing after
desalination. NH4+ is exchanged onto the zeolite and the bed is regenerated
in place with brine. Because the unit treats desalinated water, competing
cations (Na+, K+, Ca2+) are low and no competition correction is applied.
Bed life comes from a bench column breakthrough curve (NMSU assumptions);
capital and maintenance use the same unit-level TIC and system-level
investment-factor structure as the other units.

## Technical Model

### Water quality

NH3-N removal is read from the unit's removal-efficiency table (default 95%)
and also sets the breakthrough point on the bench curve. Other constituents
use the same table.

### Bench breakthrough curve

Bench test: KMI zeolite 14x30, single upflow column, EBCT 20 min, 8.24 g in a
10 mL bed (bulk density 824 kg/m3), feed about 25 mg/L NH3-N, regenerated with
10% NaCl. Cycle 1 of the test is used:

| BV | Removal |
|---|---|
| 0-391 | 100% |
| 482 | 99.8% |
| 559 | 89.4% |
| 724 | 37.2% |
| 1,244 | 0% |

```text
BV_bench   = BV on cycle 1 where removal falls to the target (linear interpolation)
           = 517.6 BV at 95% removal
```

A 100% target returns the last BV still at 100% removal (390.7 BV).

### Scaling to the inlet water

```text
BV         = BV_bench x C_bench / C_in        C_bench = 24.38 mg/L (cycle-1 mean)
t_service  = BV x EBCT / 1440                 service time between regenerations (days)
n_cycles   = 365 / t_service                  regenerations per year (continuous operation)
V_bed      = Q x EBCT / 1440                  bed volume (m3)
M_bed      = 824 x V_bed                      zeolite inventory (kg, reported)
N_removed  = Q x (C_in - C_out) / 1000        kg N/day
```

The scaling holds the NH3-N mass loaded per bed volume constant, so a more
dilute feed gives proportionally more bed volumes. A warning appears when
feed NH3-N is above 30 mg/L (outside the bench range).

### Regeneration

The bed is regenerated in place with the bench procedure: a 10% NaCl brine
at pH 11, 0.9 L per 10 mL bed (90 bed volumes), reused for 5 regenerations.
Na+ displaces NH4+ from the zeolite; NaOH holds the brine at pH 11 so the
eluted NH4+ converts to NH3, which keeps the exchange driving force high and
lets the brine be reused.

```text
V_brine    = BV_regen x V_bed / n_reuse        fresh brine per regeneration (m3)
rho_brine  = 997 + 735 x w_NaCl                brine density (kg/m3)
NaCl       = V_brine x rho_brine x w_NaCl x n_cycles                 kg/year
NaOH       = N_removed x 365 / 14.007 x r_OH x 39.997                kg/year
brine      = V_brine x n_cycles                spent brine (m3/year, reported)
```

r_OH is the NaOH added per mole of NH4-N eluted. The default of 1 is an
engineering estimate: each NH4+ eluted at pH 11 is converted to NH3 and
consumes one OH-. Set it to 0 for neutral (pH 7) regeneration.

### Media replacement and solid waste

```text
M_AEC      = N_removed x t_service x 1000 / AEC    zeolite mass loaded per cycle (kg)
replaced   = M_AEC x f_replace x n_cycles          kg/year, reported as spent zeolite
```

AEC is the ammonium exchange capacity in mg N per g zeolite (default 4.0,
Deng et al. 2014 range 2.5-21.5). The default replacement fraction is 0
because the media is regenerated in place.

### Energy

```text
energy_intensity = rho x g x H / eta / 3.6e6   kWh per m3 feed
pump_power       = energy_intensity x Q / 24   kW
```

H is the total dynamic head through the contactors and piping and eta the
pump efficiency, as for GAC.

## Cost Model

### Capital

```text
C_bare    = 3305.1 x Q^0.6961 x CEPCI_base / CEPCI_2021     Q = inlet flow (m3/day)
C_direct  = TIC x C_bare                                    unit-level installation factor
CAPEX     = IF x C_direct                                   system-level investment factor
```

The cost curve was fitted to the US EPA WBS Cation Exchange model (March 2023
release, 2021 dollars) run with zeolite settings at the EPA standard design
flows 0.124, 0.305, 0.740, 2.152, 7.365 and 22.614 MGD (470-85,600 m3/day):

- EBCT 20 min; bed volumes between regenerations about 2,000.
- Minimum surface loading lowered from 5 to 1 gpm/ft2 so that 20-min beds
  can be autosized; all other EPA defaults kept (pressure vessels, piping,
  valves, instrumentation, brine and backwash tanks, building).
- Vessels autosized by the model at each flow.
- The resin line is removed, so the initial zeolite charge is not costed.

| Design flow (MGD) | Direct cost excl. media (2021 $) | Fit error |
|---|---|---|
| 0.124 | 224,019 | +7% |
| 0.305 | 480,668 | -7% |
| 0.740 | 747,692 | +11% |
| 2.152 | 2,068,757 | -16% |
| 7.365 | 4,072,659 | +1% |
| 22.614 | 8,416,825 | +7% |

EPA direct costs already include transportation and installation, so the
default TIC is 1.15 (same basis as GAC). In these runs EPA's own total
capital was 1.46-1.57 times its direct cost.

### Operating

```text
C_elec    = energy_intensity x Q x days x electricity price
C_chem    = (NaCl x c_NaCl + NaOH x c_NaOH) x days / 365
C_media   = replaced x days / 365 x c_zeolite
C_maint   = f_maint x C_direct
OPEX      = (1 + f_cont) x (C_elec + C_chem + C_media + C_maint)
```
Spent-brine disposal is left to the system level; the model reports the
brine volume.

## Default Inputs

| Input | Default | Basis |
|---|---|---|
| Recovery | 0.995 | NMSU assumptions |
| EBCT | 20 min | NMSU assumptions (bench test); Turan and Turan 2021 |
| Brine per regeneration | 90 bed volumes | NMSU assumptions (bench: 0.9 L per 10 mL bed) |
| Brine reuse | 5 regenerations | NMSU assumptions (bench) |
| NaCl in brine | 10% by mass | NMSU assumptions (bench) |
| NaOH to NH4-N | 1 mol/mol | Engineering estimate: stoichiometric OH- to keep pH 11 as NH4+ is eluted |
| AEC | 4.0 mg N/g | NMSU assumptions; Deng et al. 2014 (2.5-21.5) |
| Pump head, efficiency | 10 m, 0.70 | Engineering estimate (same as GAC) |
| Zeolite price | 4.41 $/kg (2014 $) | NMSU assumptions (bench vendor price); Deng et al. 2014 |
| Media replacement | 0 per cycle | NMSU assumptions (regenerated in place) |
| NaCl price | 40 $/t (2014 $) | Deng et al. 2014 |
| NaOH price | 300 $/t (2014 $) | Deng et al. 2014 |
| Equipment cost curve | 3305.1 x Q^0.6961 (2021 $) | US EPA WBS Cation Exchange model, zeolite settings |
| TIC | 1.15 | Engineering estimate on an installed-cost basis |
| Maintenance fraction | 0.02 /yr of C_direct | NMSU assumptions |
| O&M contingency | 0.20 | NMSU assumptions; Wang et al. 2024 DWPR report |

## Assumptions and Limits

- Bed life comes from one bench column, cycle 1 only; cycle 2 after
  regeneration ran longer, so cycle 1 is conservative.
- BV scales inversely with feed NH3-N (constant mass loading); isotherm
  effects at low concentration are not captured.
- Intended for post-treatment of desalinated water with low competing cations.
- The bench brine volume (90 bed volumes) is high for full scale; EPA's
  cation-exchange design basis (15 lb NaCl per ft3 of media) uses roughly
  eight times less salt.
- Spent-brine disposal and NH4Cl recovery are not included.
- The cost curve is for EBCT 20 min; changing EBCT changes bed life but not
  capital cost. It was fitted to design flow; the app applies it to the
  unit inlet flow.

## Sources

- NMSU assumptions: bench zeolite column test (KMI zeolite 14x30, EBCT 20 min,
  10% NaCl regeneration) and TEA cost assumptions.
- Koon, J.H., Kaufman, W.J. Optimization of Ammonia Removal by Ion Exchange
  Using Clinoptilolite. US EPA Water Pollution Control Research Series,
  Report 17080 (1972); UC Berkeley Sanitary Engineering Research Laboratory
  (1971).
- Turan and Turan 2021, Water Science & Technology, DOI 10.2166/wst.2021.468.
- Deng, Q., Dhar, B.R., Elbeshbishy, E., Lee, H.-S. 2014. Ammonium nitrogen
  removal from the permeates of anaerobic membrane bioreactors: economic
  regeneration of exhausted zeolite. Environmental Technology 35, 2008-2017.
  DOI 10.1080/09593330.2014.889759.
- US EPA 2023. Work Breakdown Structure (WBS) Model for Cation Exchange System
  Treatment (Excel model, release March 2023, 2021 dollars) and model
  documentation. Drinking Water Treatment Technology Unit Cost Models.
- Wang et al. 2024 DWPR report (O&M contingency).
