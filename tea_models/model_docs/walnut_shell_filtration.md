# Walnut Shell Filtration Model Documentation

## Scope

Walnut shell filtration (WSF) removes dispersed oil and suspended solids from
produced water ahead of downstream treatment. The media is cleaned in place by
backwash with mechanical scrubbing and a periodic chemical clean. Performance
and cost follow the NMSU WSF model (NMSU assumptions).

## Using the Model

### Removal efficiencies

Open **Removal efficiencies** for the WSF unit:

| Constituent | Default | Set by |
|---|---|---|
| Oil and grease | 80% | User |
| TSS | 80% | User |
| Turbidity | 80% | User (same as TSS) |
| TOC | 60% | User |
| Iron | 50% | User |
| H2S | 75% | User (when H2S is added to the feed) |
| Other constituents | 0% | User |

The defaults are the lower limits of reported WSF removals (NMSU assumptions).
WSF mainly captures free and dispersed oil and particles; dissolved organics
pass largely through, so the TOC removal depends on how much of the feed TOC is
oil or particle-bound.

### What the model calculates

- Outlet water quality from the removal table.
- Outlet flow from the water recovery (default 0.99); the rest leaves as
  backwash reject.
- Electricity from the energy intensity (default 0.17 kWh/m3 of feed), which
  covers feed and backwash pumping and media scrubbing.

## Cost Model

### Capital

The capital cost follows the NMSU WSF model: the annualized CAPEX of a
reference WSF (US DOE vendor data, WSF only, 20,000 bbl/day) is converted back
to an installed cost with the amortization used in the DOE report, then scaled
to the inlet flow.

```text
C_ref     = c_bbl x 7,200,000 bbl/yr / CRF(5%, 10 yr)      c_bbl = 0.008993 $/bbl  ->  C_ref = 500,000 $ (2020)
C_bare    = C_ref x (Q / 3,180 m3/day)^n                   escalated with CEPCI; n = 0.87
C_direct  = TIC x C_bare                                   TIC = 1
CAPEX     = IF x C_direct                                  system-level investment factor
```

The reference covers the WSF alone; the gas flotation unit reported with it in
the DOE data is excluded. The reference cost includes installation, so TIC
is 1; indirect costs are covered by the system-level investment factor.

### Operating

```text
electricity = energy intensity x Q x days x electricity price
cleaning    = media cleaning cost x Q x days
maintenance = maintenance fraction x C_direct          includes labor
OPEX        = (1 + O&M contingency) x (electricity + cleaning + maintenance)
```

The media is reused: backwash scrubbing restores it, and attrition losses are
typically below 5% per year. The media cleaning cost (default 0.0546 $/m3,
2020 $) is the weekly cleaning chemical cost in the same DOE vendor data
(62,500 $/yr at 20,000 bbl/day) and also covers media makeup.

## Default Inputs

| Input | Default | Basis |
|---|---|---|
| Oil and grease, TSS, turbidity removal | 80% | NMSU assumptions (removal table) |
| TOC removal | 60% | NMSU assumptions (removal table) |
| Iron removal | 50% | NMSU assumptions (removal table) |
| H2S removal | 75% | NMSU assumptions (removal table) |
| Recovery | 0.99 | NMSU assumptions |
| Energy intensity | 0.17 kWh/m3 | NMSU assumptions; US DOE report, WSF vendor electricity |
| Reference CAPEX | 0.008993 $/bbl (2020 $) | US DOE report, WSF vendor data (64,752 $/yr at 7,200,000 bbl/yr) |
| CAPEX scaling exponent | 0.87 | NMSU assumptions |
| TIC | 1.0 | Reference cost includes installation |
| Media cleaning cost | 0.0546 $/m3 (2020 $) | US DOE report, WSF vendor data |
| Maintenance fraction | 0.03 /yr of C_direct, including labor | NMSU assumptions (same basis as GAC and DAF) |
| O&M contingency | 0.20 of OPEX | NMSU assumptions; Wang et al. 2024 DWPR report |

## Assumptions and Limits

- Removals are fixed fractions and do not depend on loading, media condition or
  backwash frequency.
- Backwash reject is sent to the system-level reject stream; it is not recycled
  to the front of the train.
- The reference cost year (2020) is inferred from the cost index used in the
  DOE report.
- The vendor data are for one 20,000 bbl/day system; costs far from that size
  rely on the scaling exponent.

## Sources

- NMSU assumptions: NMSU WSF model (removal assumptions, scaling exponent,
  O&M factors).
- Drover, C. 2022. Fouling-resistant, chlorine-tolerant zwitterionic membranes
  for treatment of produced water in the Permian Basin. Final report, US DOE
  award DE-FE0031851 (ZwitterCo). DOI 10.2172/1887171. Vendor data for
  DGF + WSF pretreatment at 20,000 bbl/day.
- Wang et al. 2024 DWPR report (O&M contingency).
