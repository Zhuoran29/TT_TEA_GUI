"""Ion exchange (demineralization) cost model: SAC + SBA beds, HCl and NaOH regeneration.

See tea_models.cost_models.ion_exchange for the equations.
"""

from tea_models.cost_models.ion_exchange import DEMIN_DEFAULTS as DEFAULTS, run_cost


def run(unit_process, technical_result, cost_inputs, context):
    return run_cost(unit_process, technical_result, cost_inputs, context, DEFAULTS)
