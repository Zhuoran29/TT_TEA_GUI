# Walnut shell filtration

Walnut shell filtration uses the DOE DGF+WSF produced-water pretreatment cost
basis from the Good model.

## Technical model

The unit uses the app's generic media-filter sizing and water-quality interface.
Default energy intensity is 0.17 kWh/m3 feed. Recovery produces a waste/brine
flow that is combined with the train-level brine stream.

## Cost model

The DOE cost basis reports annualized CAPEX and OPEX in $/bbl at a 20,000
bbl/day reference flow. The model converts the annualized CAPEX basis back to an
installed reference CAPEX using the current train CRF, scales it by capacity,
then lets the app-level train logic annualize CAPEX consistently.

OPEX includes the reference WSF OPEX rate, electricity, labor, and O&M
contingency. Maintenance as a fraction of CAPEX is intentionally not included.

## Sources

- Drover 2022, DOE produced-water pretreatment report, DGF+WSF cost basis.
- Wang et al. 2024, Bureau of Reclamation DWPR final report, TEA labor and
  contingency assumptions.
