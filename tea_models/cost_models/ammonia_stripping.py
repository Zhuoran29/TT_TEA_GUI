"""Ammonia stripping cost model from the NMPWRC air-stripper workbook curve."""

from __future__ import annotations

import math

from tea_models.cost_models.cost_utils import cost_index_factor_to_base, escalate_cost, input_value, result, value


DEFAULTS = {
    "capital_cost_multiplier": 1.0,
    "opex_cost_multiplier": 1.0,
}

M3_DAY_PER_MGD = 3785.411784
WORKBOOK_COST_YEAR = 2021

# Air Strip Cost Model worksheet, rows 4:8 and S:T, full unit-process CIP costs.
FLOW_MGD = [0.1, 1.0, 5.0, 15.0, 30.0]
FULL_CAPEX_2021 = [
    1297015.5986577275,
    2786001.3471833305,
    5921125.3156908322,
    11748288.033765184,
    22018150.923276156,
]
FULL_OPEX_2021 = [
    23591.802722679688,
    264383.27774303086,
    1306365.3391753056,
    3913166.0013205549,
    7840408.487720645,
]


def _input(values, name, default):
    try:
        return float(values.get(name, default))
    except (TypeError, ValueError):
        return float(default)


def _log_interpolate(x, xs, ys):
    x = max(float(x or 0.0), 1e-12)
    if x <= xs[0]:
        left, right = 0, 1
    elif x >= xs[-1]:
        left, right = len(xs) - 2, len(xs) - 1
    else:
        left, right = 0, 1
        for idx in range(len(xs) - 1):
            if xs[idx] <= x <= xs[idx + 1]:
                left, right = idx, idx + 1
                break

    x1, x2 = xs[left], xs[right]
    y1, y2 = ys[left], ys[right]
    exponent = math.log(y2 / y1) / math.log(x2 / x1)
    return y1 * (x / x1) ** exponent, exponent


def run(unit_process, technical_result, cost_inputs, context):
    inlet_flow = value(technical_result, "inlet_flow")
    flow_mgd = inlet_flow / M3_DAY_PER_MGD
    cost_index_factor = cost_index_factor_to_base(context, WORKBOOK_COST_YEAR)
    capex_multiplier = max(_input(cost_inputs, "capital_cost_multiplier", DEFAULTS["capital_cost_multiplier"]), 0.0)
    opex_multiplier = max(_input(cost_inputs, "opex_cost_multiplier", DEFAULTS["opex_cost_multiplier"]), 0.0)

    capex_2021, capex_exponent = _log_interpolate(flow_mgd, FLOW_MGD, FULL_CAPEX_2021)
    opex_2021, opex_exponent = _log_interpolate(flow_mgd, FLOW_MGD, FULL_OPEX_2021)
    installed_capex = capex_2021 * cost_index_factor * capex_multiplier
    annual_opex = opex_2021 * cost_index_factor * opex_multiplier

    override_variable_opex = escalate_cost(
        input_value(cost_inputs, "variable_opex_per_m3", 0.0),
        cost_inputs,
        "variable_opex_per_m3",
        context,
    )
    if override_variable_opex > 0.0:
        operating_days = float(context.get("operating_days_per_year", 330.0))
        annual_opex += inlet_flow * operating_days * override_variable_opex

    return {
        "installed_capital_cost": result(installed_capex, "USD"),
        "equipment_capital_cost": result(installed_capex, "USD"),
        "workbook_capex_2021": result(capex_2021, "USD"),
        "workbook_opex_2021": result(opex_2021, "USD/year"),
        "cost_index_factor": result(cost_index_factor, "factor"),
        "capital_cost_multiplier": result(capex_multiplier, "-"),
        "opex_cost_multiplier": result(opex_multiplier, "-"),
        "capex_curve_exponent": result(capex_exponent, "exponent"),
        "opex_curve_exponent": result(opex_exponent, "exponent"),
        "variable_operating_cost": result(annual_opex, "USD/year"),
        "total_annual_operating_cost": result(annual_opex, "USD/year"),
    }
