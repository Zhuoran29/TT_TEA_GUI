"""One-way sensitivity analysis for completed TEA cases."""

from copy import deepcopy

from tea_models.analyses.scenario_comparison import (
    BBL_PER_M3,
    feed_lcow_per_bbl,
    product_lcow_per_bbl,
    product_flow_m3_day,
)
from tea_models.tea_engine import (
    calculate_crf,
    calculate_lcow,
    input_records_to_tables,
    ordered_units_from_train,
)


SYSTEM_PARAMETERS = {
    "feed_flow": {"label": "Feed flow", "context_key": "feed_flow_m3_day", "unit": "m3/day"},
    "electricity_price": {"label": "Electricity price", "context_key": "electricity_price", "unit": "$/kWh"},
    "thermal_energy_price": {"label": "Thermal energy price", "context_key": "thermal_energy_price", "unit": "$/kWh"},
    "discount_rate": {"label": "Discount rate", "context_key": "discount_rate_percent", "unit": "%"},
    "project_life": {"label": "Project life", "context_key": "project_life_years", "unit": "year"},
    "operating_time": {"label": "Operating time", "context_key": "operation_time_percent", "unit": "%"},
    "investment_factor": {"label": "Investment factor", "context_key": "investment_factor", "unit": "factor"},
}

OUTPUT_METRICS = {
    "feed_lcow": {"label": "Feed LCOW", "unit": "$/bbl feed"},
    "product_lcow": {"label": "Product LCOW", "unit": "$/bbl product"},
    "capex": {"label": "Total CAPEX", "unit": "USD"},
    "opex": {"label": "Annual OPEX", "unit": "USD/year"},
    "product_flow": {"label": "Product flow", "unit": "m3/day"},
    "electricity_intensity": {"label": "Electricity intensity", "unit": "kWh/bbl feed"},
    "thermal_intensity": {"label": "Thermal intensity", "unit": "kWh/bbl feed"},
}


def parameter_base_value(parameter_key, context):
    definition = SYSTEM_PARAMETERS[parameter_key]
    return float(context.get(definition["context_key"], 0.0) or 0.0)


def apply_system_parameter(context, feedwater_quality, parameter_key, value):
    """Apply one varied value to copied inputs and maintain dependent fields."""
    varied_context = deepcopy(context)
    varied_quality = deepcopy(feedwater_quality)
    value = max(float(value), 0.0)

    if parameter_key == "feed_flow":
        varied_context["feed_flow_m3_day"] = value
        varied_context["feed_flow_bbl_day"] = value * BBL_PER_M3
        display_unit = varied_context.get("feed_flow_display_unit", "m3/day")
        varied_context["feed_flow_display_value"] = (
            value * BBL_PER_M3 if display_unit == "bbl/day" else value
        )
        varied_quality["flow"] = {"value": value * BBL_PER_M3, "unit": "bbl/day"}
    else:
        varied_context[SYSTEM_PARAMETERS[parameter_key]["context_key"]] = value

    if parameter_key in {"discount_rate", "project_life"}:
        varied_context["capital_recovery_factor"] = calculate_crf(
            varied_context.get("discount_rate_percent", 0.0),
            varied_context.get("project_life_years", 1.0),
        )
    if parameter_key == "operating_time":
        varied_context["operating_days_per_year"] = 365.0 * value / 100.0
    return varied_context, varied_quality


def result_metric(metric_key, results, context):
    """Read one normalized target metric from a calculation result."""
    snapshot = {"results": results, "context": context}
    if metric_key == "feed_lcow":
        return feed_lcow_per_bbl(snapshot)
    if metric_key == "product_lcow":
        return product_lcow_per_bbl(snapshot)
    if metric_key == "capex":
        return float(results.get("total_capital_cost", 0.0) or 0.0)
    if metric_key == "opex":
        return float(results.get("total_annual_operating_cost", 0.0) or 0.0)
    if metric_key == "product_flow":
        return product_flow_m3_day(snapshot)
    if metric_key == "electricity_intensity":
        return float(results.get("electricity_intensity_kwh_per_bbl_feed", 0.0) or 0.0)
    if metric_key == "thermal_intensity":
        return float(results.get("thermal_energy_intensity_kwh_per_bbl_feed", 0.0) or 0.0)
    raise KeyError(f"Unknown sensitivity output: {metric_key}")


def run_one_way_sensitivity(
    treatment_train,
    context,
    feedwater_quality,
    unit_inputs,
    baseline_results,
    parameter_keys,
    metric_key,
    variation_percent,
):
    """Run low/base/high cases independently for each selected parameter."""
    variation_fraction = max(float(variation_percent), 0.0) / 100.0
    technical_tables = input_records_to_tables(unit_inputs.get("technical", {}))
    cost_tables = input_records_to_tables(unit_inputs.get("cost", {}))
    removal_tables = {
        int(sequence): values
        for sequence, values in unit_inputs.get("removal_efficiencies", {}).items()
    }
    ordered_units = ordered_units_from_train(treatment_train)
    baseline_metric = result_metric(metric_key, baseline_results, context)
    rows = []

    for parameter_key in parameter_keys:
        definition = SYSTEM_PARAMETERS[parameter_key]
        base_value = parameter_base_value(parameter_key, context)
        if base_value <= 0.0:
            raise ValueError(f"{definition['label']} must be greater than zero for percent-based sensitivity analysis.")
        case_values = [
            ("Low", base_value * (1.0 - variation_fraction), -float(variation_percent)),
            ("Base", base_value, 0.0),
            ("High", base_value * (1.0 + variation_fraction), float(variation_percent)),
        ]
        for case, input_value, change_percent in case_values:
            if case == "Base":
                metric_value = baseline_metric
            else:
                varied_context, varied_quality = apply_system_parameter(
                    context, feedwater_quality, parameter_key, input_value
                )
                varied_results = calculate_lcow(
                    ordered_units,
                    technical_tables,
                    cost_tables,
                    removal_tables,
                    varied_context,
                    varied_quality,
                )
                metric_value = result_metric(metric_key, varied_results, varied_context)
            impact_percent = (
                (metric_value - baseline_metric) / baseline_metric * 100.0
                if abs(baseline_metric) > 1e-12 else 0.0
            )
            rows.append({
                "Parameter key": parameter_key,
                "Parameter": definition["label"],
                "Case": case,
                "Input value": input_value,
                "Input unit": definition["unit"],
                "Input change (%)": change_percent,
                "Output": OUTPUT_METRICS[metric_key]["label"],
                "Output value": metric_value,
                "Output unit": OUTPUT_METRICS[metric_key]["unit"],
                "Output impact (%)": impact_percent,
            })
    return rows


def tornado_rows(sensitivity_rows):
    """Collapse detailed sensitivity cases into low/high tornado values."""
    grouped = {}
    for row in sensitivity_rows:
        item = grouped.setdefault(row["Parameter"], {"Parameter": row["Parameter"]})
        if row["Case"] == "Low":
            item["Low impact (%)"] = row["Output impact (%)"]
        elif row["Case"] == "High":
            item["High impact (%)"] = row["Output impact (%)"]
    return sorted(
        grouped.values(),
        key=lambda item: max(abs(item.get("Low impact (%)", 0.0)), abs(item.get("High impact (%)", 0.0))),
        reverse=True,
    )
