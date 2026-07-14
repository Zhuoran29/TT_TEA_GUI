"""Brackish-water reverse-osmosis design model and TEA adapter.

The design equations are adapted from ``DesalinationModels/BWRO.py`` in the
SEDAT model library.  The SEDAT model sizes from product capacity; this adapter
accepts the TEA framework's feed stream and derives product capacity from the
selected recovery.
"""

from __future__ import annotations

from math import ceil, exp

from tea_models.water_quality import apply_unit_water_quality, get_default_removal_efficiencies


def _result(value, unit):
    return {"value": value, "unit": unit}


def _number(values, name, default):
    try:
        return float(values.get(name, default))
    except (TypeError, ValueError):
        return float(default)


def _tds_g_l(stream, fallback):
    entry = (stream.get("water_quality", {}) or {}).get("TDS", {})
    try:
        value = float(entry.get("value", fallback) or fallback)
    except (TypeError, ValueError):
        return float(fallback)
    unit = str(entry.get("unit", "mg/L") or "mg/L").lower().replace(" ", "")
    if unit in {"mg/l", "ppm"}:
        return value / 1000.0
    if unit in {"kg/m3", "g/l"}:
        return value
    return value / 1000.0


class BWRODesign:
    """Screening single-pass BWRO model with 1--3 concentrate stages."""

    def __init__(
        self,
        feed_tds_g_l,
        temperature_c,
        product_capacity_m3_day,
        recovery,
        array_stages=None,
        elements_per_vessel=6,
        design_flux_lmh=18.0,
        concentration_polarization=1.05,
        fouling_factor=0.85,
        high_pressure_pump_efficiency=0.85,
        feed_pump_efficiency=0.80,
        feed_pump_pressure_bar=1.0,
        piping_loss_bar=0.5,
        has_erd=False,
        erd_efficiency=0.95,
        pretreatment_sec=0.0,
    ):
        self.feed_tds = float(feed_tds_g_l)
        self.temperature_c = float(temperature_c)
        self.product_capacity = float(product_capacity_m3_day)
        self.recovery = float(recovery) / 100.0 if float(recovery) > 1 else float(recovery)
        self.array_stages = None if array_stages in (None, 0, 0.0) else int(array_stages)
        self.elements_per_vessel = int(elements_per_vessel)
        self.design_flux_lmh = float(design_flux_lmh)
        self.cp_factor = float(concentration_polarization)
        self.fouling_factor = float(fouling_factor)
        self.hp_efficiency = float(high_pressure_pump_efficiency)
        self.feed_pump_efficiency = float(feed_pump_efficiency)
        self.feed_pump_pressure = float(feed_pump_pressure_bar)
        self.piping_loss = float(piping_loss_bar)
        self.has_erd = bool(round(float(has_erd)))
        self.erd_efficiency = float(erd_efficiency)
        self.pretreatment_sec = float(pretreatment_sec)

        # FilmTec BW30 PRO-400/34 membrane data used by the source model.
        self.element_test_product_m3_h = 42.0 / 24.0
        self.element_area_m2 = 37.0
        self.test_pressure_bar = 15.5
        self.test_tds_g_l = 2.0
        self.salt_rejection = 0.996
        self.test_recovery = 0.15
        self.max_pressure_bar = 41.0
        self.max_feed_m3_h_element = 17.0
        self.max_dp_bar_element = 1.0
        self.max_dp_bar_vessel = 3.5
        self.min_concentrate_m3_h_vessel = 2.7
        self.max_stage_recovery = 0.75
        self.warnings = []
        self._validate()
        self._derive_permeability()

    @staticmethod
    def _osmotic_pressure(concentration_g_l, temperature_k):
        return 2.0 * 0.0831 * temperature_k * max(concentration_g_l, 0.0) / 58.443

    def _validate(self):
        if not 0 < self.recovery < 1:
            raise ValueError("BWRO recovery must be between 0 and 1.")
        if self.feed_tds <= 0 or self.product_capacity <= 0:
            raise ValueError("BWRO feed TDS and product capacity must be positive.")
        if self.elements_per_vessel < 1 or self.design_flux_lmh <= 0:
            raise ValueError("BWRO vessel size and design flux must be positive.")
        if not 0 < self.hp_efficiency <= 1 or not 0 < self.feed_pump_efficiency <= 1:
            raise ValueError("BWRO pump efficiencies must be in (0, 1].")
        if not 0 < self.fouling_factor <= 1:
            raise ValueError("BWRO fouling factor must be in (0, 1].")
        if self.array_stages not in (None, 1, 2, 3):
            raise ValueError("BWRO array stages must be 0 (automatic), 1, 2, or 3.")
        if not 0 <= self.erd_efficiency <= 1:
            raise ValueError("BWRO ERD efficiency must be in [0, 1].")
        if not 0.5 <= self.feed_tds <= 10.0:
            self.warnings.append(
                "Feed TDS is outside the source model's screening range of 0.5--10 g/L."
            )
        if self.temperature_c > 45:
            self.warnings.append("Feed temperature exceeds the membrane's 45 C limit.")

    def _derive_permeability(self):
        test_temp_k = 298.15
        test_brine = self.test_tds_g_l / (1.0 - self.test_recovery)
        test_membrane_feed = self.cp_factor * (self.test_tds_g_l + test_brine) / 2.0
        test_permeate = (1.0 - self.salt_rejection) * test_membrane_feed
        test_ndp = self.test_pressure_bar - (
            self._osmotic_pressure(test_membrane_feed, test_temp_k)
            - self._osmotic_pressure(test_permeate, test_temp_k)
        )
        if test_ndp <= 0:
            raise ValueError("BWRO membrane test data produce a non-positive NDP.")
        reference = self.element_test_product_m3_h / (self.element_area_m2 * test_ndp)
        temperature_factor = exp(0.024 * (self.temperature_c - 25.0))
        self.effective_permeability = reference * temperature_factor * self.fouling_factor
        self.temperature_k = self.temperature_c + 273.15

    def _stage_count(self):
        if self.array_stages is not None:
            return self.array_stages
        if self.recovery <= 0.75:
            return 1
        if self.recovery <= 0.90:
            return 2
        return 3

    def _allocate_vessels(self, total, stages, final_brine_m3_h):
        if total < stages:
            raise ValueError("Not enough BWRO pressure vessels for the requested stages.")
        weights = [2 ** (stages - index - 1) for index in range(stages)]
        available = total - stages
        raw = [available * weight / float(sum(weights)) for weight in weights]
        extra = [int(value) for value in raw]
        remainder = available - sum(extra)
        order = sorted(range(stages), key=lambda index: raw[index] - extra[index], reverse=True)
        for index in order[:remainder]:
            extra[index] += 1
        vessels = [value + 1 for value in extra]
        if stages > 1 and self.min_concentrate_m3_h_vessel > 0:
            max_final = max(1, int(final_brine_m3_h / self.min_concentrate_m3_h_vessel))
            if vessels[-1] > max_final:
                excess = vessels[-1] - max_final
                vessels[-1] = max_final
                vessels[0] += excess
        return vessels

    def _salt_balance(self, feed_tds, feed_flow, permeate_flow):
        brine_flow = max(feed_flow - permeate_flow, 1e-12)
        brine_tds = feed_tds
        permeate_tds = (1.0 - self.salt_rejection) * feed_tds
        for _ in range(30):
            membrane_feed = self.cp_factor * (feed_tds + brine_tds) / 2.0
            permeate_tds = (1.0 - self.salt_rejection) * membrane_feed
            updated = (feed_tds * feed_flow - permeate_tds * permeate_flow) / brine_flow
            if abs(updated - brine_tds) < 1e-10:
                brine_tds = updated
                break
            brine_tds = 0.5 * (brine_tds + updated)
        return permeate_tds, brine_tds

    def _pressure_drop(self, feed_per_vessel, brine_per_vessel):
        total = 0.0
        for index in range(self.elements_per_vessel):
            fraction = (index + 0.5) / self.elements_per_vessel
            element_flow = feed_per_vessel + fraction * (brine_per_vessel - feed_per_vessel)
            total += self.max_dp_bar_element * (
                element_flow / self.max_feed_m3_h_element
            ) ** 2
        return min(total, self.max_dp_bar_vessel)

    def _solve_stage(self, inlet_pressure, feed_flow, feed_tds, vessels):
        elements = vessels * self.elements_per_vessel
        area = elements * self.element_area_m2

        def evaluate(permeate_flow):
            brine_flow = feed_flow - permeate_flow
            permeate_tds, brine_tds = self._salt_balance(feed_tds, feed_flow, permeate_flow)
            pressure_drop = self._pressure_drop(feed_flow / vessels, brine_flow / vessels)
            membrane_feed = self.cp_factor * (feed_tds + brine_tds) / 2.0
            delta_osmotic = self._osmotic_pressure(
                membrane_feed, self.temperature_k
            ) - self._osmotic_pressure(permeate_tds, self.temperature_k)
            average_pressure = inlet_pressure - pressure_drop / 2.0
            predicted = self.effective_permeability * area * max(
                average_pressure - delta_osmotic, 0.0
            )
            return predicted - permeate_flow, permeate_tds, brine_tds, pressure_drop

        low, high = 0.0, feed_flow * (1.0 - 1e-8)
        for _ in range(80):
            middle = (low + high) / 2.0
            if evaluate(middle)[0] > 0:
                low = middle
            else:
                high = middle
        permeate = (low + high) / 2.0
        _, permeate_tds, brine_tds, pressure_drop = evaluate(permeate)
        return {
            "vessels": vessels,
            "feed_flow": feed_flow,
            "permeate_flow": permeate,
            "brine_flow": feed_flow - permeate,
            "permeate_tds": permeate_tds,
            "brine_tds": brine_tds,
            "recovery": permeate / feed_flow,
            "outlet_pressure": inlet_pressure - pressure_drop,
            "pressure_drop": pressure_drop,
        }

    def _run_array(self, pressure, feed_flow, vessels):
        output = []
        pressure -= self.piping_loss
        tds = self.feed_tds
        for vessel_count in vessels:
            stage = self._solve_stage(pressure, feed_flow, tds, vessel_count)
            output.append(stage)
            pressure = stage["outlet_pressure"]
            feed_flow = stage["brine_flow"]
            tds = stage["brine_tds"]
        return output

    def calculate(self):
        target_product_m3_h = self.product_capacity / 24.0
        feed_m3_h = target_product_m3_h / self.recovery
        required_elements = int(
            ceil(target_product_m3_h / (self.design_flux_lmh / 1000.0 * self.element_area_m2))
        )
        total_vessels = int(ceil(required_elements / float(self.elements_per_vessel)))
        stage_count = self._stage_count()
        vessels = self._allocate_vessels(
            total_vessels, stage_count, feed_m3_h - target_product_m3_h
        )

        low, high = max(self.feed_pump_pressure, 0.01), self.max_pressure_bar
        if sum(stage["permeate_flow"] for stage in self._run_array(high, feed_m3_h, vessels)) < target_product_m3_h:
            raise ValueError("BWRO target recovery cannot be met below the membrane pressure limit.")
        for _ in range(80):
            middle = (low + high) / 2.0
            product = sum(
                stage["permeate_flow"] for stage in self._run_array(middle, feed_m3_h, vessels)
            )
            if product < target_product_m3_h:
                low = middle
            else:
                high = middle
        pressure = (low + high) / 2.0
        stages = self._run_array(pressure, feed_m3_h, vessels)
        product_m3_h = sum(stage["permeate_flow"] for stage in stages)
        brine_m3_h = stages[-1]["brine_flow"]
        product_tds = sum(
            stage["permeate_tds"] * stage["permeate_flow"] for stage in stages
        ) / product_m3_h

        feed_pump_kw = feed_m3_h * self.feed_pump_pressure / (
            36.0 * self.feed_pump_efficiency
        )
        gross_hp_kw = feed_m3_h * max(pressure - self.feed_pump_pressure, 0.0) / (
            36.0 * self.hp_efficiency
        )
        recovered_kw = 0.0
        if self.has_erd:
            recovered_kw = (
                self.erd_efficiency * brine_m3_h * max(stages[-1]["outlet_pressure"], 0.0) / 36.0
            )
        hp_kw = max(gross_hp_kw - recovered_kw, 0.0)
        ro_sec = (feed_pump_kw + hp_kw) / product_m3_h

        for number, stage in enumerate(stages, 1):
            if stage["feed_flow"] / stage["vessels"] > self.max_feed_m3_h_element:
                self.warnings.append(f"Stage {number} feed flow per vessel exceeds 17.0 m3/h.")
            if stage["pressure_drop"] >= self.max_dp_bar_vessel - 1e-9:
                self.warnings.append(f"Stage {number} reaches the vessel pressure-drop limit.")
            if stage["recovery"] > self.max_stage_recovery:
                self.warnings.append(f"Stage {number} recovery exceeds the 75% screening limit.")
        if brine_m3_h / vessels[-1] < self.min_concentrate_m3_h_vessel:
            self.warnings.append("Final-stage concentrate flow per vessel is below 2.7 m3/h.")
        if self.recovery > 0.90:
            self.warnings.append(
                "Overall recovery above 90% needs scaling/fouling analysis and may require recycle or CCRO."
            )

        return {
            "feed_flow_m3_day": feed_m3_h * 24.0,
            "product_flow_m3_day": product_m3_h * 24.0,
            "brine_flow_m3_day": brine_m3_h * 24.0,
            "product_tds_mg_l": product_tds * 1000.0,
            "brine_tds_g_l": stages[-1]["brine_tds"],
            "feed_pressure_bar": pressure,
            "vessels": total_vessels,
            "elements": total_vessels * self.elements_per_vessel,
            "array": ":".join(str(value) for value in vessels),
            "feed_pump_kw": feed_pump_kw,
            "high_pressure_pump_kw": hp_kw,
            "erd_recovered_kw": recovered_kw,
            "ro_sec_kwh_m3_product": ro_sec,
            "total_sec_kwh_m3_product": ro_sec + self.pretreatment_sec,
            "warnings": list(self.warnings),
        }


def run(unit_process, technical_inputs, stream):
    inlet_flow = float(stream.get("flow_m3_day", 0.0) or 0.0)
    recovery = _number(technical_inputs, "recovery", 0.80)
    if inlet_flow <= 0:
        raise ValueError("BWRO inlet flow must be positive.")

    design = BWRODesign(
        feed_tds_g_l=_tds_g_l(stream, _number(technical_inputs, "feed_tds_g_l", 0.8)),
        temperature_c=_number(technical_inputs, "feed_temperature", 25.0),
        product_capacity_m3_day=inlet_flow * recovery,
        recovery=recovery,
        array_stages=_number(technical_inputs, "array_stages", 0),
        elements_per_vessel=_number(technical_inputs, "elements_per_vessel", 6),
        design_flux_lmh=_number(technical_inputs, "design_flux_lmh", 18.0),
        concentration_polarization=_number(technical_inputs, "concentration_polarization", 1.05),
        fouling_factor=_number(technical_inputs, "fouling_factor", 0.85),
        high_pressure_pump_efficiency=_number(
            technical_inputs, "high_pressure_pump_efficiency", 0.85
        ),
        feed_pump_efficiency=_number(technical_inputs, "feed_pump_efficiency", 0.80),
        feed_pump_pressure_bar=_number(technical_inputs, "feed_pump_pressure_bar", 1.0),
        piping_loss_bar=_number(technical_inputs, "piping_loss_bar", 0.5),
        has_erd=_number(technical_inputs, "has_erd", 0),
        erd_efficiency=_number(technical_inputs, "erd_efficiency", 0.95),
        pretreatment_sec=_number(technical_inputs, "pretreatment_energy_intensity", 0.0),
    ).calculate()

    inlet_quality = stream.get("water_quality", {})
    removals = technical_inputs.get("removal_efficiencies")
    if removals is None:
        removals = get_default_removal_efficiencies(unit_process, inlet_quality)
    (
        _,
        outlet_flow,
        brine_flow,
        water_quality_in,
        water_quality_out,
        outlet_stream,
    ) = apply_unit_water_quality(stream, recovery, removals)
    # Use the membrane salt-balance result for TDS instead of a generic removal midpoint.
    if "TDS" in water_quality_out:
        water_quality_out["TDS"] = {
            "value": design["product_tds_mg_l"],
            "unit": "mg/L",
        }
        outlet_stream["water_quality"]["TDS"] = dict(water_quality_out["TDS"])

    return {
        "inlet_flow": _result(inlet_flow, "m3/day"),
        "outlet_flow": _result(outlet_flow, "m3/day"),
        "brine_flow": _result(brine_flow, "m3/day"),
        "water_recovery": _result(recovery, "fraction"),
        "energy_intensity": _result(
            design["total_sec_kwh_m3_product"], "kWh/m3 product"
        ),
        "thermal_energy_intensity": _result(0.0, "kWh/m3 product"),
        "removal_efficiencies": removals,
        "water_quality_in": water_quality_in,
        "water_quality_out": water_quality_out,
        "outlet_stream": outlet_stream,
        "feed_tds": _result(_tds_g_l(stream, 0.8), "g/L"),
        "permeate_tds": _result(design["product_tds_mg_l"], "mg/L"),
        "brine_salinity": _result(design["brine_tds_g_l"], "g/L"),
        "required_feed_pressure": _result(design["feed_pressure_bar"], "bar"),
        "pressure_vessels": _result(design["vessels"], "count"),
        "membrane_elements": _result(design["elements"], "count"),
        "membrane_area": _result(design["elements"] * 37.0, "m2"),
        "concentrate_stage_array": _result(design["array"], ""),
        "feed_pump_power": _result(design["feed_pump_kw"], "kW"),
        "high_pressure_pump_power": _result(design["high_pressure_pump_kw"], "kW"),
        "erd_recovered_power": _result(design["erd_recovered_kw"], "kW"),
        "ro_specific_energy": _result(
            design["ro_sec_kwh_m3_product"], "kWh/m3 product"
        ),
        "design_warnings": _result(design["warnings"], ""),
    }
