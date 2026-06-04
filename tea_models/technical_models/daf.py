from tea_models.technical_models.template_units import run_template


DEFAULTS = {
    "unit_kind": "daf",
    "recovery": 0.98,
    "energy_intensity": 0.08,
    "chemical_dose": 0.03,
}


def run(unit_process, technical_inputs, stream):
    return run_template(unit_process, technical_inputs, stream, DEFAULTS)
