# Ion Exchange (Demineralization) Model Documentation

## Scope

Two-bed demineralization:
- An H-form strong acid cation (SAC) bed exchanges all cations for H+.
- An OH-form strong base anion (SBA) bed exchanges all anions for OH-.
- H+ and OH- form water, so TDS, sodium and chloride are removed.
- The beds are regenerated with HCl and NaOH.

Every ion takes up resin capacity, so regenerant use grows with the total
ionic load. Above a few hundred mg/L TDS, BWRO is usually cheaper. For
removing only selected constituents without changing TDS, use **Ion
exchange** (selective). Sizing, vessel costs and rinse volumes follow the US
EPA WBS cation and anion exchange models. Regeneration levels are typical
demineralization values (see Default Inputs).

## Using the Model

### Removal efficiencies

| Constituent | Default | Set by |
|---|---|---|
| TDS | 95% | User. Sets the removal of every ion. |
| All ions (Na, Cl, Ca, Mg, Ba, Sr, Mn, Li, NH4, SO4, HCO3, F, silica, boron, As, Se, U, radionuclides), hardness, alkalinity, conductivity | same as TDS | Model |
| Organics (TOC, oil, BTEX) | 0% | |

Demineralization removes all ions at one fraction, so only the TDS entry is
used. A warning is shown when other entries differ from it. A removal below
the bed removal (99%) is met by bypass, so a TDS target can be reached by
treating part of the flow. For example, 738 to 480 mg/L TDS (35% removal)
treats 35% of the flow.

### What the model calculates

- **Treated fraction and bypass**: f = removal / bed removal.
- **Ionic load** and **run length** of each bed.
- **HCl and NaOH use** and the **spent regenerant** volume, which sets the
  water recovery.
- **Product water**: every ion x (1 - removal).
- **Spent regenerant quality**, by mass balance.
- **Resin volume**, **electricity**, and costs.

### Ionic load and run length

```text
cations = max(Ca/20.04 + Mg/12.15, hardness/50.04) + Ba/68.66 + Sr/43.81 + Mn/27.47
          + Na/22.99 + Li/6.94 + NH3-N/14.01                                         meq/L
anions  = Cl/35.45 + SO4/48.03 + F/19.00 + SiO2/60.08 + B/10.81 + max(HCO3/61.02, alk/50.04)
load    = max(cations, anions, TDS/58.44)               TDS as NaCl covers ions that are not tracked
BV      = min(1000 x capacity / (bed removal x load), 1000)    per bed
```

| Bed | Capacity | Regenerant dose | Regenerant ratio |
|---|---|---|---|
| Cation (SAC, H form) | 1.0 eq/L | 100 g HCl/L | 2.7 x stoichiometric |
| Anion (SBA, OH form) | 0.5 eq/L | 100 g NaOH/L | 5.0 x stoichiometric |

At 738 mg/L TDS (about 12.6 meq/L) the anion bed runs about 40 bed volumes
(80 minutes at EBCT 2 min) between regenerations.

### Regeneration and recovery

```text
HCl, NaOH     = dose x V_bed x cycles per year                       kg/year
waste per cycle = dose / regenerant concentration + rinse + backwash   bed volumes
recovery      = 1 - spent regenerant / feed
```

| Bed | Regenerant | Rinse | Backwash | Waste per cycle |
|---|---|---|---|---|
| Cation | 100 g/L at 5% HCl: 2.0 BV | 7 BV | 1.2 BV | 10.2 BV |
| Anion | 100 g/L at 4% NaOH: 2.4 BV | 7 BV | 1.2 BV | 10.6 BV |

At high loads the recovery falls quickly. At 738 mg/L TDS and 95% removal,
about 38% of the feed leaves as spent regenerant and rinse water. The spent
regenerant is reported for the system-level waste stream; its disposal cost
is not included in this unit.

### Energy

```text
energy = rho x g x H / pump efficiency / 3.6e6 x f       kWh per m3 feed, H = 10 m
```

## Cost Model

Same structure as selective IX:

```text
C_direct  = TIC x (a_c x Q_bed^b_c + a_a x Q_bed^b_a + resin)     2021 dollars; TIC = 1.15
CAPEX     = IF x C_direct
OPEX      = (1 + O&M contingency) x (HCl + NaOH + resin + electricity + maintenance)
```

The vessel cost curves are those of the selective unit (EPA cation and anion
exchange models). Acid-resistant linings, a degasifier and neutralization of
the spent regenerant are not included.

## Default Inputs

| Input | Default | Basis |
|---|---|---|
| TDS removal | 95% | NMSU assumptions |
| Bed removal | 0.99 | NMSU assumptions |
| EBCT | 2.5 min cation, 2.0 min anion | EPA cation and anion exchange models |
| Cation capacity | 1.0 eq/L | Lenntech, indicative capacity at 500 mg/L TDS |
| Anion capacity | 0.5 eq/L | Lenntech, indicative capacity at 500 mg/L TDS |
| HCl dose, concentration | 100 g/L, 5% | Woolley 2012: 60-160 g/L, 3-6% |
| NaOH dose, concentration | 100 g/L, 4% | Woolley 2012: 60-160 g/L, 3-6% |
| Rinse, backwash | 7 BV, 1.2 BV per bed | EPA anion exchange model |
| BV_max | 1,000 | EPA cation exchange model |
| Cost curves, TIC, resin prices, resin life | as selective IX | EPA models and cost data |
| HCl price | 1,086 $/t (2021 $) | EPA cost data, large quantity |
| NaOH price | 940 $/t as NaOH (2021 $) | EPA cost data, 50% solution, large quantity |
| Maintenance fraction | 0.02 /yr of C_direct, including labor | NMSU assumptions |
| O&M contingency | 0.20 of OPEX | NMSU assumptions; Wang et al. 2024 DWPR report |

## Assumptions and Limits

- The defaults describe co-current regeneration. Counter-current
  regeneration uses about half the regenerant (Lenntech), so lower doses can
  be entered.
- Bicarbonate is counted in the anion load. A degasifier between the beds
  would remove it as CO2 and reduce the NaOH use.
- Silica and boron are counted as removed, but they are the first ions to
  break through in practice.
- Removal is a fixed fraction; leakage and effluent pH are not modeled.
- Spent-regenerant disposal and neutralization are not included.

## Sources

- US EPA 2023. WBS Models for Cation Exchange and Anion Exchange Treatment
  (2021 dollars), workbooks, documentation and cost data.
- Lenntech. Ion exchange demineralization plants.
  https://www.lenntech.com/ix-demi-plants.htm
- Woolley, J. 2012. Ion exchange process design. SCI Introduction to Ion
  Exchange in Water Treatment course.
- Wang et al. 2024 DWPR report (O&M contingency).
