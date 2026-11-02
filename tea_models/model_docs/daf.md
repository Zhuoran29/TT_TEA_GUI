# DAF Model Documentation

## Scope

Dissolved air flotation (DAF) with coagulation (ACH and polymer) and H2O2
oxidation, used as produced-water pretreatment for suspended solids, iron,
oil and grease, and part of the organics. Chemical dosing and capital cost
follow the NMSU DAF model (NMSU assumptions).

## Using the Model

### Removal efficiencies

Open **Removal efficiencies** for the DAF unit:

| Constituent | Default | Set by |
|---|---|---|
| TSS | 87% | User. Together with iron, sets the ACH and polymer doses. |
| Iron | 87% | User. Together with TSS, sets the ACH and polymer doses. |
| Oil and grease | 87% | User. NMSU assumes the same removal as TSS. |
| Turbidity | 87% | User. |
| TOC | Calculated | Model, from the H2O2 dose (see below). The table shows the calculated value; the user can enter a different value to override it. |
| H2S | Calculated | Model, from the H2O2 left after oxidizing the feed iron (see below). Shown and overridable in the same way as TOC. |
| Other constituents | 0% | User. |

### What the model calculates

- **ACH and polymer doses** for the TSS and iron removals in the table.
- **H2O2 dose**: 1.75 mg H2O2 per mg of feed iron (input). With no iron in the
  feed, no H2O2 is dosed.
- **TOC removal** from the H2O2 dose. COD removal is taken equal to TOC removal.
- **H2S removal** by the H2O2 dose, when H2S is in the feed.
- **Float (sludge)** and the **water recovery** that follows from it.
- **Electricity** of the recycle pump and auxiliary equipment.

### How the doses are determined

- **ACH and polymer**: NMSU dose-removal relationships for TSS and iron, built
  from jar tests on hypersaline produced water (Abada et al. 2022: DAF at
  pH 7.5 and 12% recycle; ACH 0-75 mg Al/L without polymer, polymer 0-5 mg/L
  at 25 mg Al/L, and polymer alone at 5 mg/L). The model picks
  the cheapest ACH and polymer doses at which the predicted TSS and iron
  removals both reach the values in the removal table (default chemical
  prices). Removals are counted from the raw
  water. In the tests, DAF with the oxidant alone (no ACH or polymer) already
  removed about 62% of TSS and iron, and the highest removal reached was
  about 95%. Targets below about 62% need no ACH or polymer. At the default
  87%, the model doses about 2.4 mg Al/L of ACH and 4.0 mg/L of polymer:
  in the tests, polymer alone at 5 mg/L removed about 88% of TSS and 85% of
  iron, so little ACH is needed at this target.
- **TOC**: COD removal measured in Fenton oxidation tests on produced water
  (Afzal et al. 2018) at six H2O2:Fe molar ratios (2-75) and four H2O2
  concentrations (0.001-0.15 mol/L). The model reads the removal from these
  measurements at the dosed ratio and H2O2 concentration, interpolating
  between the measured points. The default 1.75 mg H2O2 per mg Fe is a molar
  ratio of 2.87. With the default ratio:

| Feed iron (mg/L) | H2O2 dose (mg/L) | Calculated TOC removal |
|---|---|---|
| 19.5 | 34 | 33% |
| 25.7 | 45 | 34% |
| 49.8 | 87 | 37% |

- **H2S**: part of the H2O2 is used to oxidize the feed iron (Fe2+ to Fe3+,
  0.3045 mg H2O2 per mg Fe); the rest oxidizes H2S to elemental sulfur
  (H2S + H2O2 -> S + 2 H2O, 0.998 mg H2O2 per mg H2S):

```text
H2S removed = min( H2S_in , (H2O2:Fe ratio - 0.3045) x Fe_in / 0.998 )      mg/L
```

  With the default ratio of 1.75 this is the NMSU relationship
  min(H2S_in, 1.445 x Fe_in / 0.998). For example, 12 mg/L of feed iron
  removes up to 17.4 mg/L of H2S. To add H2S to the feed, select it under
  **Additional Input Parameters** in the influent water quality.

The model shows a warning when a TSS or iron target is above the highest
removal measured in the jar tests (about 95%), or when the H2O2 dose is
outside the tested range.

### Float and water recovery

The skimmed float carries the removed solids and oil and the sludge formed
by the chemicals:

```text
float solids = removed TSS + Al(OH)3 from ACH + Fe(OH)3 from removed iron + polymer + S from H2S   kg dry/day
float        = float solids + removed oil                                            kg/day
float volume = float / solids content / 1000                                         m3/day
recovery     = 1 - float volume / inlet flow
```

Al(OH)3 is 2.89 kg per kg of Al dosed and Fe(OH)3 is 1.91 kg per kg of iron
removed; sulfur is 0.94 kg per kg of H2S removed. The float solids content (default 3%) is an input. The float is
reported for the system-level waste stream; its disposal cost is not
included in this unit.

### Energy

A fraction of the treated water (recycle ratio, default 12%) is pumped to a
saturator at about 5 bar, where air dissolves; released into the incoming
water, it forms the microbubbles that float the flocs.

```text
energy = rho x g x H x recycle ratio / pump efficiency / 3.6e6 + auxiliary energy    kWh per m3 feed
```

The auxiliary energy (default 0.02 kWh/m3) covers the air compressor,
flocculators and float skimmer. At the defaults the total is about
0.044 kWh/m3.

## Cost Model

### Capital

```text
C_bare    = 313,992 x (Q / 3 MGD)^n            2018 dollars, escalated with CEPCI; n = 0.87
C_direct  = TIC x C_bare                       TIC = 1
CAPEX     = IF x C_direct                      system-level investment factor
```

The reference cost (3 MGD) is an installed cost, so TIC is 1. Indirect
costs (contingency, engineering, contractor overhead and profit, sales tax)
are covered by the system-level investment factor.

### Operating

```text
electricity = energy x Q x days x electricity price
chemicals   = (ACH x ACH price + polymer x polymer price + H2O2 x H2O2 price) x days
maintenance = maintenance fraction x C_direct          includes labor
OPEX        = (1 + O&M contingency) x (electricity + chemicals + maintenance)
```

ACH is costed as product mass: Al dose / Al content of the product (default
0.124).

## Default Inputs

| Input | Default | Basis |
|---|---|---|
| TSS, iron, oil and grease, turbidity removal | 87% | NMSU assumptions (removal table) |
| Recycle ratio | 0.12 | NMSU assumptions; Abada et al. 2022 |
| Recycle pump head, efficiency | 51 m, 0.70 | Engineering estimate (about 5 bar saturator) |
| Auxiliary energy | 0.02 kWh/m3 | Engineering estimate |
| H2O2 per iron | 1.75 mg/mg | NMSU assumptions (pilot study) |
| ACH aluminum content | 0.124 | Typical ACH product (23-24% Al2O3) |
| COD/TOC ratio | 4 | NMSU assumptions (used only to report COD) |
| Float solids content | 0.03 | Engineering estimate (mechanically skimmed float, 2-5%) |
| CAPEX scaling exponent | 0.87 | NMSU assumptions; Lugo et al. 2025; Liu et al. 2023 |
| TIC | 1.0 | Reference cost is an installed cost |
| ACH price | 0.4506 $/kg product (2021 $) | US EPA WBS cost database (polyaluminum chloride, large quantity) |
| Polymer price | 1.6344 $/kg (2021 $) | US EPA WBS cost database |
| H2O2 price | 1.3986 $/kg as 100% (2021 $) | US EPA WBS cost database (50% solution, large quantity) |
| Maintenance fraction | 0.03 /yr of C_direct, including labor | NMSU assumptions (same basis as GAC) |
| O&M contingency | 0.20 of OPEX | NMSU assumptions; Wang et al. 2024 DWPR report |

## Assumptions and Limits

- How ACH and polymer act together rests on a single polymer-only test (a
  preliminary test in the paper's supplement). Doses with little ACH and much
  polymer, such as the default, carry more uncertainty than doses near
  25 mg Al/L.
- Doses come from one set of jar tests and do not change with feed TSS or
  oil concentration, although emulsified oil and fine solids raise coagulant
  demand in practice.
- The two calibration data sets were measured at different pH, and the model
  applies both at once:
  - ACH and polymer doses: DAF tests at pH 7.5 (Abada et al. 2022). At
    pH 6.5, turbidity and iron removal dropped sharply (about 68 NTU and 9 mg/L
    iron left, against 14 NTU and 2 mg/L at pH 7.5), so the doses do not apply
    to acidic water.
  - TOC removal: Fenton tests at pH 3-3.5 with 120 minutes of reaction, on
    produced water with 3,200 mg/L COD (Afzal et al. 2018). At the pH of DAF
    (7-8), iron precipitates as Fe(OH)3 and is no longer recycled as a
    catalyst, and much of the H2O2 decomposes to oxygen. H2O2 then acts mainly
    as the iron oxidant (the role of chlorine in the Abada tests), and TOC
    removal by oxidation is small.
  - The H2O2 dosed can oxidize at most 0.47 mg COD per mg H2O2 (after the
    share used to oxidize iron). For a feed with 25.7 mg/L iron and about
    400 mg/L COD, that is about 4% of the COD; removal above that relies on
    coagulation and flotation of organics.
  - The calculated TOC removal is therefore an upper bound for DAF at pH 7-8.
    Reaching it would need a separate Fenton step ahead of DAF: acidify to
    about pH 3, react for about 2 hours, then neutralize to pH 7.5 before
    coagulation. The acid and base (which depend on the feed alkalinity), the
    reaction tank, and handling of H2S released on acidification are not
    included in this unit.
  - Enter a TOC removal in the removal table to override the calculated value.
- H2O2 is dosed and costed from feed iron even when the TOC removal is
  overridden.
- H2O2 is assumed to react first with iron and then with H2S; its use for TOC
  oxidation is not deducted from the H2S calculation (as in the NMSU model).
- The ACH price is the EPA polyaluminum chloride price per kg of product; ACH
  is more concentrated and usually costs more per kg.

## Sources

- NMSU assumptions: NMSU DAF model (pilot H2O2 to iron ratio, removal
  targets, CAPEX scaling, O&M factors).
- Abada, B., Joag, S., Sharma, R., Chellam, S. 2022. Hypersaline produced water
  clarification by dissolved air flotation and sedimentation with ultrashort
  residence times. Water Research 226, 119241.
- Afzal, T., Isa, M.H., Mustafa, M.R.u. 2018. Removal of organic pollutants
  from produced water using Fenton oxidation. E3S Web of Conferences 34, 02035.
- Lugo, A. et al. 2025. Journal of Environmental Chemical Engineering 13, 117026.
- Liu, M. et al. 2023. Techno-economic analysis for the selection of
  cost-effective treatment for algae removal in drinking water treatment
  plants. Water 15, 243.
- US EPA Work Breakdown Structure (WBS) cost models, chemical cost database
  (2021 dollars).
- Wang et al. 2024 DWPR report (O&M contingency).
