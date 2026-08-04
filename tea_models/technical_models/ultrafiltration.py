from tea_models.technical_models.template_units import run_template


DEFAULTS = {
    "unit_kind": "uf",
    "recovery": 0.96,
    "energy_intensity": 0.0,
    "membrane_flux": 45.0,
    "backwash_fraction": 0.04,
    "sodium_bisulfite_dose_mg_l": 5.0,
    "pump_tdh_ft": 50.0,
    "pump_efficiency": 0.75,
    "motor_efficiency": 0.95,
    "vfd_factor": 0.98,
}


GALLON_PER_M3 = 264.172052


def _result(value, unit):
    return {"value": value, "unit": unit}


def _input(values, name, default):
    try:
        return float(values.get(name, default))
    except (TypeError, ValueError):
        return float(default)


def _value(result, name, default=0.0):
    entry = result.get(name, {})
    try:
        return float(entry.get("value", default) if isinstance(entry, dict) else entry)
    except (TypeError, ValueError):
        return float(default)


def _pump_power_kw(flow_m3_day, tdh_ft, pump_efficiency, motor_efficiency, vfd_factor):
    flow_gpm = flow_m3_day * GALLON_PER_M3 / 1440.0
    hydraulic_hp = flow_gpm * max(tdh_ft, 0.0) / 3960.0
    return hydraulic_hp * 0.7457 / max(pump_efficiency * motor_efficiency * vfd_factor, 1e-12)


def run(unit_process, technical_inputs, stream):
    chemical_dose = _input(
        technical_inputs,
        "sodium_bisulfite_dose_mg_l",
        DEFAULTS["sodium_bisulfite_dose_mg_l"],
    ) / 1000.0
    template_inputs = {**technical_inputs, "chemical_dose": chemical_dose}
    outputs = run_template(unit_process, template_inputs, stream, DEFAULTS)

    inlet_flow = _value(outputs, "inlet_flow")
    tdh_ft = _input(technical_inputs, "pump_tdh_ft", DEFAULTS["pump_tdh_ft"])
    pump_eff = _input(technical_inputs, "pump_efficiency", DEFAULTS["pump_efficiency"])
    motor_eff = _input(technical_inputs, "motor_efficiency", DEFAULTS["motor_efficiency"])
    vfd_factor = _input(technical_inputs, "vfd_factor", DEFAULTS["vfd_factor"])
    pump_kw = _pump_power_kw(inlet_flow, tdh_ft, pump_eff, motor_eff, vfd_factor)
    energy_intensity = pump_kw * 24.0 / max(inlet_flow, 1e-12)

    outputs.update({
        "energy_intensity": _result(energy_intensity, "kWh/m3 feed"),
        "uf_pump_power": _result(pump_kw, "kW"),
        "pump_tdh": _result(tdh_ft, "ft"),
        "pump_efficiency": _result(pump_eff, "fraction"),
        "motor_efficiency": _result(motor_eff, "fraction"),
        "vfd_factor": _result(vfd_factor, "factor"),
        "sodium_bisulfite_dose": _result(chemical_dose * 1000.0, "mg/L"),
        "sodium_bisulfite_consumption": _result(chemical_dose * inlet_flow, "kg/day"),
    })
    return outputs
