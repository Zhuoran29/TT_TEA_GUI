"""BWRO cost model adapted to the TEA framework's feed-normalized reporting.

The source ``BWRO_cost.py`` reports USD/m3 product and performs its own capital
annualization.  Here, product-basis rates are converted to annual dollar costs;
the shared framework applies its project life/discount-rate CRF once and divides
the complete treatment train by the original feed volume.
"""

from __future__ import annotations


def _result(value, unit):
    return {"value": value, "unit": unit}


def _value(result, name, default=0.0):
    entry = result.get(name, {})
    try:
        if isinstance(entry, dict):
            return float(entry.get("value", default) or default)
        return float(entry or default)
    except (TypeError, ValueError):
        return float(default)


def _input(values, name, default):
    try:
        return float(values.get(name, default))
    except (TypeError, ValueError):
        return float(default)


def run(unit_process, technical_result, cost_inputs, context):
    product_capacity = _value(technical_result, "outlet_flow")
    feed_capacity = _value(technical_result, "inlet_flow")
    brine_capacity = _value(technical_result, "brine_flow")
    recovery = _value(technical_result, "water_recovery", 0.8)
    operating_days = float(context.get("operating_days_per_year", 330.0))
    annual_product = product_capacity * operating_days
    annual_feed = feed_capacity * operating_days
    annual_brine = brine_capacity * operating_days
    if product_capacity <= 0 or annual_product <= 0 or not 0 < recovery < 1:
        raise ValueError("BWRO product flow and recovery must be positive.")

    total_installed_cost = _input(cost_inputs, "total_installed_cost", 0.0)
    unit_capex = _input(cost_inputs, "unit_capex", 0.0)
    reference_unit_capex = _input(cost_inputs, "reference_unit_capex", 1500.0)
    reference_capacity = _input(cost_inputs, "reference_capacity", 1000.0)
    scaling_exponent = _input(cost_inputs, "capex_scaling_exponent", -0.15)
    cost_index_factor = _input(cost_inputs, "cost_index_factor", 1.0)
    if total_installed_cost > 0:
        installed_capex = total_installed_cost * cost_index_factor
        capex_method = "user-specified total installed cost"
    elif unit_capex > 0:
        installed_capex = unit_capex * product_capacity * cost_index_factor
        capex_method = "user-specified unit CAPEX"
    else:
        if reference_unit_capex < 0 or reference_capacity <= 0:
            raise ValueError("BWRO reference CAPEX must be nonnegative and capacity positive.")
        scaled_unit_capex = reference_unit_capex * (
            product_capacity / reference_capacity
        ) ** scaling_exponent
        installed_capex = scaled_unit_capex * product_capacity * cost_index_factor
        capex_method = "screening product-capacity correlation"

    fixed_om_fraction = _input(cost_inputs, "fixed_om_fraction", 0.035)
    insurance_fraction = _input(cost_inputs, "insurance_fraction", 0.005)
    membrane_cost = _input(cost_inputs, "membrane_cost", 30.0)
    membrane_replacement_fraction = _input(
        cost_inputs, "membrane_replacement_fraction", 0.20
    )
    membrane_area = _value(technical_result, "membrane_area")

    chemical_rate = _input(cost_inputs, "chemical_cost_per_m3_product", 0.03)
    labor_rate = _input(cost_inputs, "labor_cost_per_m3_product", 0.05)
    pretreatment_rate = _input(cost_inputs, "pretreatment_cost_per_m3_product", 0.0)
    posttreatment_rate = _input(cost_inputs, "posttreatment_cost_per_m3_product", 0.0)
    other_rate = _input(cost_inputs, "other_variable_cost_per_m3_product", 0.0)
    intake_rate = _input(cost_inputs, "intake_water_cost_per_m3_feed", 0.0)
    brine_rate = _input(cost_inputs, "brine_disposal_cost_per_m3_concentrate", 0.0)

    nonnegative = [
        cost_index_factor,
        fixed_om_fraction,
        insurance_fraction,
        membrane_cost,
        membrane_replacement_fraction,
        chemical_rate,
        labor_rate,
        pretreatment_rate,
        posttreatment_rate,
        other_rate,
        intake_rate,
        brine_rate,
    ]
    if any(value < 0 for value in nonnegative):
        raise ValueError("BWRO cost inputs and factors cannot be negative.")

    fixed_om = installed_capex * fixed_om_fraction
    insurance = installed_capex * insurance_fraction
    membranes = (
        membrane_area * membrane_cost * membrane_replacement_fraction * cost_index_factor
    )
    electricity = (
        annual_product
        * _value(technical_result, "energy_intensity")
        * float(context.get("electricity_price", 0.0))
    )
    product_variable_rate = (
        chemical_rate + labor_rate + pretreatment_rate + posttreatment_rate + other_rate
    )
    product_variable = annual_product * product_variable_rate
    intake = annual_feed * intake_rate
    brine_disposal = annual_brine * brine_rate
    annual_opex = (
        fixed_om
        + insurance
        + membranes
        + electricity
        + product_variable
        + intake
        + brine_disposal
    )

    # Diagnostic product-basis OPEX only. Capital is annualized centrally using
    # the framework CRF, so no project life or interest rate is duplicated here.
    product_opex = annual_opex / annual_product
    return {
        "installed_capital_cost": _result(installed_capex, "USD"),
        "equipment_capital_cost": _result(installed_capex, "USD"),
        "capex_estimation_method": _result(capex_method, ""),
        "fixed_operating_cost": _result(fixed_om, "USD/year"),
        "insurance_cost": _result(insurance, "USD/year"),
        "membrane_replacement_cost": _result(membranes, "USD/year"),
        "energy_operating_cost": _result(electricity, "USD/year"),
        "product_variable_operating_cost": _result(product_variable, "USD/year"),
        "source_water_operating_cost": _result(intake, "USD/year"),
        "brine_disposal_operating_cost": _result(brine_disposal, "USD/year"),
        "total_annual_operating_cost": _result(annual_opex, "USD/year"),
        "annual_product_volume": _result(annual_product, "m3/year"),
        "annual_feed_volume": _result(annual_feed, "m3/year"),
        "annual_concentrate_volume": _result(annual_brine, "m3/year"),
        "opex_per_product_volume": _result(product_opex, "USD/m3 product"),
    }
