"""Mechanical vapor compression technical model.

Surrogate equations are translated from MVC.xlsx cells L16 and L25:L38.
"""

from __future__ import annotations

import math

from tea_models.technical_models.helper_function import sw_dens_mass, water_dens_mass
from tea_models.water_quality import (
    apply_unit_water_quality,
    get_default_removal_efficiencies,
)


M3_PER_MGD = 3785.411784
SECONDS_PER_DAY = 86_400.0


def _input(technical_inputs, name, default):
    value = technical_inputs.get(name, default)
    if value is None:
        return float(default)
    return float(value)


def _norm(value, mean, scale):
    return (float(value) - mean) / scale


def _surface(x, y, z, coeffs):
    return (
        coeffs[0]
        + coeffs[1] * x
        + coeffs[2] * y
        + coeffs[3] * z
        + coeffs[4] * x**2
        + coeffs[5] * x * y
        + coeffs[6] * x * z
        + coeffs[7] * y**2
        + coeffs[8] * y * z
        + coeffs[9] * z**2
    )


def _result(value, unit):
    return {"value": value, "unit": unit}


def run(unit_process, technical_inputs, stream):
    inlet_flow = float(stream.get("flow_m3_day", 0.0) or 0.0)
    feed_flow_m3_s = inlet_flow / SECONDS_PER_DAY

    feed_tds = _input(technical_inputs, "feed_tds_mass_fraction", 0.154)
    feed_temperature = _input(technical_inputs, "feed_temperature", 25.0)
    recovery = _input(technical_inputs, "recovery", 0.45)
    recovery = max(0.0, min(recovery, 0.999999))
    inlet_quality = stream.get("water_quality", {})
    removal_efficiencies = technical_inputs.get("removal_efficiencies")
    if removal_efficiencies is None:
        removal_efficiencies = get_default_removal_efficiencies(unit_process, inlet_quality)
    target_values = technical_inputs.get("target_values", {})
    if "target_pH" in technical_inputs:
        target_values = {**target_values, "pH": technical_inputs["target_pH"]}
    if "target_ph" in technical_inputs:
        target_values = {**target_values, "pH": technical_inputs["target_ph"]}

    feed_density = sw_dens_mass(feed_temperature, feed_tds)
    feed_h2o_mass_flow = feed_flow_m3_s * feed_density * (1.0 - feed_tds)
    (
        inlet_flow,
        outlet_flow,
        brine_flow,
        water_quality_in,
        water_quality_out,
        outlet_stream,
    ) = apply_unit_water_quality(stream, recovery, removal_efficiencies, target_values)

    x = _norm(feed_tds, 0.0979460957660327, 0.0371437477194878)
    y = _norm(recovery, 0.462864379241135, 0.131900819203958)
    z = _norm(feed_temperature, 24.9900602121762, 6.32630022789431)

    l25 = math.exp(_surface(x, y, z, (
        5.2991724550459,
        0.460510752764032,
        0.27807787256851,
        -0.00123145881877445,
        -0.065797371343884,
        0.0105404269584629,
        -0.000794893982155385,
        0.0552363130480272,
        0.000369284510955899,
        -0.000300892974975408,
    )))
    l26 = math.exp(_surface(x, y, z, (
        2.91089577559312,
        0.0360219512543886,
        0.209075331141344,
        -0.00700909710972457,
        0.0133627037707581,
        0.00533319095636329,
        0.000288479471659992,
        0.00882440958102116,
        0.0108962397439139,
        -0.0000579946718178803,
    ))) * feed_h2o_mass_flow
    l27 = math.exp(_surface(x, y, z, (
        3.21376122814688,
        -0.171818583269744,
        0.82000800649903,
        0.174177722519546,
        -0.174961879223373,
        -0.224283995914913,
        -0.00689399582587829,
        -0.467277389556597,
        -0.14650036621398,
        -0.00501450781431941,
    )))
    l28 = math.exp(_surface(x, y, z, (
        3.68590553837297,
        -0.123490704611723,
        0.843132557789914,
        0.16947129004912,
        -0.167250886146687,
        -0.200513520951597,
        -0.00684267531541299,
        -0.454144056103779,
        -0.144485482753333,
        -0.00485066456131585,
    )))
    l29 = math.exp(_surface(x, y, z, (
        4.77058205951845,
        0.0309719315490126,
        0.235129217194045,
        0.0388504921352216,
        -0.0326582760663689,
        -0.0290378271913102,
        -0.00318890684389036,
        -0.0981279462630197,
        -0.0359874808521932,
        -0.00161145877814376,
    )))
    l30 = _surface(x, y, z, (
        1.60422447880102,
        0.0769764125626131,
        0.0380650545528094,
        -0.00708407638579959,
        0.0147061054850293,
        0.039470172823339,
        -0.00123089827294903,
        0.020428366465375,
        0.0025758253529689,
        0.000216526979206588,
    ))
    l31 = math.exp(_surface(x, y, z, (
        4.13212314590142,
        -0.0374556431107663,
        0.388551425189684,
        0.10509571877293,
        -0.0693546041360372,
        -0.0845533648626574,
        -0.00209010246818985,
        -0.213521534141218,
        -0.0923366285021097,
        -0.0117742586083469,
    )))
    l32 = math.exp(_surface(x, y, z, (
        4.32137611512525,
        -0.042090046609717,
        0.321696109489111,
        0.0763937689631469,
        -0.0674188330605194,
        -0.0727166623182486,
        -0.000748876098328288,
        -0.171576008657065,
        -0.0668994527802507,
        -0.00617956400380338,
    )))

    x33 = _norm(feed_tds, 0.0881465237166992, 0.0281124627983501)
    y33 = _norm(recovery, 0.528971734892788, 0.101531795531635)
    z33 = _norm(feed_temperature, 24.9873294346979, 6.32644300078804)
    l33 = math.exp(_surface(x33, y33, z33, (
        1.39224499326364,
        -0.0575564637211795,
        -0.387580872655209,
        -0.118613530042505,
        -0.00712115538148424,
        0.0447497928041697,
        0.00527110718087138,
        -0.0760066495426587,
        -0.028462954452058,
        -0.0136926826635352,
    ))) * feed_h2o_mass_flow

    x34 = _norm(feed_tds, 0.0867174996225276, 0.0279735818346055)
    y34 = _norm(recovery, 0.536735618299864, 0.105704872958828)
    z34 = _norm(feed_temperature, 25.0286879057829, 6.32100373536852)
    l34 = math.exp(_surface(x34, y34, z34, (
        1.75159844851389,
        -0.000511193013170992,
        0.0914567998764919,
        -0.0965758591902102,
        -0.0923418109891364,
        -0.120224895206411,
        -0.0315438776534937,
        -0.166086301257829,
        -0.0783994677294938,
        -0.0133496391921447,
    ))) * feed_h2o_mass_flow

    l35 = math.exp(_surface(x, y, z, (
        12.1221263623055,
        0.0360242668321297,
        0.209110558714533,
        -0.00701324845670036,
        0.0133449654721739,
        0.00529099286982857,
        0.000285723270712021,
        0.00877296545377042,
        0.010892764933723,
        -0.000073744664654135,
    ))) * feed_h2o_mass_flow**1.002936235
    l36 = math.exp(_surface(x, y, z, (
        10.7950239103402,
        0.0895263236305439,
        0.320939475471495,
        -0.00470753228168846,
        0.00866371421837752,
        0.023809558581282,
        0.0000558158679927265,
        -0.0230270187989793,
        0.00201693574954204,
        0.000183154913912125,
    ))) * feed_h2o_mass_flow**0.9998361497
    l37 = math.exp(_surface(x, y, z, (
        10.4895910029321,
        0.141256353502776,
        0.356103759830611,
        -0.00604019368871803,
        0.0104637424686718,
        0.0426158948784617,
        0.00134150661167394,
        -0.0160235984809652,
        0.000942812958435616,
        -0.0000588417604917824,
    ))) * feed_h2o_mass_flow**0.998836418
    l38 = _surface(x, y, z, (
        0.654455270453957,
        -0.0536218906232339,
        -0.0528596260648409,
        -0.00292539113741298,
        -0.00220152010521286,
        -0.0209395494487105,
        -0.000768432725263067,
        -0.0065455310308751,
        0.00170779200144479,
        4.51680477907546e-06,
    ))

    density_at_condenser = water_dens_mass(l32)
    if feed_flow_m3_s > 0.0:
        l16 = (
            math.exp(_surface(x, y, z, (
                3.09165809966988,
                0.0998086869587713,
                0.0571980523864993,
                -0.0082069587166399,
                0.009776293529238,
                0.0424667261970504,
                0.00135459285200456,
                0.0201753339512687,
                0.000856811483274561,
                -0.000234224285269729,
            )))
            * feed_h2o_mass_flow
            / max(1.0 - feed_tds, 1e-12)
            * recovery
            / density_at_condenser
            / feed_flow_m3_s
        )
    else:
        l16 = 0.0

    return {
        "inlet_flow": _result(inlet_flow, "m3/day"),
        "outlet_flow": _result(outlet_flow, "m3/day"),
        "brine_flow": _result(brine_flow, "m3/day"),
        "water_recovery": _result(recovery, "fraction"),
        "energy_intensity": _result(l16, "kWh/m3 feed"),
        "constituent_removal_efficiency": _result(0.999, "fraction"),
        "removal_efficiencies": removal_efficiencies,
        "water_quality_in": water_quality_in,
        "water_quality_out": water_quality_out,
        "outlet_stream": outlet_stream,
        "chemical_dose": _result(0.0, "kg/m3"),
        "feed_h2o_mass_flow": _result(feed_h2o_mass_flow, "kg/s"),
        "feed_tds_mass_fraction": _result(feed_tds, "fraction"),
        "feed_temperature": _result(feed_temperature, "deg C"),
        "specific_electric_energy_consumption": _result(l16, "kWh/m3 feed"),
        "brine_salinity": _result(l25, "g/L"),
        "evaporator_area": _result(l26, "m2"),
        "evaporator_pressure": _result(l27, "kPa"),
        "compressed_vapor_pressure": _result(l28, "kPa"),
        "compressed_vapor_temperature": _result(l29, "deg C"),
        "compressor_pressure_ratio": _result(l30, ""),
        "preheated_feed_temperature": _result(l31, "deg C"),
        "condenser_vapor_temperature": _result(l32, "deg C"),
        "brine_hx_area": _result(l33, "m2"),
        "distillate_hx_area": _result(l34, "m2"),
        "evaporator_capex": _result(l35, "USD"),
        "compressor_capex": _result(l36, "USD"),
        "electricity_cost": _result(l37, "USD/year"),
        "capex_opex_ratio": _result(l38, ""),
    }
