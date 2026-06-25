from tea_models.technical_models.template_units import run_template
from tea_models.unit_model_defaults import (
    supports_technical,
    technical_defaults,
)


def supports(unit_process):
    return supports_technical(unit_process)


def run(unit_process, technical_inputs, stream):
    return run_template(unit_process, technical_inputs, stream, technical_defaults(unit_process))
