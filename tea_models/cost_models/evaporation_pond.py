from tea_models.cost_models.template_units import run_template


DEFAULTS = {
    "capex_per_flow": 8.0,
    "fixed_opex_fraction": 0.03,
    "variable_opex_per_m3": 0.01,
    "land_cost_per_m2": 0.8,
    "liner_cost_per_m2": 4.8,
}


def run(unit_process, technical_result, cost_inputs, context):
    return run_template(technical_result, cost_inputs, context, DEFAULTS)
