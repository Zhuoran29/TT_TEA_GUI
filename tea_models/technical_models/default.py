def run(unit_process, technical_inputs, stream):
    """Default technical model for a unit process.

    Unit-specific technical model files can replace this function while keeping
    the same signature.
    """
    inlet_flow = float(stream.get("flow_m3_day", 0.0))
    recovery = float(technical_inputs.get("recovery", 1.0))
    recovery = max(0.0, min(recovery, 1.0))

    outlet_flow = inlet_flow * recovery
    brine_flow = max(inlet_flow - outlet_flow, 0.0)

    return {
        "inlet_flow": {"value": inlet_flow, "unit": "m3/day"},
        "outlet_flow": {"value": outlet_flow, "unit": "m3/day"},
        "brine_flow": {"value": brine_flow, "unit": "m3/day"},
        "water_recovery": {"value": recovery, "unit": "fraction"},
        "energy_intensity": {
            "value": float(technical_inputs.get("energy_intensity", 0.0)),
            "unit": "kWh/m3",
        },
        "constituent_removal_efficiency": {
            "value": float(technical_inputs.get("removal_efficiency", 0.0)),
            "unit": "fraction",
        },
        "chemical_dose": {
            "value": float(technical_inputs.get("chemical_dose", 0.0)),
            "unit": "kg/m3",
        },
    }
