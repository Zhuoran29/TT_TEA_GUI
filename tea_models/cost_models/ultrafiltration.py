from tea_models.cost_models.template_units import run_template


DEFAULTS = {
    "capex_per_flow": 500.0,
    "fixed_opex_fraction": 0.05,
    "variable_opex_per_m3": 0.04,
    "electricity_price": 0.08,
    "chemical_price": 1.0,
    "media_replacement_price": 35.0,
    "media_replacement_fraction": 0.12,
}


def run(unit_process, technical_result, cost_inputs, context):
    return run_template(technical_result, cost_inputs, context, DEFAULTS)
