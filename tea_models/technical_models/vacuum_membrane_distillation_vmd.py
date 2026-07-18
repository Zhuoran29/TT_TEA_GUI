"""Vacuum membrane distillation surrogate from the WaterTAP MD workbook.

The workbook's surrogate formulas use the following inputs:
    C7  = feed mass flow rate, kg/s
    C9  = feed TDS mass fraction
    C10 = feed temperature, deg C
    C12 = recovery ratio

The workbook labels the main energy output as SEEC, but it corresponds to the
WaterTAP heat flow cost and is therefore reported to the TEA framework as STEC
under ``thermal_energy_intensity``.
"""

from __future__ import annotations

import math

from tea_models.technical_models.helper_function import sw_dens_mass
from tea_models.water_quality import apply_unit_water_quality, get_default_removal_efficiencies


SECONDS_PER_DAY = 86_400.0
DEFAULT_CHILLER_COP = 7.0

_TDS_MEAN = 0.104636363636364
_DEFAULT_TDS_MASS_FRACTION = _TDS_MEAN
_TDS_STD = 0.0407358960026718
_RECOVERY_MEAN = 0.480909090909091
_RECOVERY_STD = 0.140288957995764
_TEMP_MEAN = 25.0
_TEMP_STD = 6.32455532033676


def _result(value, unit):
    return {"value": value, "unit": unit}


def _input(values, name, default):
    try:
        return float(values.get(name, default))
    except (TypeError, ValueError):
        return float(default)


def _stream_tds_mg_l(stream):
    entry = (stream.get("water_quality", {}) or {}).get("TDS", {}) or {}
    try:
        value = float(entry.get("value", 0.0) or 0.0)
    except (TypeError, ValueError):
        return 0.0
    unit = str(entry.get("unit", "mg/L") or "mg/L").lower().replace(" ", "")
    if unit in {"g/l", "kg/m3"}:
        return value * 1000.0
    return value


def _tds_mass_fraction(stream, temperature_c):
    concentration = _stream_tds_mg_l(stream)
    if concentration <= 0.0:
        return _DEFAULT_TDS_MASS_FRACTION
    fraction = min(max(concentration / 1_000_000.0, 0.0), 0.5)
    for _ in range(10):
        density = sw_dens_mass(temperature_c, fraction)
        fraction = concentration / max(density * 1000.0, 1e-12)
    return min(max(fraction, 0.0), 0.5)


def _z_inputs(tds_fraction, recovery, temperature_c):
    return (
        (tds_fraction - _TDS_MEAN) / _TDS_STD,
        (recovery - _RECOVERY_MEAN) / _RECOVERY_STD,
        (temperature_c - _TEMP_MEAN) / _TEMP_STD,
    )


def _poly(z, coeffs):
    x_tds, x_recovery, x_temp = z
    return (
        coeffs[0]
        + coeffs[1] * x_tds
        + coeffs[2] * x_recovery
        + coeffs[3] * x_temp
        + coeffs[4] * x_tds**2
        + coeffs[5] * x_tds * x_recovery
        + coeffs[6] * x_tds * x_temp
        + coeffs[7] * x_recovery**2
        + coeffs[8] * x_recovery * x_temp
        + coeffs[9] * x_temp**2
    )


def _exp_surrogate(z, coeffs):
    return math.exp(_poly(z, coeffs))


def _linear_surrogate(z, coeffs):
    return _poly(z, coeffs)


SURROGATES = {
    "brine_pump_power": ("exp", (1.08835688891815, 0.193079018393422, 0.462156033760062, -0.000708155440002554, 0.0189200798105618, 0.0790695161849348, 0.000325959050298217, 0.0210328398710013, -0.000953532392684691, -0.0010962607957302)),
    "brine_salinity_g_l": ("exp", (5.33279345965985, 0.434326949283316, 0.259692748241686, 1.63235781131262e-06, -0.0739982676480773, -0.0122701367916773, 9.75024263980246e-08, 0.045233661089915, 4.56715912170455e-06, 1.00802171046966e-05)),
    "chiller_power": ("linear", (-442.900275621987, -116.708038754654, -217.91128229845, -20.9986034596602, -2.03398980582771, -65.3111217935804, 0.924774681307008, -63.0769088462836, -0.0167454159857942, 2.63790113665073)),
    "effectiveness": ("linear", (77.9460779338089, -4.81233011272067, -3.13684633659373, 0.00122691339917285, -0.114674369013605, -1.10062627840466, -0.000617131114828404, -0.931469393958152, 0.0019113869096592, 0.0181916957721465)),
    "heat_exchanger_area_per_feed_mass_flow": ("exp", (5.58612896491198, 0.0871183866745585, 0.399603668505592, -0.00684816463537126, 0.0287926936545807, 0.0709388361187298, -0.00018912128071085, 0.000108242167732716, 0.00223932068067949, -0.00018992204014745)),
    "heater_power": ("exp", (6.04466077145759, 0.27200275919704, 0.509609380528188, -0.000319672085565621, -0.00643571147491498, 0.0551319673854233, 8.99018219712649e-05, 0.0177643004475976, -0.000118477837972614, -0.00139718163234339)),
    "lcow_feed": ("exp", (2.50890767209008, 0.294955067158052, 0.492236622540077, 0.00549768755638029, -0.00171724097194735, 0.0575909092142222, -0.00172888099410489, 0.017397243770475, -0.00278301133020773, -0.00138109454843386)),
    "lcow_permeate": ("exp", (3.24393917688364, 0.294995080551367, 0.18590845302857, 0.00549768755638028, -0.00209394325860039, 0.0577086940603676, -0.00172888099410491, 0.0567846963309893, -0.00278301133020774, -0.00138109454843386)),
    "membrane_area_per_feed_mass_flow": ("exp", (4.24968655014894, -0.0795221096432949, 0.287317325751157, -2.02592595002084e-05, 0.0241627401767641, 0.0331934357622422, -3.04904901285321e-05, -0.0276320666564176, -0.000120054386725021, -0.000132022284495552)),
    "permeate_pump_power": ("exp", (1.69781321939536, 0.159048281281259, 0.439449699777849, 0.000302514965986612, 0.0167789557258618, 0.0699448733250066, -0.000159043528113524, 0.0125814071148853, -3.14678341599947e-05, -0.00122246421559717)),
    "recycle_ratio": ("linear", (7.81869945940622, 2.41772972194068, 4.65050223981225, -0.00158121330651395, 0.23309467517074, 1.6037754430264, 0.000426211507466992, 1.35933201851435, -0.00321812470483121, -0.0410903112437036)),
    "stec_feed": ("exp", (5.03958413126092, 0.311039397373435, 0.501589512927506, 0.00624903074988383, -0.00635838428460338, 0.0539599085832146, -0.00201410447616318, 0.0178627949431653, -0.00322452292535271, -0.00143087658175342)),
    "stec_permeate": ("exp", (5.77461563605449, 0.311079410766749, 0.195261343415998, 0.00624903074988383, -0.00673508657125712, 0.0540776934293588, -0.0020141044761632, 0.0572502475036797, -0.00322452292535272, -0.00143087658175342)),
    "thermal_efficiency": ("linear", (55.8567594687379, -7.41716446408066, -4.68275219622208, 0.0014066537330436, 0.165685314805142, -1.34362031562688, -0.000602921878033973, -1.36505761957187, 0.00251428767038198, 0.0170848009633455)),
}


def _surrogate(name, z):
    kind, coeffs = SURROGATES[name]
    if kind == "exp":
        return _exp_surrogate(z, coeffs)
    return _linear_surrogate(z, coeffs)


def run(unit_process, technical_inputs, stream):
    inlet_flow = float(stream.get("flow_m3_day", 0.0) or 0.0)
    if inlet_flow <= 0.0:
        raise ValueError("VMD inlet flow must be positive.")

    recovery = min(max(_input(technical_inputs, "recovery", 0.50), 0.0), 0.999999)
    temperature = _input(technical_inputs, "feed_temperature", 25.0)
    tds_fraction = _tds_mass_fraction(
        stream,
        temperature,
    )

    feed_density = sw_dens_mass(temperature, tds_fraction)
    feed_mass_flow = inlet_flow / SECONDS_PER_DAY * feed_density
    z = _z_inputs(tds_fraction, recovery, temperature)

    inlet_quality = stream.get("water_quality", {})
    removals = technical_inputs.get("removal_efficiencies")
    if removals is None:
        removals = get_default_removal_efficiencies(unit_process, inlet_quality)
    (
        inlet_flow,
        outlet_flow,
        brine_flow,
        water_quality_in,
        water_quality_out,
        outlet_stream,
    ) = apply_unit_water_quality(stream, recovery, removals)

    membrane_area_per_flow = _surrogate("membrane_area_per_feed_mass_flow", z)
    hx_area_per_flow = _surrogate("heat_exchanger_area_per_feed_mass_flow", z)
    membrane_area = membrane_area_per_flow * feed_mass_flow
    heat_exchanger_area = hx_area_per_flow * feed_mass_flow
    recycle_ratio = max(_surrogate("recycle_ratio", z), 0.0)
    stec_feed = max(_surrogate("stec_feed", z), 0.0)
    stec_permeate = max(_surrogate("stec_permeate", z), 0.0)

    # The workbook power surrogates are normalized near a 1 kg/s feed case.
    heater_power = max(_surrogate("heater_power", z) * feed_mass_flow, 0.0)
    chiller_power = abs(_surrogate("chiller_power", z) * feed_mass_flow)
    brine_pump_power = max(_surrogate("brine_pump_power", z) * feed_mass_flow, 0.0)
    permeate_pump_power = max(_surrogate("permeate_pump_power", z) * feed_mass_flow, 0.0)
    chiller_electric_power = chiller_power / DEFAULT_CHILLER_COP
    auxiliary_electric_power = brine_pump_power + permeate_pump_power + chiller_electric_power
    electric_intensity = auxiliary_electric_power * 24.0 / max(inlet_flow, 1e-12)
    thermal_power_from_stec = stec_feed * inlet_flow / 24.0

    warnings = []
    if not 0.035 <= tds_fraction <= 0.175:
        warnings.append("Feed TDS is outside the surrogate training range of roughly 3.5-17.5 wt%.")
    if not 0.25 <= recovery <= 0.75:
        warnings.append("Recovery is outside the surrogate training range of roughly 25-75%.")
    if not 15.0 <= temperature <= 35.0:
        warnings.append("Feed temperature is outside the surrogate training range of roughly 15-35 C.")
    warnings.append(
        "Workbook SEEC is treated as STEC because WaterTAP reports heat-flow specific energy for this MD costing metric."
    )

    return {
        "inlet_flow": _result(inlet_flow, "m3/day"),
        "outlet_flow": _result(outlet_flow, "m3/day"),
        "brine_flow": _result(brine_flow, "m3/day"),
        "water_recovery": _result(recovery, "fraction"),
        "energy_intensity": _result(electric_intensity, "kWh/m3 feed"),
        "thermal_energy_intensity": _result(stec_feed, "kWh/m3 feed"),
        "removal_efficiencies": removals,
        "water_quality_in": water_quality_in,
        "water_quality_out": water_quality_out,
        "outlet_stream": outlet_stream,
        "feed_tds_mass_fraction": _result(tds_fraction, "fraction"),
        "feed_temperature": _result(temperature, "deg C"),
        "feed_mass_flow": _result(feed_mass_flow, "kg/s"),
        "feed_density": _result(feed_density, "kg/m3"),
        "recycle_ratio": _result(recycle_ratio, "recycle/feed"),
        "brine_salinity": _result(_surrogate("brine_salinity_g_l", z), "g/L"),
        "membrane_area": _result(membrane_area, "m2"),
        "membrane_area_per_feed_mass_flow": _result(membrane_area_per_flow, "m2/(kg/s)"),
        "heat_exchanger_area": _result(heat_exchanger_area, "m2"),
        "heat_exchanger_area_per_feed_mass_flow": _result(hx_area_per_flow, "m2/(kg/s)"),
        "heater_thermal_duty": _result(heater_power, "kW"),
        "chiller_thermal_duty": _result(chiller_power, "kW"),
        "chiller_electric_power": _result(chiller_electric_power, "kW"),
        "thermal_power_from_stec": _result(thermal_power_from_stec, "kW"),
        "brine_pump_power": _result(brine_pump_power, "kW"),
        "permeate_pump_power": _result(permeate_pump_power, "kW"),
        "auxiliary_electric_power": _result(auxiliary_electric_power, "kW"),
        "total_electric_power": _result(auxiliary_electric_power, "kW"),
        "seec_reported_by_workbook": _result(stec_feed, "kWh/m3 feed"),
        "stec_feed": _result(stec_feed, "kWh/m3 feed"),
        "stec_permeate": _result(stec_permeate, "kWh/m3 permeate"),
        "thermal_efficiency": _result(_surrogate("thermal_efficiency", z), "%"),
        "heat_exchanger_effectiveness": _result(_surrogate("effectiveness", z), "%"),
        "surrogate_lcow_feed": _result(_surrogate("lcow_feed", z), "USD/m3 feed"),
        "surrogate_lcow_permeate": _result(_surrogate("lcow_permeate", z), "USD/m3 permeate"),
        "model_warnings": _result(warnings, ""),
    }
