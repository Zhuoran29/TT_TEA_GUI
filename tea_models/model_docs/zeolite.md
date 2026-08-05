# Zeolite

The zeolite model uses the Good folder bench breakthrough data for ammonia
removal and includes an NH4Cl product credit.

## Technical model

Default NH3-N removal is 95%. The model interpolates the bench breakthrough
curve at the target removal, adjusts BV by the ratio of average bench feed
NH3-N to train inlet NH3-N, then calculates service time and annual cycles from
BV and EBCT.

Zeolite mass is estimated from removed ammonia, service time, and ammonium
exchange capacity.

## Cost model

Equipment CAPEX is based on an ion-exchange vessel cost of $150/gpm. The Good
folder model assumes regenerated zeolite media, so full media replacement per
cycle is zero by default. OPEX includes electricity, optional media replacement
if a replacement fraction is entered, O&M contingency, and a negative cost
credit for recovered NH4Cl.

Maintenance as a fraction of CAPEX is intentionally not included.

## Sources

- Deng et al. 2014, Environmental Technology, DOI 10.1080/09593330.2014.889759.
- Turan and Turan 2021, Water Science & Technology, DOI 10.2166/wst.2021.468.
- US EPA Drinking Water Treatment Technology Unit Cost Models.
- NMPWRC bench zeolite testing data and NH4Cl credit assumption.
