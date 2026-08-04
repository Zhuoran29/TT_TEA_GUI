# Electrocoagulation

Electrocoagulation is modeled as an aluminum-electrode EC unit at a default
current density of 20 mA/cm2.

## Technical model

Water-quality default removals use the R20 removal table from the Good model.
The EC reactor volume and electrode area are scaled from the reference reactor
volume, reference flow, and hydraulic retention time. Energy is calculated from
solution resistance, system current, and cell voltage. Aluminum dose is
calculated with Faraday's law.

Al(OH)3 solids plus removed TSS are reported as solid waste. The unit recovery
creates a waste/brine flow that is passed to the shared brine disposal stream.
No EC brine disposal cost is included in this model.

## Cost model

Reference EC CAPEX is scaled by capacity using the editable CAPEX scaling
exponent. The app-level investment factor and CRF are used for installed CAPEX
and LCOW. OPEX includes aluminum electrode consumption, electricity, labor,
solid-waste disposal, and O&M contingency.

Maintenance as a fraction of CAPEX is intentionally not included.

## Sources

- Naje et al. 2019, electrocoagulation treatment at 20 mA/cm2.
- Lugo et al. 2025, Journal of Environmental Chemical Engineering 13, 117026.
- Abada et al. 2022, Journal of Water Process Engineering aluminum electrode
  price basis.
- WaterTAP electrocoagulation model assumptions.
