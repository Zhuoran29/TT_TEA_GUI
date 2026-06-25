AF_PER_BBL = 42.0 / 325851.0
BBL_PER_M3 = 6.28981077


COUNTY_BASELINES = {
    "Lea": {
        "population": 71070,
        "employment": 42931,
        "households": 24870,
        "output": 11371733109.45,
        "value_added": 5988885717.74,
        "employee_compensation": 2522451767.30,
        "proprietor_income": 363961674.85,
        "taxes": 654596489.61,
    },
    "Eddy": {
        "population": 58460,
        "employment": 42370,
        "households": 22274,
        "output": 13255494023.61,
        "value_added": 7593747168.19,
        "employee_compensation": 2825860351.46,
        "proprietor_income": 184401716.23,
        "taxes": 730703635.93,
    },
}


SECTOR_OUTPUTS = {
    "Lea": {
        "Grain farming": 1636121.49,
        "All other crop farming": 17109017.29,
        "Tree nut farming": 4483700.68,
        "Beef cattle ranching": 64361679.78,
        "Petroleum refineries": 1701018709.52,
        "Potash, soda, and borate mining": 42604703.40,
        "Data centers / manufacturing": 27956647.13,
    },
    "Eddy": {
        "Grain farming": 1739330.43,
        "All other crop farming": 19538386.93,
        "Tree nut farming": 20131466.78,
        "Beef cattle ranching": 26361063.63,
        "Petroleum refineries": 2031646600.35,
        "Potash, soda, and borate mining": 186723308.31,
        "Data centers / manufacturing": 27414251.43,
    },
}


DEFAULT_SECTOR_WATER_USE_AF_YR = {
    "Grain farming": 1800.0,
    "All other crop farming": 2200.0,
    "Tree nut farming": 3200.0,
    "Beef cattle ranching": 900.0,
    "Petroleum refineries": 1400.0,
    "Potash, soda, and borate mining": 1200.0,
    "Data centers / manufacturing": 650.0,
}


def daily_flow_to_af_per_year(value, unit, operating_days=365.0):
    """Convert a daily water flow to acre-ft/year."""
    if unit == "m3/day":
        return float(value) * BBL_PER_M3 * AF_PER_BBL * float(operating_days)
    return float(value) * AF_PER_BBL * float(operating_days)


def present_worth(annual_value, discount_rate_percent, project_life_years):
    """Return present worth of a constant annual value."""
    years = max(int(project_life_years), 1)
    rate = float(discount_rate_percent) / 100.0
    if abs(rate) < 1e-12:
        return float(annual_value) * years
    factor = (1.0 - (1.0 + rate) ** (-years)) / rate
    return float(annual_value) * factor


def run_socioeconomic_model(
    county,
    sector,
    treated_water_af_yr,
    annual_project_cost,
    sector_water_use_af_yr,
    water_to_output_elasticity=1.0,
    output_multiplier=1.6,
    ramp_years=5,
    project_life_years=15,
    discount_rate_percent=5.0,
    unemployment_rate_percent=5.0,
):
    """Screening-level approximation of the PW-ESESim economic logic.

    The report describes the economic core as an IMPLAN input-output database
    linked to PW-ESESim. This approximation keeps the documented relationship:
    a percent change in sector water use is mapped to a percent change in
    sector production, then scaled to county-level economic outputs.
    """
    county_baseline = COUNTY_BASELINES[county]
    sector_output = SECTOR_OUTPUTS[county][sector]
    sector_water_use_af_yr = max(float(sector_water_use_af_yr), 1e-9)
    treated_water_af_yr = max(float(treated_water_af_yr), 0.0)

    water_change_fraction = treated_water_af_yr / sector_water_use_af_yr
    production_change_fraction = water_change_fraction * float(water_to_output_elasticity)
    direct_output_change = sector_output * production_change_fraction
    total_output_change = direct_output_change * float(output_multiplier)

    output_ratio = total_output_change / max(county_baseline["output"], 1e-9)
    value_added_change = county_baseline["value_added"] * output_ratio
    labor_income_change = (
        county_baseline["employee_compensation"] + county_baseline["proprietor_income"]
    ) * output_ratio
    tax_change = county_baseline["taxes"] * output_ratio

    output_per_job = county_baseline["output"] / max(county_baseline["employment"], 1)
    jobs_created = total_output_change / output_per_job
    unemployed_people = county_baseline["employment"] * float(unemployment_rate_percent) / 100.0
    unemployment_reduction_points = (
        jobs_created / max(unemployed_people, 1e-9) * float(unemployment_rate_percent)
    )

    annual_net_benefit = value_added_change - float(annual_project_cost)
    present_worth_benefit = present_worth(
        value_added_change,
        discount_rate_percent,
        project_life_years,
    )
    present_worth_cost = present_worth(
        annual_project_cost,
        discount_rate_percent,
        project_life_years,
    )

    ramp_years = max(int(ramp_years), 1)
    project_life_years = max(int(project_life_years), 1)
    annual_rows = []
    for year in range(1, project_life_years + 1):
        ramp_fraction = min(year / ramp_years, 1.0)
        annual_rows.append({
            "Year": year,
            "Value added": value_added_change * ramp_fraction,
            "Project cost": float(annual_project_cost) * ramp_fraction,
            "Net benefit": annual_net_benefit * ramp_fraction,
            "Jobs": jobs_created * ramp_fraction,
        })

    return {
        "county": county,
        "sector": sector,
        "treated_water_af_yr": treated_water_af_yr,
        "water_change_fraction": water_change_fraction,
        "production_change_fraction": production_change_fraction,
        "direct_output_change": direct_output_change,
        "total_output_change": total_output_change,
        "value_added_change": value_added_change,
        "labor_income_change": labor_income_change,
        "tax_change": tax_change,
        "jobs_created": jobs_created,
        "unemployment_reduction_points": unemployment_reduction_points,
        "annual_project_cost": float(annual_project_cost),
        "annual_net_benefit": annual_net_benefit,
        "present_worth_benefit": present_worth_benefit,
        "present_worth_cost": present_worth_cost,
        "present_worth_net": present_worth_benefit - present_worth_cost,
        "annual_rows": annual_rows,
    }
