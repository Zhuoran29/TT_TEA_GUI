from tea_models.water_quality import (
    apply_unit_water_quality,
    get_default_removal_efficiencies,
)


def _input(values, name, default):
    try:
        return float(values.get(name, default))
    except (TypeError, ValueError):
        return float(default)


def _result(value, unit):
    return {"value": value, "unit": unit}


def _oil_removed_kg_day(water_quality_in, water_quality_out, inlet_flow):
    inlet_oil = water_quality_in.get("Oil", {}).get("value")
    outlet_oil = water_quality_out.get("Oil", {}).get("value")
    if inlet_oil is None or outlet_oil is None:
        return 0.0
    return max(float(inlet_oil) - float(outlet_oil), 0.0) * inlet_flow / 1000.0


def _solids_removed_kg_day(water_quality_in, water_quality_out, inlet_flow):
    inlet_tss = water_quality_in.get("TSS", {}).get("value")
    outlet_tss = water_quality_out.get("TSS", {}).get("value")
    if inlet_tss is None or outlet_tss is None:
        return 0.0
    return max(float(inlet_tss) - float(outlet_tss), 0.0) * inlet_flow / 1000.0


def run_template(unit_process, technical_inputs, stream, defaults):
    recovery = _input(technical_inputs, "recovery", defaults.get("recovery", 1.0))
    energy_intensity = _input(
        technical_inputs,
        "energy_intensity",
        defaults.get("energy_intensity", 0.0),
    )
    chemical_dose = _input(
        technical_inputs,
        "chemical_dose",
        defaults.get("chemical_dose", 0.0),
    )
    removal_efficiencies = technical_inputs.get("removal_efficiencies")
    if removal_efficiencies is None:
        removal_efficiencies = get_default_removal_efficiencies(
            unit_process,
            stream.get("water_quality", {}),
        )

    (
        inlet_flow,
        outlet_flow,
        brine_flow,
        water_quality_in,
        water_quality_out,
        outlet_stream,
    ) = apply_unit_water_quality(stream, recovery, removal_efficiencies)

    outputs = {
        "inlet_flow": _result(inlet_flow, "m3/day"),
        "outlet_flow": _result(outlet_flow, "m3/day"),
        "brine_flow": _result(brine_flow, "m3/day"),
        "water_recovery": _result(recovery, "fraction"),
        "energy_intensity": _result(energy_intensity, "kWh/m3"),
        "chemical_dose": _result(chemical_dose, "kg/m3"),
        "chemical_consumption": _result(chemical_dose * inlet_flow, "kg/day"),
        "oil_removed": _result(
            _oil_removed_kg_day(water_quality_in, water_quality_out, inlet_flow),
            "kg/day",
        ),
        "solids_removed": _result(
            _solids_removed_kg_day(water_quality_in, water_quality_out, inlet_flow),
            "kg/day",
        ),
        "removal_efficiencies": removal_efficiencies,
        "water_quality_in": water_quality_in,
        "water_quality_out": water_quality_out,
        "outlet_stream": outlet_stream,
    }

    unit_kind = defaults.get("unit_kind")
    if unit_kind == "separator":
        hrt = _input(technical_inputs, "hydraulic_retention_time", 30.0)
        design_factor = _input(technical_inputs, "design_factor", 1.2)
        outputs.update({
            "hydraulic_retention_time": _result(hrt, "min"),
            "separator_volume": _result(inlet_flow * hrt / 1440.0 * design_factor, "m3"),
            "design_factor": _result(design_factor, "fraction"),
        })
    elif unit_kind == "daf":
        loading = _input(technical_inputs, "surface_loading_rate", 8.0)
        recycle = _input(technical_inputs, "recycle_ratio", 0.15)
        outputs.update({
            "surface_loading_rate": _result(loading, "m/h"),
            "daf_surface_area": _result(inlet_flow / max(loading * 24.0, 1e-9), "m2"),
            "recycle_flow": _result(inlet_flow * recycle, "m3/day"),
            "recycle_ratio": _result(recycle, "fraction"),
        })
    elif unit_kind == "uf":
        flux = _input(technical_inputs, "membrane_flux", 45.0)
        backwash = _input(technical_inputs, "backwash_fraction", max(1.0 - recovery, 0.0))
        outputs.update({
            "membrane_flux": _result(flux, "L/m2-h"),
            "membrane_area": _result(inlet_flow * 1000.0 / max(flux * 24.0, 1e-9), "m2"),
            "backwash_flow": _result(inlet_flow * backwash, "m3/day"),
            "backwash_fraction": _result(backwash, "fraction"),
        })
    elif unit_kind in {"gac", "zeolite"}:
        ebct = _input(technical_inputs, "empty_bed_contact_time", defaults.get("empty_bed_contact_time", 10.0))
        density = _input(technical_inputs, "media_bulk_density", defaults.get("media_bulk_density", 500.0))
        bed_volume = inlet_flow / 1440.0 * ebct
        outputs.update({
            "empty_bed_contact_time": _result(ebct, "min"),
            "media_bed_volume": _result(bed_volume, "m3"),
            "media_inventory": _result(bed_volume * density, "kg"),
            "media_bulk_density": _result(density, "kg/m3"),
        })
    elif unit_kind == "pond":
        net_evap = _input(technical_inputs, "net_evaporation_rate", 1.0)
        depth = _input(technical_inputs, "operating_depth", 1.5)
        freeboard = _input(technical_inputs, "freeboard", 0.5)
        pond_area = inlet_flow * 365.0 / max(net_evap, 1e-9)
        outputs.update({
            "net_evaporation_rate": _result(net_evap, "m/year"),
            "pond_area": _result(pond_area, "m2"),
            "pond_area_acres": _result(pond_area / 4046.8564224, "acre"),
            "storage_volume": _result(pond_area * (depth + freeboard), "m3"),
            "operating_depth": _result(depth, "m"),
            "freeboard": _result(freeboard, "m"),
        })

    return outputs
