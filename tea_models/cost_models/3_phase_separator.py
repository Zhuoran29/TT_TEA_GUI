from tea_models.cost_models.template_units import run_template


DEFAULTS = {
    "capex_per_flow": 180.0,
    "fixed_opex_fraction": 0.04,
    "variable_opex_per_m3": 0.01,
    "electricity_price": 0.08,
}


def run(unit_process, technical_result, cost_inputs, context):
    return run_template(technical_result, cost_inputs, context, DEFAULTS)
