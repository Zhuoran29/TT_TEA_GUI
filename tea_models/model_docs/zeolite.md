# Zeolite Model Documentation

## Scope

Fixed-bed zeolite (clinoptilolite) ion exchange for ammonia (NH3-N) polishing
after desalination. NH4+ is exchanged onto the zeolite, and the bed is
regenerated in place with brine. Because the unit treats desalinated water,
competing cations (Na+, K+, Ca2+) are low and no correction for them is
applied. Bed life comes from an NMSU bench column test (NMSU assumptions).

## Using the Model

### Removal efficiencies

Open **Removal efficiencies** for the zeolite unit:

| Constituent | Default | Set by |
|---|---|---|
| Ammonia nitrogen | 95% | User. Also sets the breakthrough point that determines bed life. |
| Other constituents | 0% | User |

A higher NH3-N removal shortens the time between regenerations, because the
bed must be regenerated before the effluent rises above the target.

### What the model calculates

- **Bed life** (bed volumes and days between regenerations) from the NH3-N
  removal and the inlet NH3-N.
- **Bed volume and zeolite inventory** from the flow and EBCT.
- **Regeneration chemicals** (NaCl and NaOH) and the **spent brine** volume.
- **Media replacement** and spent zeolite, when a replacement fraction is set.
- **Electricity** for pumping through the beds.

### How bed life is determined

The bed life comes from the first service cycle of the NMSU bench column
(KMI zeolite 14x30, EBCT 20 min, feed about 25 mg/L NH3-N, 10% NaCl
regeneration):

| Bed volumes treated | NH3-N removal |
|---|---|
| 0-391 | 100% |
| 482 | 99.8% |
| 559 | 89.4% |
| 724 | 37.2% |
| 1,244 | 0% |

The model reads the bed volumes at which removal falls to the target (518 BV
at 95%; 391 BV at 100%) and scales them to the inlet NH3-N, keeping the NH3-N
loaded per bed volume the same as in the bench test:

```text
BV         = BV_bench x 24.38 / C_in        24.38 mg/L = bench feed, C_in = inlet NH3-N
t_service  = BV x EBCT / 1440               days between regenerations
V_bed      = Q x EBCT / 1440                bed volume (m3)
inventory  = 824 x V_bed                    kg zeolite (bench bulk density)
```

At the default 95% removal and EBCT 20 min:

| Inlet NH3-N (mg/L) | Bed volumes | Days between regenerations |
|---|---|---|
| 1 | 12,619 | 175 |
| 5 | 2,524 | 35 |
| 10 | 1,262 | 18 |
| 25 | 505 | 7 |

A warning appears when inlet NH3-N is above 30 mg/L (above the bench range).

### Regeneration

The bed is regenerated with the bench procedure: a 10% NaCl brine at pH 11,
90 bed volumes per regeneration, reused for 5 regenerations. NaOH keeps the
brine at pH 11 so that the eluted ammonium converts to ammonia.

```text
fresh brine per regeneration = 90 x V_bed / 5                          m3
NaCl  = fresh brine x brine density x 0.10 x regenerations per year     kg/year
NaOH  = N removed (kmol/year) x NaOH ratio x 40                         kg/year
spent brine = fresh brine x regenerations per year                      m3/year (reported)
```

The NaOH ratio (default 1 mol per mol NH4-N) is an engineering estimate; set
it to 0 for neutral (pH 7) regeneration.

### Media replacement

The media is regenerated in place, so the default replacement fraction is 0.
When it is set, the replaced mass per cycle is that fraction of the zeolite
loaded in one cycle at the ammonium exchange capacity (AEC, default 4 mg N/g);
the replaced mass is reported as spent zeolite.

### Energy

```text
energy = rho x g x H / pump efficiency / 3.6e6       kWh per m3 feed
```

H is the head through the beds and piping (default 10 m), as for GAC.

## Cost Model

### Capital

```text
C_bare    = 3305.1 x Q^0.6961              2021 dollars, Q = inlet flow (m3/day), escalated with CEPCI
C_direct  = TIC x C_bare                   TIC = 1.15
CAPEX     = IF x C_direct                  system-level investment factor
```

The cost curve comes from the US EPA cation exchange cost model run with
zeolite settings (EBCT 20 min) at flows from 0.12 to 22.6 MGD. It covers
pressure vessels, piping, valves, instrumentation, brine and backwash tanks
and building, but not the initial zeolite charge. The EPA costs already
include transportation and installation, so TIC is 1.15 (same basis as GAC).

### Operating

```text
electricity = energy x Q x days x electricity price
chemicals   = (NaCl x NaCl price + NaOH x NaOH price) x days / 365
media       = replaced zeolite x days / 365 x zeolite price
maintenance = maintenance fraction x C_direct
OPEX        = (1 + O&M contingency) x (electricity + chemicals + media + maintenance)
```

Spent-brine disposal is not costed in this unit; the brine volume is reported
for the system level.

## Default Inputs

| Input | Default | Basis |
|---|---|---|
| NH3-N removal | 95% | NMSU assumptions (removal table) |
| Recovery | 0.995 | NMSU assumptions |
| EBCT | 20 min | NMSU assumptions (bench test); Turan and Turan 2021 |
| Brine per regeneration | 90 bed volumes | NMSU assumptions (bench: 0.9 L per 10 mL bed) |
| Brine reuse | 5 regenerations | NMSU assumptions (bench) |
| NaCl in brine | 10% by mass | NMSU assumptions (bench) |
| NaOH to NH4-N | 1 mol/mol | Engineering estimate |
| AEC | 4.0 mg N/g | NMSU assumptions; Deng et al. 2014 (2.5-21.5) |
| Pump head, efficiency | 10 m, 0.70 | Engineering estimate (same as GAC) |
| Zeolite price | 4.41 $/kg (2014 $) | NMSU assumptions (bench vendor price); Deng et al. 2014 |
| Media replacement | 0 per cycle | NMSU assumptions (regenerated in place) |
| NaCl price | 40 $/t (2014 $) | Deng et al. 2014 |
| NaOH price | 300 $/t (2014 $) | Deng et al. 2014 |
| Equipment cost curve | 3305.1 x Q^0.6961 (2021 $) | US EPA cation exchange cost model, zeolite settings |
| TIC | 1.15 | Engineering estimate on an installed-cost basis |
| Maintenance fraction | 0.02 /yr of C_direct | NMSU assumptions |
| O&M contingency | 0.20 of OPEX | NMSU assumptions; Wang et al. 2024 DWPR report |

## Assumptions and Limits

- Bed life comes from one bench column, first cycle only; the second cycle
  after regeneration ran longer, so the first cycle is conservative.
- Bed volumes scale inversely with inlet NH3-N; behaviour at very low
  concentrations is not captured.
- Intended for desalinated water with low competing cations.
- The bench brine volume (90 bed volumes) is high for full scale; the EPA
  design basis (15 lb NaCl per ft3 of media) uses about eight times less salt.
- Spent-brine disposal and ammonium chloride recovery are not included.
- The cost curve is for EBCT 20 min; changing EBCT changes bed life but not
  capital cost.

## Sources

- NMSU assumptions: bench zeolite column test (KMI zeolite 14x30, EBCT 20 min,
  10% NaCl regeneration) and TEA cost assumptions.
- Koon, J.H., Kaufman, W.J. Optimization of Ammonia Removal by Ion Exchange
  Using Clinoptilolite. US EPA Water Pollution Control Research Series,
  Report 17080 (1972).
- Turan and Turan 2021, Water Science & Technology, DOI 10.2166/wst.2021.468.
- Deng, Q., Dhar, B.R., Elbeshbishy, E., Lee, H.-S. 2014. Ammonium nitrogen
  removal from the permeates of anaerobic membrane bioreactors: economic
  regeneration of exhausted zeolite. Environmental Technology 35, 2008-2017.
- US EPA 2023. Work Breakdown Structure (WBS) Model for Cation Exchange
  Treatment (2021 dollars). Drinking Water Treatment Technology Unit Cost Models.
- Wang et al. 2024 DWPR report (O&M contingency).
