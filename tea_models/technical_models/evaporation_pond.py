from tea_models.technical_models.template_units import run_template


DEFAULTS = {
    "unit_kind": "pond",
    "recovery": 1.0,
    "energy_intensity": 0.0,
    "chemical_dose": 0.0,
}


def run(unit_process, technical_inputs, stream):
    return run_template(unit_process, technical_inputs, stream, DEFAULTS)
