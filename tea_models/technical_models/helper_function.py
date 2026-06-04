"""Property-package helpers translated from MVC.xlsx.

The equations and coefficients come from the workbook's "Property Packages"
sheet. Temperatures are in degrees C, pressure is in Pa, and seawater salinity
is represented as TDS mass fraction unless a function says otherwise.
"""

from __future__ import annotations

import math


PA_REF = 101_325.0
KELVIN_OFFSET = 273.15

CEPCI = {
    2001: 394.3,
    2002: 395.6,
    2003: 402.0,
    2004: 444.2,
    2005: 468.2,
    2006: 499.6,
    2007: 525.4,
    2008: 575.4,
    2009: 521.9,
    2010: 550.8,
    2011: 585.7,
    2012: 584.6,
    2013: 567.3,
    2014: 576.1,
    2015: 556.8,
    2016: 541.7,
    2017: 567.5,
    2018: 603.1,
    2019: 607.5,
    2020: 596.2,
    2021: 708.8,
    2022: 816.0,
    2023: 797.9,
    2024: 798.8,
}

WATER_DENSITY_COEFFS = (
    (999.9, 0),
    (2.034e-2, 1),
    (-6.162e-3, 2),
    (2.261e-5, 3),
    (-4.657e-8, 4),
)

SEAWATER_DENSITY_COEFFS = (
    (802.0, 0, 1),
    (-2.001, 1, 1),
    (1.677e-2, 2, 1),
    (-3.06e-5, 3, 1),
    (-1.613e-5, 2, 2),
)

WATER_ENTHALPY_COEFFS = (
    (141.355, 0),
    (4202.07, 1),
    (-0.535, 2),
    (4.0e-3, 3),
)

WATER_SPECIFIC_VOLUME_COEFFS = (
    (996.7767, 0),
    (-3.2406, 1),
    (1.27e-2, 2),
    (-4.7723e-5, 3),
)

LATENT_HEAT_COEFFS = (
    (2_501_000.0, 0),
    (-2369.0, 1),
    (0.2678, 2),
    (-8.103e-3, 3),
    (-2.079e-5, 4),
)

SEAWATER_ENTHALPY_COEFFS = (
    (-23482.5, 0, 0),
    (315183.0, 0, 1),
    (2802690.0, 0, 2),
    (-14460600.0, 0, 3),
    (7826.07, 1, 0),
    (-4.41733, 2, 0),
    (0.21394, 3, 0),
    (-19910.8, 1, 1),
    (27784.6, 1, 2),
    (9.72801, 2, 1),
)

BPE_COEFFS = (
    (17.95, 0, 2),
    (0.2823, 1, 2),
    (-4.584e-4, 2, 2),
    (6.56, 0, 1),
    (5.267e-2, 1, 1),
    (1.536e-4, 2, 1),
)

WATER_SAT_PRESSURE_COEFFS = {
    "a1": -5800.2206,
    "a2": 1.3914993,
    "a3": -4.8640239e-2,
    "a4": 4.1764768e-5,
    "a5": -1.4452093e-8,
    "a6": 6.5459673,
}

SEAWATER_SAT_PRESSURE_COEFFS = (
    (-4.5818e-4, 1),
    (-2.0443e-6, 2),
)


def _poly_temperature(coeffs, temperature_c):
    return sum(coef * temperature_c**order for coef, order in coeffs)


def _validate_tds_mass_fraction(tds_mass_fraction):
    tds = float(tds_mass_fraction)
    if tds < 0:
        raise ValueError("TDS mass fraction must be non-negative.")
    return tds


def water_dens_mass(temperature_c):
    """Return pure-water mass density in kg/m3."""
    return _poly_temperature(WATER_DENSITY_COEFFS, float(temperature_c))


def sw_dens_mass(temperature_c, tds_mass_fraction):
    """Return seawater mass density in kg/m3."""
    temperature_c = float(temperature_c)
    tds = _validate_tds_mass_fraction(tds_mass_fraction)
    salt_adjustment = sum(
        coef * temperature_c**temperature_order * tds**tds_order
        for coef, temperature_order, tds_order in SEAWATER_DENSITY_COEFFS
    )
    return water_dens_mass(temperature_c) + salt_adjustment


def water_enth_mass(temperature_c, pressure_pa=PA_REF):
    """Return pure-water specific enthalpy in J/kg."""
    temperature_c = float(temperature_c)
    pressure_pa = float(pressure_pa)
    sensible_enthalpy = _poly_temperature(WATER_ENTHALPY_COEFFS, temperature_c)
    density_for_pressure = _poly_temperature(
        WATER_SPECIFIC_VOLUME_COEFFS, temperature_c
    )
    return sensible_enthalpy + (pressure_pa - PA_REF) / density_for_pressure


def dh_vap_mass(temperature_c):
    """Return pure-water latent heat of vaporization in J/kg."""
    return _poly_temperature(LATENT_HEAT_COEFFS, float(temperature_c))


def sw_enth_mass(temperature_c, tds_mass_fraction, pressure_pa=PA_REF):
    """Return seawater specific enthalpy in J/kg."""
    temperature_c = float(temperature_c)
    tds = _validate_tds_mass_fraction(tds_mass_fraction)
    pressure_pa = float(pressure_pa)
    salt_adjustment = tds * sum(
        coef * temperature_c**temperature_order * tds**tds_order
        for coef, temperature_order, tds_order in SEAWATER_ENTHALPY_COEFFS
    )
    pressure_adjustment = (pressure_pa - PA_REF) / sw_dens_mass(temperature_c, tds)
    return water_enth_mass(temperature_c, PA_REF) + salt_adjustment + pressure_adjustment


def sw_bpe(temperature_c, tds_mass_fraction):
    """Return seawater boiling point elevation in degrees C."""
    temperature_c = float(temperature_c)
    tds = _validate_tds_mass_fraction(tds_mass_fraction)
    return sum(
        coef * temperature_c**temperature_order * tds**tds_order
        for coef, temperature_order, tds_order in BPE_COEFFS
    )


def water_pressure_sat(temperature_c):
    """Return pure-water saturation pressure in Pa."""
    temperature_k = float(temperature_c) + KELVIN_OFFSET
    coeffs = WATER_SAT_PRESSURE_COEFFS
    exponent = (
        coeffs["a1"] / temperature_k
        + coeffs["a2"]
        + coeffs["a3"] * temperature_k
        + coeffs["a4"] * temperature_k**2
        + coeffs["a5"] * temperature_k**3
        + coeffs["a6"] * math.log(temperature_k)
    )
    return math.exp(exponent)


def sw_pressure_sat(temperature_c, tds_mass_fraction):
    """Return seawater saturation pressure in Pa."""
    tds = _validate_tds_mass_fraction(tds_mass_fraction)
    salinity_g_per_kg = tds * 1000.0
    salinity_adjustment = sum(
        coef * salinity_g_per_kg**order
        for coef, order in SEAWATER_SAT_PRESSURE_COEFFS
    )
    return water_pressure_sat(float(temperature_c)) * math.exp(salinity_adjustment)


def CostIndexFactor(from_year, to_year):
    """Return CEPCI escalation factor from one year to another."""
    from_year = int(from_year)
    to_year = int(to_year)
    try:
        return CEPCI[to_year] / CEPCI[from_year]
    except KeyError as exc:
        years = f"{min(CEPCI)}-{max(CEPCI)}"
        raise ValueError(f"CEPCI data are only available for {years}.") from exc


def cost_index_factor(from_year, to_year):
    """PEP-8 alias for CostIndexFactor."""
    return CostIndexFactor(from_year, to_year)


def tds_mass_fraction_from_concentration(tds_concentration_g_l, temperature_c):
    """Convert TDS concentration in g/L to mass fraction."""
    concentration_kg_m3 = float(tds_concentration_g_l)
    if concentration_kg_m3 < 0:
        raise ValueError("TDS concentration must be non-negative.")

    tds = concentration_kg_m3 / water_dens_mass(temperature_c)
    for _ in range(20):
        density = sw_dens_mass(temperature_c, tds)
        next_tds = concentration_kg_m3 / density
        if abs(next_tds - tds) < 1e-12:
            return next_tds
        tds = next_tds
    return tds
