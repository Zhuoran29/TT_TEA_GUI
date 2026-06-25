from tea_models.cost_models.template_units import run_template
from tea_models.unit_model_defaults import (
    cost_defaults,
    supports_cost,
)


def supports(unit_process):
    return supports_cost(unit_process)


def run(unit_process, technical_result, cost_inputs, context):
    return run_template(technical_result, cost_inputs, context, cost_defaults(unit_process))
