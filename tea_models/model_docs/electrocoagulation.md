# Electrocoagulation Model Documentation

## Scope

Electrocoagulation (EC) with aluminum electrodes, used as produced-water
pretreatment for suspended solids, oil and organics. Aluminum dissolves from
the anodes, forms Al(OH)3 flocs, and the flocs are separated with the removed
solids. Sizing and costs follow the NMSU EC model (NMSU assumptions).

## Using the Model

### Removal efficiencies

Open **Removal efficiencies** for the EC unit. All values are set by the user.
The defaults are the values of the NMSU removal table that can be traced to
the EC tests of Al-Ajmi et al. 2025 (produced water, 30 min of EC):

| Constituent | Default | Measured in the tests |
|---|---|---|
| BTEX | 98% | 123,400 to 1,600 ug/L |
| Oil and grease | 77% | 44.8 to <10 mg/L |
| TSS | 58% | 124 to 53 mg/L |
| TOC | 53% | 1,320 to 619 mg/L |
| Barium | 44% | 0.223 to 0.124 mg/L |
| Silica | 34% | 4.9 to 3.2 mg/L |
| Chloride | 16% | 9,360 to 7,836 mg/L |
| Boron | 6% | 10.6 to 10.0 mg/L |
| Sodium | 4% | 2,769 to 2,664 mg/L |
| Strontium | 4% | 29.9 to 28.8 mg/L |
| Other constituents | 0% | |

The tests were run on gas-field produced water with a conductivity of about
14 mS/cm, roughly a tenth of a Permian feed, and the iron content of the
treated water rose during the run, which points to iron electrodes. Hardness,
alkalinity, sulfate and TDS are not reduced by default. Removals do not change
with the current density, treatment time or aluminum dose.

### What the model calculates

- **Electrode area and reactor volume** from the flow and the treatment time.
- **Current, cell voltage and electricity** from the current density, the
  electrode gap and the feed conductivity.
- **Aluminum dose** from the current (Faraday's law, 100% current efficiency).
- **Effluent pH** from CO2 stripping by the cathode hydrogen.
- **Sludge**: Al(OH)3 plus removed TSS, reported for the system-level waste
  stream, and the **water recovery** that follows from it.

### Sizing

The electrode area per unit flow is taken from the reference EC-Al design
(567 m2 of electrodes for 11,356 m3/day) and scaled by the treatment time
relative to the reference (15 min):

```text
A        = 567 x (Q / 11,356) x (HRT / 15)              electrode area (m2), HRT in min
V        = A x 12.5 / 567                               reactor volume (m3)
I        = j x A                                        current (A), j = current density (A/m2)
Al dose  = I x 26.98 / (3 x 96,485) / Q                 mg/L (Q in L/s)
```

At the defaults (20 mA/cm2, 30 min) the aluminum dose is about 161 mg/L,
independent of the flow.

### Energy

```text
kappa    = conductivity from TDS (NaCl relationship)    S/m
R        = gap / (kappa x A)                            ohm
U        = I x R + 1.5                                  V; 1.5 V overpotential for Al at 20 mA/cm2
energy   = U x I x 24 / 1000 / Q                        kWh per m3 feed (Q in m3/day)
```

### Effluent pH

Each Al3+ released at the anodes is matched by three OH- from the cathodes, so
forming Al(OH)3 leaves no excess base. The pH still rises a little because the
hydrogen produced at the cathodes strips CO2 from the water. The model
calculates the effluent pH with Reaktoro (Pitzer activity model): the feed is
set to its pH and alkalinity, and the hydrogen (charge / 2F) is brought to
equilibrium with the water in one stage, which is the upper bound of the
stripping. Mineral precipitation is not included.

At the default dose the pH rises by about 0.1-0.2 units (for example 6.40 to
6.53 for the Low feed). Hardness is not removed: calcium is limited by the
carbonate available, and magnesium needs pH 9.5-10 or higher. Without a feed
pH, alkalinity or Reaktoro, the pH passes through unchanged.

Large pH increases reported for EC (for example pH 4.5 to above 9 in Al-Ajmi
et al. 2025) come from iron electrodes, where dissolved Fe2+ leaves cathode OH-
unbalanced, and from acidic, weakly buffered feeds; they do not apply to
aluminum anodes on near-neutral produced water.

### Sludge

```text
sludge   = 2.89 x Al dose + removed TSS                 mg/L dry solids (kg per m3 / 1000)
```

The sludge is reported for the system-level waste stream; its disposal cost
is not included in this unit. Removed hardness, alkalinity, silica and other
dissolved constituents are not added to the sludge mass.

### Water recovery

Water leaves with the wet sludge:

```text
sludge volume = sludge / solids content / 1000          m3 per m3 feed
recovery      = 1 - sludge volume
```

The sludge solids content (default 2.5%) is an input; Al-Ajmi et al. 2025
measured 2.41-2.62% dry solids in EC sludge. At the defaults the recovery is
about 98%.

## Cost Model

### Capital

```text
C_bare    = 1,595,666 x (Q / 11,356 m3/day)^n           2024 dollars, escalated with CEPCI; n = 0.87
C_direct  = TIC x C_bare                                TIC = 1
CAPEX     = IF x C_direct                               system-level investment factor
```

The reference cost is a plant-level EC-Al cost at 11,356 m3/day (Lugo et al.
2025), so TIC is 1. Indirect costs (contingency, engineering, contractor
overhead and profit, sales tax) are covered by the system-level investment
factor.

### Operating

```text
aluminum    = Al dose x Q x days x aluminum price       anode replacement
electricity = energy x Q x days x electricity price
maintenance = maintenance fraction x C_direct           includes labor
OPEX        = (1 + O&M contingency) x (aluminum + electricity + maintenance)
```

## Default Inputs

| Input | Default | Basis |
|---|---|---|
| Removal table | see above | NMSU assumptions; Al-Ajmi et al. 2025 (Table 2, 30 min) |
| Current density | 20 mA/cm2 | NMSU assumptions; Al-Ajmi et al. 2025 |
| Treatment time (HRT) | 30 min | NMSU assumptions; Al-Ajmi et al. 2025 |
| Electrode gap | 0.02 m | Lugo et al. 2025 |
| Sludge solids content | 0.025 | Al-Ajmi et al. 2025 (2.41-2.62% dry solids) |
| Reference CAPEX | 1,595,666 $ at 11,356 m3/day (2024 $) | NMSU assumptions; Lugo et al. 2025 |
| CAPEX scaling exponent | 0.87 | NMSU assumptions |
| TIC | 1.0 | Reference is a plant-level cost |
| Aluminum price | 2.23 $/kg (2022 $) | Anuf et al. 2022 |
| Maintenance fraction | 0.03 /yr of C_direct, including labor | NMSU assumptions (same basis as GAC, DAF and WSF) |
| O&M contingency | 0.20 of OPEX | NMSU assumptions; Wang et al. 2024 DWPR report |

## Assumptions and Limits

- The aluminum dose follows from the current density and the treatment time,
  not from the removals; changing either changes the dose and its cost but
  not the treated water quality.
- The removal table applies fixed fractions measured on a much less saline
  water. Chloride and sodium removals in particular may not carry over: 16%
  of a 59,000 mg/L chloride feed is about 9,400 mg/L.
- Current efficiency is 100%; the overpotential is fixed at 1.5 V.
- Electrode area scaling assumes the reference electrode area per unit flow
  applies at every flow.

## Sources

- NMSU assumptions: NMSU EC model (removal table, current density, treatment
  time, CAPEX scaling).
- Al-Ajmi, F., Al-Marri, M., Almomani, F. 2025. Electrocoagulation process as
  an efficient method for the treatment of produced water treatment for
  possible recycling and reuse. Water 17, 23.
- Lugo, A. et al. 2025. Journal of Environmental Chemical Engineering 13,
  117026.
- Anuf et al. 2022. Journal of Water Process Engineering,
  doi:10.1016/j.jwpe.2022.103074 (aluminum price).
- Wang et al. 2024 DWPR report (O&M contingency).
