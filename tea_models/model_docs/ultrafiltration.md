# Ultrafiltration

The UF model replaces the former screening cost placeholders with the
KBH/NMPWRC UF workbook basis.

## Technical model

The model uses train inlet water quality and the standard app removal interface.
UF recovery sets the backwash/waste flow. Membrane area is calculated from flow
and membrane flux. Pump energy is calculated from total dynamic head, pump
efficiency, motor efficiency, and VFD factor.

Sodium bisulfite dose is tracked as kg/day for OPEX.

## Cost model

Reference direct UF CAPEX is calculated from a 0.97 MGD reference flow, $2/gpd
equipment cost, $300/ft2 building cost, and 2,000 ft2 reference building area.
The result is scaled by capacity using the editable CAPEX scaling exponent.

OPEX includes electricity, sodium bisulfite, labor, and O&M contingency. CAPEX
annualization remains in the train summary.

## Sources

- KBH/NMPWRC UF TEA workbook basis.
- Wang et al. 2024, Bureau of Reclamation DWPR final report.
- WaterTAP Ultra Filtration ZO documentation.
