from tea_models.technical_models.template_units import run_template


DEFAULTS = {
    "unit_kind": "zeolite",
    "recovery": 0.995,
    "energy_intensity": 0.04,
    "chemical_dose": 0.0,
    "empty_bed_contact_time": 8.0,
    "media_bulk_density": 700.0,
}


def run(unit_process, technical_inputs, stream):
    return run_template(unit_process, technical_inputs, stream, DEFAULTS)
