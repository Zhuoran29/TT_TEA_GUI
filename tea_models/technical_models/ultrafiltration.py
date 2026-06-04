from tea_models.technical_models.template_units import run_template


DEFAULTS = {
    "unit_kind": "uf",
    "recovery": 0.96,
    "energy_intensity": 0.12,
    "chemical_dose": 0.005,
}


def run(unit_process, technical_inputs, stream):
    return run_template(unit_process, technical_inputs, stream, DEFAULTS)
