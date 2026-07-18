from tea_models.technical_models.template_units import run_template
from tea_models.unit_model_defaults import technical_defaults


PA_PER_PSI = 6894.757293168


def _input(values, name, default):
    try:
        return float(values.get(name, default))
    except (TypeError, ValueError):
        return float(default)


def _result(value, unit):
    return {"value": value, "unit": unit}


def _pressure_drop_energy_kwh_m3(pressure_drop_psi, pump_efficiency):
    return (
        max(float(pressure_drop_psi), 0.0)
        * PA_PER_PSI
        / max(float(pump_efficiency), 1e-9)
        / 3_600_000.0
    )


def run(unit_process, technical_inputs, stream):
    defaults = technical_defaults(unit_process)
    pressure_drop_psi = _input(
        technical_inputs,
        "pressure_drop_psi",
        defaults.get("pressure_drop_psi", 70.0),
    )
    pump_efficiency = _input(
        technical_inputs,
        "pump_efficiency",
        defaults.get("pump_efficiency", 0.70),
    )
    auxiliary_energy = _input(
        technical_inputs,
        "auxiliary_energy_intensity",
        defaults.get("auxiliary_energy_intensity", 0.0),
    )
    direct_energy = _input(
        technical_inputs,
        "energy_intensity",
        defaults.get("energy_intensity", 0.0),
    )
    main_pump_energy = _pressure_drop_energy_kwh_m3(pressure_drop_psi, pump_efficiency)
    energy_intensity = direct_energy if direct_energy > 0.0 else main_pump_energy + auxiliary_energy

    calculated_inputs = dict(technical_inputs)
    calculated_inputs["energy_intensity"] = energy_intensity
    outputs = run_template(unit_process, calculated_inputs, stream, defaults)
    inlet_flow = outputs["inlet_flow"]["value"]
    outputs.update({
        "pressure_drop": _result(pressure_drop_psi, "psi"),
        "pump_efficiency": _result(pump_efficiency, "fraction"),
        "main_pump_energy_intensity": _result(main_pump_energy, "kWh/m3"),
        "auxiliary_energy_intensity": _result(auxiliary_energy, "kWh/m3"),
        "main_pump_power": _result(inlet_flow * main_pump_energy / 24.0, "kW"),
    })
    return outputs
