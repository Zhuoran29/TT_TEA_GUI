# Chemical Softening Model Documentation

## Scope

Lime-soda softening with acid neutralization, used as pretreatment to remove
hardness and other scale-forming ions ahead of desalination. Lime (as
Ca(OH)2) and soda ash (Na2CO3) are added, the precipitated minerals are
settled and dewatered, and H2SO4 brings the softened water back to the target
pH. The chemistry is calculated with Reaktoro (Pitzer activity model); costs
follow the KBH TEA workbook (NMSU CS model).

## Using the Model

### Inputs

| Input | Default | Set by |
|---|---|---|
| Lime dose | 10 mg/L as Ca(OH)2 | User |
| Soda ash dose | 4,301 mg/L as Na2CO3 | User |
| Target pH after neutralization | 8.0 | User |
| H2SO4 dose override | 0 (calculated) | User; enter a value to fix the acid dose |
| Sludge solids content | 0.10 | User; sets the water recovery |

The default doses are the average-TDS case of the NMSU CS model; the high-TDS
case used 501 mg/L lime and 9,801 mg/L soda ash. The doses that give a
required removal depend on the feed, so they should be checked for each
water. The removal table is not used: removals are calculated from the
chemistry (the table values apply only if Reaktoro is unavailable).

### What the model calculates

- **Softened pH**, the **H2SO4 dose** to reach the target pH, and the
  **neutralized pH**.
- **Effluent water quality**: Ca, Mg, Ba, Sr, Na, Cl, sulfate, silica,
  alkalinity, hardness, TDS and conductivity; radium and gross alpha/beta.
- **Precipitated solids** (kg/m3), reported for the system-level waste stream.
- **Sludge volume and water recovery**.
- **Costs**.

### Chemistry

The feed ions (Ca, Mg, Ba, Sr, Na, Cl, sulfate, alkalinity as HCO3-, silica as
H4SiO4) and the chemicals are equilibrated with calcite, aragonite, dolomite,
magnesite, brucite, gypsum, anhydrite, barite, celestite and silica phases.
H2SO4 is added by bisection until the pH is within 0.1 of the target.
Ammonium is not included in the Pitzer system.

The effluent is read from the final aqueous phase:

```text
Ca, Mg, Ba, Sr, Na, Cl      element totals in solution
sulfate, silica             S and Si totals, as SO4 and SiO2
alkalinity                  HCO3- + 2 CO3-2 + 2 MgCO3 + MgOH+ + OH- - H+ - HSO4- + H3SiO4- + 2 H2SiO4-2   (as CaCO3)
hardness                    feed hardness x (2.497 Ca + 4.118 Mg)_out / (2.497 Ca + 4.118 Mg)_in
TDS                         feed TDS + change in Ca, Mg, Ba, Sr, Na, Cl, SO4, SiO2 and HCO3
conductivity                feed conductivity x TDS_out / TDS_in
```

Soda ash adds sodium and carbonate, and the acid adds sulfate, so TDS can
rise even though hardness falls. With the high-TDS doses (501 mg/L lime,
9,801 mg/L soda ash) TDS rises by about 10%, mostly as sodium bicarbonate
left from the excess soda ash.

### Radionuclides

Radium is co-precipitated during lime softening (80-95% reported). Following
the NMSU CS model (SI Eq. B2.1):

```text
Ra removal (%) = 80 + 15 x lime / (lime + 5000)        lime in mg/L
```

Radium-226, radium-228, gross alpha and gross beta are removed by this
fraction: 80.0% at 10 mg/L lime, 81.4% at 501 mg/L and 87.5% at 5,000 mg/L.

### Water recovery

```text
sludge volume = solids / sludge solids content / 1000          m3 per m3 feed
recovery      = 1 - sludge volume
```

At the default 10% solids content and 2-4 kg/m3 of solids the recovery is
about 96-98%. Lime softening sludge is typically a few to about 15% solids
from the clarifier; if the dewatering filtrate is returned to the head of the
plant, the water lost is closer to that in the dewatered cake.

## Cost Model

### Capital

```text
C_bare    = 25,829,457 x (Q / 3,785.41 m3/day)^0.87       2024 dollars, escalated with CEPCI
C_direct  = TIC x C_bare                                   TIC = 1.43
CAPEX     = IF x C_direct                                  system-level investment factor
```

The reference cost is from the KBH TEA workbook at 1 MGD (ENR May 2024,
location factor 0.815):

| Item | Cost | Basis in the workbook |
|---|---|---|
| Lime softening | 6.8 M$ | 6.8 $/gpd |
| Lime dewatering | 11.53 M$ | Scaled with the solids load (32,551 lb/day) |
| Chemical area | 7.5 M$ | Lump sum for the whole plant |

The workbook adds site work (10%) and electrical, instrumentation and
controls (30%) to the direct items, which gives TIC = 1.1 x 1.3 = 1.43.
Contingency, general conditions, engineering, contractor overhead and profit
and sales tax are covered by the system-level investment factor.

### Operating

```text
chemicals   = (lime x lime price + soda ash x soda ash price + H2SO4 x acid price) x Q x days
electricity = energy x Q x days x electricity price
maintenance = maintenance fraction x C_direct           includes labor
OPEX        = (1 + O&M contingency) x (chemicals + electricity + maintenance)
```

Soda ash is usually the largest operating cost. The solids are reported for
the system-level waste stream; their disposal cost is not included in this
unit.

## Default Inputs

| Input | Default | Basis |
|---|---|---|
| Lime dose | 10 mg/L | NMSU assumptions (average-TDS case) |
| Soda ash dose | 4,301 mg/L | NMSU assumptions (average-TDS case) |
| Target pH | 8.0 | NMSU assumptions |
| Electricity | 0.223 kWh/m3 | KBH TEA workbook: 307,042 kWh/yr at 1 MGD |
| Sludge solids content | 0.10 | Engineering estimate |
| Reference CAPEX | 25,829,457 $ at 1 MGD (2024 $) | KBH TEA workbook |
| Scaling exponent | 0.87 | NMSU assumptions |
| TIC | 1.43 | KBH TEA workbook (site 10%, E&IC 30%) |
| Lime price | 0.05 $/lb | NMSU assumptions; KBH TEA workbook |
| Soda ash price | 0.45 $/lb | NMSU assumptions; KBH TEA workbook |
| H2SO4 price | 0.043 $/lb | NMSU assumptions |
| Maintenance fraction | 0.02 /yr of C_direct, including labor | KBH TEA workbook (other maintenance 2% of system direct cost) |
| O&M contingency | 0.20 of OPEX | NMSU assumptions; Wang et al. 2024 DWPR report |

## Assumptions and Limits

- Equilibrium chemistry; precipitation kinetics, incomplete settling and
  carryover of fines are not included.
- Doses are inputs; the model does not search for the dose that meets a
  target.
- The reference cost was developed for brackish RO concentrate at the KBH
  plant. The dewatering cost scales with the solids load in the workbook but
  with flow here, and the chemical area is a whole-plant lump sum.
- The electricity basis covers softening, UF, IX and degasifier pumping in
  the workbook.
- Radium removal follows an empirical relation; ammonium, boron and organics
  are passed through.

## Sources

- NMSU assumptions: NMSU CS model (Reaktoro softening and neutralization,
  doses, radium relation, cost structure).
- KBH TEA Appendix (2024-10-24): Capital_Summary and O&M_Summary sheets.
- Wang et al. 2024 DWPR report (O&M contingency).
