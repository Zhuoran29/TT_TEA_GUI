# Ammonia Stripping

This model is adapted from `Produced Water Valorization v1.xlsm`.

## Technical Model

The technical model uses the `NH3 Stripping Design Model` worksheet. It reads
`Ammonia nitrogen` from the current inlet water-quality stream and targets the
configured outlet ammonia concentration.

The model calculates:

- ammonia removal from feed and target outlet NH3-N
- Henry-law gas/liquid conversion using the worksheet H_cp basis
- minimum air:water ratio with the worksheet design factor
- stripping factor
- packed tower height from liquid flow, tower area, KLa, and inlet/outlet NH3-N

The default KLa is the worksheet average of values cited from:

- https://www.ijche.com/article_58591.html
- https://iopscience.iop.org/article/10.1088/1755-1315/344/1/012051/pdf

The Henry-law value follows the worksheet note citing Sander's 2015 Henry's law
compilation.

## Cost Model

The cost model uses the `Air Strip Cost Model` worksheet full unit-process CIP
cost curve. CAPEX and OPEX are log-interpolated from the workbook flow points
0.1, 1, 5, 15, and 30 MGD, then escalated from the workbook 2021 dollar basis to
the project base currency year.

Because the workbook curve already includes full unit-process capital cost, the
model does not apply the app-wide investment factor again.
