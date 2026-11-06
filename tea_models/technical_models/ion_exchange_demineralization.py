"""Ion exchange (demineralization): H-form SAC + OH-form SBA, HCl/NaOH regeneration.

See tea_models.technical_models.ion_exchange for the equations.
"""

from tea_models.technical_models.ion_exchange import DEMIN_DEFAULTS as DEFAULTS, run_ix


def run(unit_process, technical_inputs, stream):
    return run_ix(unit_process, technical_inputs, stream, demineralization=True)
