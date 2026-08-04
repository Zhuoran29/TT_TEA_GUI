# Chemical softening

Chemical softening is modeled as a Reaktoro equilibrium calculation using
`pitzer.dat` and `ActivityModelPitzer`, consistent with the app's scaling
tendency workflow.

## Technical model

The model takes the train inlet water quality and adds lime as Ca(OH)2 and soda
ash as Na2CO3. Reaktoro precipitates available mineral phases such as calcite,
dolomite, brucite, gypsum, barite, celestite, and silica phases. If the acid dose
override is zero, the model solves for the H2SO4 dose needed to reach the target
neutralization pH by bisection.

The outlet water quality is taken from the final neutralized Reaktoro state.
Generated precipitated solids are reported as kg/m3 feed and are used by the
cost model for solid-waste disposal. The unit recovery creates a waste/brine
flow that is passed into the app-level brine stream.

## Cost model

Reference direct CAPEX is scaled from the KBH/NMPWRC chemical-softening workbook
basis using the user-editable capacity exponent. The app-level investment factor
converts equipment CAPEX to total installed CAPEX, and the app-level CRF handles
annualized CAPEX in the train summary.

OPEX includes lime, soda ash, H2SO4, electricity, labor, solid-waste disposal,
and O&M contingency. Maintenance as a fraction of CAPEX is intentionally not
included, matching the LSRRO convention.

## Sources

- KBH/NMPWRC chemical-softening TEA workbook basis.
- Wang et al. 2024, Bureau of Reclamation DWPR final report, TEA labor and
  indirect-cost assumptions.
- NMPWRC Reaktoro chemical-softening simulator.
