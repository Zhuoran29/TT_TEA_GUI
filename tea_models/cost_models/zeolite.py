from tea_models.cost_models.template_units import run_template


DEFAULTS = {
    "capex_per_flow": 1936.0,
    "fixed_opex_fraction": 0.04,
    "variable_opex_per_m3": 1.51,
    "electricity_price": 0.08,
    "media_replacement_price": 0.8,
    "media_replacement_fraction": 0.5,
}


def run(unit_process, technical_result, cost_inputs, context):
    return run_template(technical_result, cost_inputs, context, DEFAULTS)
