from tea_models.water_quality import (
    apply_unit_water_quality,
    get_default_removal_efficiencies,
)


def run(unit_process, technical_inputs, stream):
    """Default technical model for a unit process.

    Unit-specific technical model files can replace this function while keeping
    the same signature.
    """
    recovery = float(technical_inputs.get("recovery", 1.0))
    recovery = max(0.0, min(recovery, 1.0))
    inlet_quality = stream.get("water_quality", {})
    removal_efficiencies = technical_inputs.get("removal_efficiencies")
    if removal_efficiencies is None:
        removal_efficiencies = get_default_removal_efficiencies(unit_process, inlet_quality)
    target_values = technical_inputs.get("target_values", {})
    if "target_pH" in technical_inputs:
        target_values = {**target_values, "pH": technical_inputs["target_pH"]}
    if "target_ph" in technical_inputs:
        target_values = {**target_values, "pH": technical_inputs["target_ph"]}

    (
        inlet_flow,
        outlet_flow,
        brine_flow,
        water_quality_in,
        water_quality_out,
        outlet_stream,
    ) = apply_unit_water_quality(stream, recovery, removal_efficiencies, target_values)

    return {
        "inlet_flow": {"value": inlet_flow, "unit": "m3/day"},
        "outlet_flow": {"value": outlet_flow, "unit": "m3/day"},
        "brine_flow": {"value": brine_flow, "unit": "m3/day"},
        "water_recovery": {"value": recovery, "unit": "fraction"},
        "energy_intensity": {
            "value": float(technical_inputs.get("energy_intensity", 0.0)),
            "unit": "kWh/m3",
        },
        "thermal_energy_intensity": {
            "value": float(technical_inputs.get("thermal_energy_intensity", 0.0)),
            "unit": "kWh/m3",
        },
        "constituent_removal_efficiency": {
            "value": float(technical_inputs.get("removal_efficiency", 0.0)),
            "unit": "fraction",
        },
        "removal_efficiencies": removal_efficiencies,
        "water_quality_in": water_quality_in,
        "water_quality_out": water_quality_out,
        "outlet_stream": outlet_stream,
        "chemical_dose": {
            "value": float(technical_inputs.get("chemical_dose", 0.0)),
            "unit": "kg/m3",
        },
    }
