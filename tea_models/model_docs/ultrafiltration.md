# Ultrafiltration Model Documentation

## Scope

Pressure-driven ultrafiltration used as pretreatment to remove suspended
solids, emulsified oil and part of the organics ahead of IX or desalination.
Sodium bisulfite is dosed to dechlorinate the filtrate after chemically
enhanced backwash. Dissolved salts pass through. Costs follow the KBH TEA
workbook (NMSU UF model).

## Using the Model

### Removal efficiencies

| Constituent | Default | Set by |
|---|---|---|
| TSS | 95% | User |
| Turbidity | 95% | User |
| Oil | 90% | User |
| TOC | 20% | User |
| Dissolved ions, TDS | 0% | |

The TOC removal is an assumption. Reported UF removals of 96-98% (COD,
total hydrocarbons or TOC) were measured on produced water with high free
and emulsified oil, where most of the organic load is in the oil phase. In
the same studies, dissolved organics such as BTX were removed by about 54%,
and low-wavelength absorbance of refinery wastewater by 23%. Downstream of
DAF and walnut shell filtration most of the remaining TOC is dissolved, so
20% is used. Enter a higher value if the feed still carries emulsified oil.

### What the model calculates

- **Filtrate and backwash flows** from the recovery.
- **Filtrate quality** from the removal table.
- **Feed pump power** and electricity.
- **Sodium bisulfite use**.
- **Costs**.

### Water recovery

The backwash and cleaning waste is 1 - recovery of the feed. The default
0.99 is the KBH workbook basis: 0.9603 MGD filtrate from 0.97 MGD feed.

### Energy

```text
P      = Q_gpm x TDH / 3960 x 0.7457 / (pump eff x motor eff x VFD factor)     kW
energy = P x 24 / Q                                                             kWh/m3 feed
```

At the default 50 ft TDH this is about 0.059 kWh/m3.

### Chemicals

```text
NaHSO3 = dose x Q / 1000          kg/day
```

## Cost Model

### Capital

```text
C_ref     = 970,000 gpd x 2 $/gpd + 2,000 ft2 x 300 $/ft2 = 2.54 M$     2024 dollars
C_bare    = C_ref x (Q / 970,000 gpd)^0.87
C_direct  = TIC x C_bare                                                 TIC = 1.43
CAPEX     = IF x C_direct                                                system-level investment factor
```

The reference is the KBH TEA workbook UF line (equipment and building). The
workbook adds site work (10%) and electrical, instrumentation and controls
(30%) to the direct items, which gives TIC = 1.1 x 1.3 = 1.43. Contingency,
engineering and the other indirect costs are covered by the system-level
investment factor.

### Operating

```text
electricity = energy x Q x days x electricity price
bisulfite   = NaHSO3 x days x price
maintenance = maintenance fraction x C_direct          includes labor and membrane replacement
OPEX        = (1 + O&M contingency) x (electricity + bisulfite + maintenance)
```

Maintenance is usually the largest operating cost. Labor and membrane
replacement are not entered separately; they are covered by the 2% of
direct cost, as in the KBH workbook.

## Default Inputs

| Input | Default | Basis |
|---|---|---|
| Recovery | 0.99 | KBH TEA workbook (0.9603 / 0.97 MGD) |
| Sodium bisulfite dose | 5 mg/L | KBH TEA workbook |
| Pump TDH | 50 ft | KBH TEA workbook (Pump for MU/UF) |
| Pump, motor efficiency, VFD factor | 0.75, 0.95, 0.98 | KBH TEA workbook (Pump for MU/UF) |
| Reference flow | 970,000 gpd | KBH TEA workbook |
| Equipment unit cost | 2 $/gpd (2024 $) | KBH TEA workbook |
| Building | 2,000 ft2 at 300 $/ft2 (2024 $) | KBH TEA workbook |
| Scaling exponent | 0.87 | NMSU assumptions |
| TIC | 1.43 | KBH TEA workbook (site 10%, E&IC 30%) |
| Sodium bisulfite price | 0.25 $/lb | NMSU assumptions; KBH TEA workbook |
| Maintenance fraction | 0.02 /yr of C_direct, including labor and membrane replacement | KBH TEA workbook (other maintenance 2% of system direct cost) |
| O&M contingency | 0.20 of OPEX | NMSU assumptions; Wang et al. 2024 DWPR report |
| TOC removal | 20% | Assumption (see Removal efficiencies) |

## Assumptions and Limits

- Removals are fixed fractions; flux decline, fouling and membrane area are
  not modeled.
- The cost scales with flow, not with membrane area, so feeds that need a
  lower flux are not costed higher.
- The backwash waste is reported for the system-level waste stream; its
  disposal cost is not included in this unit.
- CEB chemicals other than sodium bisulfite are not included.

## Sources

- NMSU assumptions: NMSU UF model (cost structure, scaling exponent).
- KBH TEA Appendix (2024-10-24): Capital_Summary, O&M_Summary, Power Load
  Details and Chemical Details sheets.
- Wang et al. 2024 DWPR report (O&M contingency).
- Asatekin, A.; Mayes, A. M. 2009. Oil industry wastewater treatment with
  fouling resistant membranes containing amphiphilic comb copolymers.
  Environ. Sci. Technol. 43, 4487-4492 (UF of produced water: COD removal
  96% on a high-oil sample).
- Fakhru'l-Razi, A. et al. 2009. Review of technologies for oil and gas
  produced water treatment. J. Hazard. Mater. 170, 530-551 (UF total
  hydrocarbons 96%, BTX 54%).
