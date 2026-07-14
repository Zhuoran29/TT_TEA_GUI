"""Zeolite capital/fixed cost plus regeneration and NH4Cl-credit OPEX."""

from __future__ import annotations


DEFAULTS = {
    "capex_per_flow": 774.4,
    "fixed_opex_fraction": 0.04,
    "zeolite_price": 0.16,
    "media_loss_fraction": 0.10,
    "solid_disposal_cost": 0.11,
    "regeneration_reuses": 5.0,
    "bench_regenerant_volume": 0.90,
    "bench_zeolite_mass": 0.00824,
    "salt_mass_fraction": 0.10,
    "salt_solution_density": 1.071,
    "salt_price": 0.03,
    "nh4cl_price": 250.0,
    "nh4cl_recovery_factor": 19.08 / 19.99,
    "nh4cl_capture_fraction": 1.0,
}
N_TO_NH4CL_MASS_RATIO = 53.491 / 14.007


def _result(value, unit):
    return {"value": value, "unit": unit}


def _value(result, name, default=0.0):
    entry = result.get(name, {})
    try:
        return float(entry.get("value", default) if isinstance(entry, dict) else entry)
    except (TypeError, ValueError):
        return float(default)


def _input(values, name, default):
    try:
        return float(values.get(name, default))
    except (TypeError, ValueError):
        return float(default)


def run(unit_process, technical_result, cost_inputs, context):
    inlet_flow = _value(technical_result, "inlet_flow")
    operating_days = float(context.get("operating_days_per_year", 330.0))
    annual_volume = inlet_flow * operating_days
    investment_factor = max(float(context.get("investment_factor", 2.5)), 0.0)

    equipment_capex = _input(
        cost_inputs, "capex_per_flow", DEFAULTS["capex_per_flow"]
    ) * inlet_flow
    installed_capex = equipment_capex * investment_factor
    fixed_opex = installed_capex * _input(
        cost_inputs, "fixed_opex_fraction", DEFAULTS["fixed_opex_fraction"]
    )

    inventory = _value(technical_result, "media_inventory")
    cycle_days = _value(technical_result, "cycle_duration")
    cycles = operating_days / cycle_days if cycle_days > 0.0 else 0.0
    zeolite_price = _input(cost_inputs, "zeolite_price", DEFAULTS["zeolite_price"])
    media_loss = _input(
        cost_inputs, "media_loss_fraction", DEFAULTS["media_loss_fraction"]
    )
    disposal_price = _input(
        cost_inputs, "solid_disposal_cost", DEFAULTS["solid_disposal_cost"]
    )

    regeneration_reuses = _input(
        cost_inputs, "regeneration_reuses", DEFAULTS["regeneration_reuses"]
    )
    bench_regenerant_volume = _input(
        cost_inputs,
        "bench_regenerant_volume",
        DEFAULTS["bench_regenerant_volume"],
    )
    bench_zeolite_mass = _input(
        cost_inputs, "bench_zeolite_mass", DEFAULTS["bench_zeolite_mass"]
    )
    salt_fraction = _input(
        cost_inputs, "salt_mass_fraction", DEFAULTS["salt_mass_fraction"]
    )
    salt_density = _input(
        cost_inputs, "salt_solution_density", DEFAULTS["salt_solution_density"]
    )
    salt_price = _input(cost_inputs, "salt_price", DEFAULTS["salt_price"])
    nh4cl_price = _input(cost_inputs, "nh4cl_price", DEFAULTS["nh4cl_price"])
    recovery_factor = _input(
        cost_inputs, "nh4cl_recovery_factor", DEFAULTS["nh4cl_recovery_factor"]
    )
    capture_fraction = _input(
        cost_inputs, "nh4cl_capture_fraction", DEFAULTS["nh4cl_capture_fraction"]
    )
    if regeneration_reuses <= 0.0 or bench_zeolite_mass <= 0.0:
        raise ValueError("Zeolite regeneration reuses and bench media mass must be positive.")
    if any(value < 0.0 for value in (
        zeolite_price,
        media_loss,
        disposal_price,
        bench_regenerant_volume,
        salt_fraction,
        salt_density,
        salt_price,
        nh4cl_price,
        recovery_factor,
        capture_fraction,
    )):
        raise ValueError("Zeolite cost inputs and recovery factors cannot be negative.")
    fresh_regenerant_l_per_kg = (
        bench_regenerant_volume
        / max(regeneration_reuses, 1e-12)
        / max(bench_zeolite_mass, 1e-12)
    )
    regenerant_l_cycle = fresh_regenerant_l_per_kg * inventory
    salt_kg_cycle = (
        regenerant_l_cycle
        * salt_density
        * salt_fraction
    )
    salt_opex = cycles * salt_kg_cycle * salt_price
    makeup_opex = cycles * inventory * media_loss * zeolite_price
    replacement_opex = cycles * inventory * zeolite_price
    disposal_opex = cycles * inventory * disposal_price

    annual_removed_n = _value(technical_result, "ammonia_removed") * operating_days
    nh4cl_tonnes = (
        annual_removed_n
        * recovery_factor
        * capture_fraction
        * N_TO_NH4CL_MASS_RATIO
        / 1000.0
    )
    credit = nh4cl_tonnes * nh4cl_price
    energy_opex = (
        annual_volume
        * _value(technical_result, "energy_intensity")
        * float(context.get("electricity_price", 0.0))
    )
    variable_opex = (
        salt_opex
        + makeup_opex
        + replacement_opex
        + disposal_opex
        + energy_opex
        - credit
    )
    total_opex = fixed_opex + variable_opex

    return {
        "installed_capital_cost": _result(installed_capex, "USD"),
        "equipment_capital_cost": _result(equipment_capex, "USD"),
        "investment_factor": _result(investment_factor, "-"),
        "fixed_operating_cost": _result(fixed_opex, "USD/year"),
        "regeneration_salt_operating_cost": _result(salt_opex, "USD/year"),
        "zeolite_makeup_operating_cost": _result(makeup_opex, "USD/year"),
        "zeolite_replacement_operating_cost": _result(replacement_opex, "USD/year"),
        "solid_disposal_operating_cost": _result(disposal_opex, "USD/year"),
        "energy_operating_cost": _result(energy_opex, "USD/year"),
        "nh4cl_revenue_credit": _result(-credit, "USD/year"),
        "variable_operating_cost": _result(variable_opex, "USD/year"),
        "total_annual_operating_cost": _result(total_opex, "USD/year"),
        "regeneration_cycles": _result(cycles, "cycles/year"),
        "annual_nh4cl_product": _result(nh4cl_tonnes, "metric tonne/year"),
    }
