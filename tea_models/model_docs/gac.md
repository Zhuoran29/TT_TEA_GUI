# GAC

The GAC model uses the Good folder BV-based saturation/changeout model.

## Technical model

TOC removal is calculated from WaterTAP GAC outlet/inlet molar flow:
`1 - 0.28773 / 1.15`, or about 74.98%. Oil, BTEX, and PAHs use the same removal
fraction by default.

Bed volumes to saturation are calculated with the empirical power law:
`BV = 1.5e5 * TOC^-1.85`, capped between 1 and 150,000 BV. Changeout interval and
annual GAC use are calculated from BV, adsorber bed volume, fresh GAC mass, and
flow.

## Cost model

Reference GAC CAPEX is scaled by capacity using the editable CAPEX scaling
exponent. OPEX includes GAC replacement, GAC regeneration, replacement/
regeneration energy, and O&M contingency. Maintenance as a fraction of CAPEX is
not included.

## Sources

- Lugo et al. 2025, Journal of Environmental Chemical Engineering 13, 117026.
- WaterTAP GAC design output used by the NMPWRC GAC model.
- NMPWRC GAC pilot-data BV correlation.
