"""Interactive map extension UI."""

import copy
import json
import math
from pathlib import Path

import folium
import pandas as pd
import streamlit as st
from branca.element import MacroElement, Template
from branca.colormap import linear
from streamlit_folium import st_folium

# from pages.extensions.openei_rates import lookup_best_local_electricity_price


APP_ROOT = Path(__file__).resolve().parents[2]
LAYER_DIR = APP_ROOT / "data" / "layers"
COUNTY_BOUNDARY_PATH = LAYER_DIR / "county_boundary.geojson"
STATE_BOUNDARY_PATH = LAYER_DIR / "state_boundary.geojson"
BRACKISH_GROUNDWATER_PATH = LAYER_DIR / "BGW_Tidwell.geojson"
RENEWABLE_LCOE_PATH = LAYER_DIR / "renewable.geojson"
OIL_GAS_PRODUCTION_PATH = LAYER_DIR / "New_Mexico_Oil_and_Gas_Production_Areas.geojson"
PRODUCED_WATER_RESOURCE_PATH = LAYER_DIR / "swd_well.geojson"
ASSET_TYPES = ["Water source", "Treatment plant", "Disposal", "End user"]
ASSET_COLORS = {
    "Water source": "#2563EB",
    "Treatment plant": "#16A34A",
    "Disposal": "#DC2626",
    "End user": "#7C3AED",
}
ASSET_MARKER_LABELS = {
    "Water source": "🔵 Water source",
    "Treatment plant": "🟢 Treatment plant",
    "Disposal": "🔴 Disposal",
    "End user": "🟣 End user",
}
ASSET_SHORT_LABELS = {
    "Water source": "🔵 Source",
    "Treatment plant": "🟢 Plant",
    "Disposal": "🔴 Disposal",
    "End user": "🟣 End user",
}
RENEWABLE_SOURCE_COLORS = {
    "Solar": "#F59E0B",
    "Wind": "#0284C7",
}
RENEWABLE_SOURCE_MARKER_LABELS = {
    "Solar": "🟧 Solar",
    "Wind": "🟦 Wind",
}
ENABLE_OPENEI_LOOKUP = False
BBL_PER_M3 = 6.289810770432
STATE_LABELS = {
    "35": "NM",
    "48": "TX",
}


@st.cache_data(show_spinner=False)
def load_geojson(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


@st.cache_data(show_spinner=False)
def load_county_geojson(path):
    data = load_geojson(path)
    for feature in data.get("features", []):
        properties = feature.setdefault("properties", {})
        state = STATE_LABELS.get(str(properties.get("STATEFP", "")), properties.get("STATEFP", ""))
        properties["tooltip_label"] = f"{properties.get('NAME', 'County')}, {state}"
    return data


@st.cache_data(show_spinner=False)
def load_renewable_geojson(path):
    data = load_geojson(path)
    for feature in data.get("features", []):
        properties = feature.setdefault("properties", {})
        properties["GEOID"] = str(properties.get("GEOID", ""))
        properties["LCOE_renewable_label"] = format_layer_value(
            renewable_lcoe_value(properties),
            "$/kWh",
            precision=3,
        )
        properties["LCOE_solar_label"] = format_layer_value(
            properties.get("LCOE_solar____kWh_"),
            "$/kWh",
            precision=3,
        )
        properties["LCOE_wind_label"] = format_layer_value(
            properties.get("LCOE_wind____kWh_"),
            "$/kWh",
            precision=3,
        )
        properties["Solar_capacity_label"] = format_layer_value(
            properties.get("Solar_capacity__MW_"),
            "MW",
            precision=0,
        )
        properties["Wind_capacity_label"] = format_layer_value(
            properties.get("Wind_capacity__MW_"),
            "MW",
            precision=0,
        )
        properties["Solar_penetration_label"] = format_layer_value(
            renewable_penetration_percent_label(properties, "Solar"),
            "%",
            precision=1,
        )
        properties["Wind_penetration_label"] = format_layer_value(
            renewable_penetration_percent_label(properties, "Wind"),
            "%",
            precision=1,
        )
        properties["Battery_label"] = format_layer_value(
            properties.get("Battery__hr_"),
            "hour",
            precision=1,
        )
    return data


def format_layer_value(value, unit="", precision=2):
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return "N/A"
    if math.isnan(numeric_value):
        return "N/A"
    suffix = f" {unit}" if unit else ""
    return f"{numeric_value:,.{precision}f}{suffix}"


def renewable_lcoe_value(properties):
    try:
        return float(properties.get("LCOE_renewable"))
    except (TypeError, ValueError):
        pass

    solar_lcoe = properties.get("LCOE_solar_adjusted____kWh_", properties.get("LCOE_solar____kWh_"))
    wind_lcoe = properties.get("LCOE_wind_adjusted____kWh_", properties.get("LCOE_wind____kWh_"))
    solar_capacity = properties.get("Solar_capacity__MW_")
    wind_capacity = properties.get("Wind_capacity__MW_")
    try:
        solar_lcoe = float(solar_lcoe)
        wind_lcoe = float(wind_lcoe)
        solar_capacity = float(solar_capacity)
        wind_capacity = float(wind_capacity)
    except (TypeError, ValueError):
        return None

    total_capacity = solar_capacity + wind_capacity
    if total_capacity > 0.0:
        return (solar_lcoe * solar_capacity + wind_lcoe * wind_capacity) / total_capacity
    return (solar_lcoe + wind_lcoe) / 2.0


def renewable_penetration_value(properties, source_type):
    field = "Solar_perc____" if source_type == "Solar" else "Wind_perc____"
    try:
        return float(properties.get(field))
    except (TypeError, ValueError):
        return None


def renewable_penetration_percent_label(properties, source_type):
    value = renewable_penetration_value(properties, source_type)
    return value * 100.0 if value is not None else None


def estimated_penetration_percent(source, total_actual_capacity):
    if total_actual_capacity <= 0.0:
        return None
    try:
        geo_capacity = float(source.get("geo_capacity_mw", 0.0) or 0.0)
        geo_penetration = float(source.get("geo_penetration", 0.0) or 0.0)
        actual_capacity = float(source.get("size_mw", 0.0) or 0.0)
    except (TypeError, ValueError):
        return None
    if geo_capacity <= 0.0 or geo_penetration <= 0.0 or actual_capacity <= 0.0:
        return None
    return (geo_capacity / geo_penetration * 300.0) * actual_capacity / total_actual_capacity


def map_targets_state():
    return st.session_state.setdefault("map_targets", [])


def map_routes_state():
    return st.session_state.setdefault("map_routes", [])


def renewable_sources_state():
    return st.session_state.setdefault("renewable_sources", [])


def ensure_target_ids():
    changed = False
    for index, target in enumerate(map_targets_state(), start=1):
        if not target.get("id"):
            target["id"] = f"target-{index}"
            changed = True
    return changed


def ensure_renewable_source_ids():
    changed = False
    for index, source in enumerate(renewable_sources_state(), start=1):
        if not source.get("id"):
            source["id"] = f"renewable-{index}"
            changed = True
    return changed


def point_in_ring(lon, lat, ring):
    inside = False
    if not ring:
        return False
    j = len(ring) - 1
    for i, point in enumerate(ring):
        xi, yi = point[0], point[1]
        xj, yj = ring[j][0], ring[j][1]
        intersects = ((yi > lat) != (yj > lat)) and (
            lon < (xj - xi) * (lat - yi) / ((yj - yi) or 1e-12) + xi
        )
        if intersects:
            inside = not inside
        j = i
    return inside


def point_in_polygon(lon, lat, polygon):
    if not polygon or not point_in_ring(lon, lat, polygon[0]):
        return False
    return not any(point_in_ring(lon, lat, hole) for hole in polygon[1:])


def point_in_geojson_geometry(lon, lat, geometry):
    if not geometry:
        return False
    coordinates = geometry.get("coordinates", [])
    if geometry.get("type") == "Polygon":
        return point_in_polygon(lon, lat, coordinates)
    if geometry.get("type") == "MultiPolygon":
        return any(point_in_polygon(lon, lat, polygon) for polygon in coordinates)
    return False


def renewable_feature_at(lon, lat):
    if not RENEWABLE_LCOE_PATH.exists():
        return None
    data = load_renewable_geojson(str(RENEWABLE_LCOE_PATH))
    for feature in data.get("features", []):
        if point_in_geojson_geometry(lon, lat, feature.get("geometry")):
            return feature
    return None


def make_renewable_source(source_type, lat, lon):
    feature = renewable_feature_at(lon, lat)
    properties = feature.get("properties", {}) if feature else {}
    lcoe, size = renewable_values_for_type(properties, source_type)
    geo_penetration = renewable_penetration_value(properties, source_type)
    fallback_price = cents_to_dollars_per_kwh(
        st.session_state.get("map_local_electricity_price_cents", 8.0)
    )
    electricity_rate = {}
    # if ENABLE_OPENEI_LOOKUP:
    #     try:
    #         electricity_rate = lookup_best_local_electricity_price(lat, lon) or {}
    #     except Exception:
    #         electricity_rate = {"status": "OpenEI lookup failed."}
    count = sum(1 for source in renewable_sources_state() if source.get("plant_type") == source_type) + 1
    return {
        "id": f"renewable-{len(renewable_sources_state()) + 1}",
        "name": f"{source_type} {count}",
        "plant_type": source_type,
        "size_mw": size,
        "estimated_lcoe": lcoe,
        "geo_capacity_mw": size,
        "geo_penetration": geo_penetration,
        "local_electricity_price": float(electricity_rate.get("price") or fallback_price),
        "electricity_rate_source": electricity_rate,
        "lat": float(lat),
        "lon": float(lon),
    }


def renewable_values_for_type(properties, source_type):
    lcoe_key = "LCOE_solar____kWh_" if source_type == "Solar" else "LCOE_wind____kWh_"
    capacity_key = "Solar_capacity__MW_" if source_type == "Solar" else "Wind_capacity__MW_"
    return (
        float(properties.get(lcoe_key, 0.0) or 0.0),
        float(properties.get(capacity_key, 0.0) or 0.0),
    )


def migrate_transportation_defaults():
    if st.session_state.get("transportation_defaults_version", 1) >= 3:
        return

    for route in map_routes_state():
        method = route.get("transportation method", "Truck")
        if float(route.get("cost", 0.05) or 0.05) == 0.05:
            route["cost"] = 0.008 if method == "Pipeline" else 0.03
        if float(route.get("road factor", 1.3) or 1.3) == 1.3:
            route["road factor"] = 1.1 if method == "Pipeline" else 1.25
    st.session_state.transportation_defaults_version = 3


def map_view_state():
    return st.session_state.setdefault(
        "interactive_map_view",
        {
            "center": {"lat": 33.3, "lng": -101.5},
            "zoom": 6,
        },
    )


def haversine_miles(first, second):
    radius_miles = 3958.7613
    lat1 = math.radians(float(first["lat"]))
    lat2 = math.radians(float(second["lat"]))
    dlat = lat2 - lat1
    dlon = math.radians(float(second["lon"]) - float(first["lon"]))
    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2.0) ** 2
    )
    return 2.0 * radius_miles * math.asin(math.sqrt(a))


def feed_flow_bbl_day():
    context = st.session_state.get("tea_context", {})
    if context.get("feed_flow_bbl_day") is not None:
        return float(context.get("feed_flow_bbl_day") or 0.0)
    return float(st.session_state.get("tea_feed_flow_value", 25000.0) or 0.0)


def product_flow_bbl_day():
    results = st.session_state.get("tea_results", {})
    value = float(results.get("final_product_flow", 0.0) or 0.0)
    unit = results.get("final_product_flow_unit", "m3/day")
    if unit == "m3/day":
        return value * BBL_PER_M3
    return value


def brine_flow_bbl_day():
    results = st.session_state.get("tea_results", {})
    for unit_result in results.get("unit_results", []):
        if unit_result.get("section") == "Desalination":
            brine = unit_result.get("technical_results", {}).get("brine_flow", {})
            if isinstance(brine, dict):
                value = float(brine.get("value", 0.0) or 0.0)
                unit = brine.get("unit", "m3/day")
            else:
                value = float(brine or 0.0)
                unit = "m3/day"
            if unit == "m3/day":
                return value * BBL_PER_M3
            return value
    return 0.0


def annual_feed_volume_bbl():
    return feed_flow_bbl_day() * operating_days_per_year()


def annual_product_volume_bbl():
    return product_flow_bbl_day() * operating_days_per_year()


def annual_brine_volume_bbl():
    return brine_flow_bbl_day() * operating_days_per_year()


def volume_for_route(from_target, to_target):
    from_type = from_target["type"]
    to_type = to_target["type"]
    if from_type == "Water source" and to_type == "Treatment plant":
        source_count = max(
            sum(1 for target in map_targets_state() if target.get("type") == "Water source"),
            1,
        )
        return annual_feed_volume_bbl() / source_count
    if from_type == "Treatment plant" and to_type == "Treatment plant":
        return annual_feed_volume_bbl()
    if from_type == "Treatment plant" and to_type == "Disposal":
        return annual_brine_volume_bbl()
    if from_type == "Treatment plant" and to_type == "End user":
        return annual_product_volume_bbl()
    return 0.0


def make_clicked_point(asset_type, lat, lon):
    short_name = {
        "Water source": "Source",
        "Treatment plant": "Treatment plant",
        "Disposal": "Disposal",
        "End user": "End user",
    }.get(asset_type, asset_type)
    count = sum(1 for target in map_targets_state() if target.get("type") == asset_type) + 1
    return {
        "id": f"target-{len(map_targets_state()) + 1}",
        "name": f"{short_name} {count}",
        "type": asset_type,
        "lat": float(lat),
        "lon": float(lon),
    }


def apply_map_click(map_data):
    if not map_data:
        return False
    clicked = map_data.get("last_clicked")
    if not clicked:
        return False

    lat = clicked.get("lat")
    lon = clicked.get("lng")
    if lat is None or lon is None:
        return False

    click_mode = st.session_state.get("map_click_mode")
    if click_mode == "renewable":
        source_type = st.session_state.get("renewable_click_source_type", "Solar")
        selection_signature = f"renewable|{source_type}|{lat:.6f}|{lon:.6f}"
        if st.session_state.get("last_processed_map_selection") == selection_signature:
            return False
        st.session_state.last_processed_map_selection = selection_signature
        feature = renewable_feature_at(lon, lat)
        if not feature:
            st.session_state.map_click_notice = "No renewable resource data found at the selected point."
            return True
        renewable_sources_state().append(make_renewable_source(source_type, lat, lon))
        return True
    if click_mode != "transportation":
        return False

    target_type = st.session_state.get("map_click_target", "Water source")
    selection_signature = f"transportation|{target_type}|{lat:.6f}|{lon:.6f}"
    if st.session_state.get("last_processed_map_selection") == selection_signature:
        return False
    st.session_state.last_processed_map_selection = selection_signature

    map_targets_state().append(make_clicked_point(target_type, lat, lon))
    return True


def save_map_view(map_data):
    if not map_data:
        return

    view = map_view_state()
    center = map_data.get("center")
    zoom = map_data.get("zoom")
    if isinstance(center, dict) and center.get("lat") is not None and center.get("lng") is not None:
        view["center"] = {
            "lat": float(center["lat"]),
            "lng": float(center["lng"]),
        }
    if zoom is not None:
        view["zoom"] = int(zoom)


def target_by_id(target_id):
    for target in map_targets_state():
        if target.get("id") == target_id:
            return target
    return None


def target_by_name(name):
    for target in map_targets_state():
        if target.get("name") == name:
            return target
    return None


def desired_route_pairs():
    targets = map_targets_state()
    sources = [target for target in targets if target.get("type") == "Water source"]
    plants = [target for target in targets if target.get("type") == "Treatment plant"]
    downstream = [
        target
        for target in targets
        if target.get("type") in {"Disposal", "End user"}
    ]
    if not plants:
        return []

    route_pairs = []
    first_plant = plants[0]
    route_pairs.extend((source, first_plant) for source in sources)
    route_pairs.extend(zip(plants, plants[1:]))
    last_plant = plants[-1]
    route_pairs.extend((last_plant, destination) for destination in downstream)
    return route_pairs


def sync_possible_routes():
    ensure_target_ids()
    existing = {
        (
            route.get("from_id") or route.get("from"),
            route.get("to_id") or route.get("to"),
        ): route
        for route in map_routes_state()
    }

    routes = []
    for from_target, to_target in desired_route_pairs():
        key = (from_target["id"], to_target["id"])
        route = dict(existing.get(key, {}))
        route.update(
            {
                "from": from_target["name"],
                "to": to_target["name"],
                "from_id": from_target["id"],
                "to_id": to_target["id"],
            }
        )
        route["transportation method"] = (
            "Pipeline"
            if route.get("transportation method") in {"Pipeline", "Piping"}
            else "Truck"
        )
        route.setdefault(
            "cost",
            0.008 if route["transportation method"] == "Pipeline" else 0.03,
        )
        route.setdefault(
            "road factor",
            1.1 if route["transportation method"] == "Pipeline" else 1.25,
        )
        route["volume"] = volume_for_route(from_target, to_target)
        routes.append(route)
    st.session_state.map_routes = routes


def route_calculations(routes):
    rows = []
    for route in routes:
        from_target = target_by_id(route.get("from_id")) or target_by_name(route.get("from"))
        to_target = target_by_id(route.get("to_id")) or target_by_name(route.get("to"))
        if not from_target or not to_target:
            continue
        straight_distance = haversine_miles(from_target, to_target)
        method = route.get("transportation method", "Truck")
        if method == "Piping":
            method = "Pipeline"
        road_factor = float(route.get("road factor", 1.0) or 1.0)
        distance = straight_distance * road_factor
        volume = float(route.get("volume", 0.0) or 0.0)
        cost = float(route.get("cost", 0.0) or 0.0)
        annual_cost = distance * volume * cost
        rows.append({
            "from": from_target.get("name", route.get("from")),
            "to": to_target.get("name", route.get("to")),
            "transportation method": method,
            "volume": volume,
            "cost": cost,
            "distance": distance,
            "road factor": road_factor,
            "annual cost": annual_cost,
            "path": [[from_target["lat"], from_target["lon"]], [to_target["lat"], to_target["lon"]]],
        })
    return rows


def operating_days_per_year():
    context = st.session_state.get("tea_context", {})
    if context.get("operating_days_per_year") is not None:
        return float(context["operating_days_per_year"])
    operation_time = float(st.session_state.get("tea_operation_time_percent", 100.0) or 0.0)
    return 365.0 * operation_time / 100.0


def tea_annual_feed_volume():
    context = st.session_state.get("tea_context", {})
    operating_days = float(context.get("operating_days_per_year", operating_days_per_year()))
    display_unit = context.get("feed_flow_display_unit", "bbl/day")
    if display_unit == "bbl/day":
        daily_flow = float(context.get("feed_flow_bbl_day", feed_flow_bbl_day()) or 0.0)
    else:
        daily_flow = float(context.get("feed_flow_m3_day", 0.0) or 0.0)
    return max(daily_flow * operating_days, 1e-9)


def transportation_unit_result(transportation_cost, sequence, annual_feed_volume, lcow_unit):
    annual_cost = float(transportation_cost["annual_transportation_cost"])
    return {
        "sequence": sequence,
        "section": "Extension",
        "unit_process": "Transportation",
        "inlet_flow": 0.0,
        "inlet_flow_unit": "",
        "outlet_flow": 0.0,
        "outlet_flow_unit": "",
        "water_recovery": 0.0,
        "water_recovery_unit": "",
        "energy_intensity": 0.0,
        "energy_intensity_unit": "",
        "installed_capital_cost": 0.0,
        "installed_capital_cost_unit": "USD",
        "annualized_capital_cost": 0.0,
        "annualized_capital_cost_unit": "USD/year",
        "total_annual_operating_cost": annual_cost,
        "total_annual_operating_cost_unit": "USD/year",
        "capital_lcow_contribution": 0.0,
        "capital_lcow_contribution_unit": lcow_unit,
        "opex_lcow_contribution": annual_cost / annual_feed_volume,
        "opex_lcow_contribution_unit": lcow_unit,
        "technical_results": {
            "distance_miles": {
                "value": float(transportation_cost.get("distance_miles", 0.0) or 0.0),
                "unit": "mile",
            },
            "transported_volume": {
                "value": float(transportation_cost.get("annual_transported_volume_bbl", 0.0) or 0.0),
                "unit": "bbl/year",
            },
        },
        "cost_results": {
            "cost_per_bbl_mile": {
                "value": float(transportation_cost.get("cost_per_bbl_mile", 0.0) or 0.0),
                "unit": "$/bbl-mile",
            },
            "total_annual_operating_cost": {
                "value": annual_cost,
                "unit": "USD/year",
            },
        },
    }


def rebuild_results_csv_rows(results):
    rows = []
    for unit_result in results["unit_results"]:
        for model_type in ["technical", "cost"]:
            for result_name, result in unit_result.get(f"{model_type}_results", {}).items():
                if not isinstance(result, dict) or "value" not in result:
                    continue
                rows.append({
                    "sequence": unit_result["sequence"],
                    "section": unit_result["section"],
                    "unit_process": unit_result["unit_process"],
                    "model_type": model_type,
                    "result_name": result_name,
                    "value": result.get("value"),
                    "unit": result.get("unit", ""),
                })

    project_rows = [
        ("total_capital_cost", results["total_capital_cost"], "USD"),
        ("annualized_capital_cost", results["annualized_capital_cost"], "USD/year"),
        ("total_annual_operating_cost", results["total_annual_operating_cost"], "USD/year"),
        ("total_annual_cost", results["total_annual_cost"], "USD/year"),
        ("final_product_flow", results["final_product_flow"], results["final_product_flow_unit"]),
        ("levelized_cost_of_water", results["levelized_cost_of_water"], results["levelized_cost_unit"]),
    ]
    for result_name, value, unit in project_rows:
        rows.append({
            "sequence": "",
            "section": "Project",
            "unit_process": "Overall system",
            "model_type": "project_summary",
            "result_name": result_name,
            "value": value,
            "unit": unit,
        })
    return rows


def result_entry_value(result_dict, name, default=0.0):
    entry = result_dict.get(name, {})
    if isinstance(entry, dict):
        return float(entry.get("value", default) or default)
    return float(entry or default)


def annual_electricity_use_kwh(results, electricity_price):
    if electricity_price <= 0.0:
        return 0.0
    total_energy_cost = 0.0
    for unit_result in results.get("unit_results", []):
        total_energy_cost += result_entry_value(
            unit_result.get("cost_results", {}),
            "energy_operating_cost",
        )
    return total_energy_cost / electricity_price


def dollars_to_cents_per_kwh(value):
    try:
        return float(value) * 100.0
    except (TypeError, ValueError):
        return None


def cents_to_dollars_per_kwh(value):
    try:
        return float(value) / 100.0
    except (TypeError, ValueError):
        return 0.0


def ensure_electricity_rate_sources(sources):
    if not ENABLE_OPENEI_LOOKUP:
        return sources
    updated_any = False
    for source in sources:
        rate_source = source.get("electricity_rate_source") or {}
        if (
            (not rate_source or rate_source.get("price") is None)
            and source.get("lat") is not None
            and source.get("lon") is not None
        ):
            try:
                rate_source = lookup_best_local_electricity_price(source["lat"], source["lon"]) or {}
            except Exception:
                rate_source = {"status": "OpenEI lookup failed."}
            source["electricity_rate_source"] = rate_source
            updated_any = True
            if rate_source.get("price") is not None:
                source["local_electricity_price"] = float(rate_source.get("price", 0.0) or 0.0)
    if updated_any:
        st.session_state.renewable_sources = sources
    return sources


def render_electricity_rate_details(sources):
    if not ENABLE_OPENEI_LOOKUP:
        return
    sources = ensure_electricity_rate_sources(sources)
    detail_rows = []
    for source in sources:
        rate_source = source.get("electricity_rate_source") or {}
        detail_rows.append(
            {
                "Plant": source.get("name", ""),
                "Sector": rate_source.get("sector", "N/A"),
                "Utility": rate_source.get("utility", "N/A"),
                "Rate name": rate_source.get("rate_name", "N/A"),
                "Average (c/kWh)": dollars_to_cents_per_kwh(rate_source.get(
                    "price",
                    source.get("local_electricity_price", 0.0),
                )),
                "Min (c/kWh)": dollars_to_cents_per_kwh(rate_source.get("min_price")),
                "Max (c/kWh)": dollars_to_cents_per_kwh(rate_source.get("max_price")),
                "OpenEI link": rate_source.get("uri", ""),
                "Status": rate_source.get("status", "N/A"),
            }
        )

    with st.expander("OpenEI electricity rate details", expanded=False):
        if not detail_rows:
            st.caption("No OpenEI rate details available.")
            return
        st.dataframe(
            detail_rows,
            hide_index=True,
            width="stretch",
            column_config={
                "Average (c/kWh)": st.column_config.NumberColumn(
                    "Average (c/kWh)",
                    format="%.3f",
                ),
                "Min (c/kWh)": st.column_config.NumberColumn(
                    "Min (c/kWh)",
                    format="%.3f",
                ),
                "Max (c/kWh)": st.column_config.NumberColumn(
                    "Max (c/kWh)",
                    format="%.3f",
                ),
                "OpenEI link": st.column_config.LinkColumn("OpenEI link"),
            },
        )


def renewable_sources_table():
    ensure_renewable_source_ids()
    sources = renewable_sources_state()
    if not sources:
        st.info("Choose Solar or Wind, then click the map to add a renewable source.")
        return []
    # sources = ensure_electricity_rate_sources(sources)
    for source in sources:
        feature = renewable_feature_at(source["lon"], source["lat"])
        if feature:
            properties = feature.get("properties", {})
            _, geo_capacity = renewable_values_for_type(properties, source.get("plant_type", "Solar"))
            source["geo_capacity_mw"] = geo_capacity
            source["geo_penetration"] = renewable_penetration_value(
                properties,
                source.get("plant_type", "Solar"),
            )
    total_actual_capacity = sum(float(source.get("size_mw", 0.0) or 0.0) for source in sources)

    table_rows = [
        {
            "Plant": source["name"],
            "Plant type": source["plant_type"],
            "Size (MW)": source["size_mw"],
            "Estimated LCOE ($/kWh)": source["estimated_lcoe"],
            "Estimated penetration (%)": estimated_penetration_percent(
                source,
                total_actual_capacity,
            ),
            "Local electricity price (c/kWh)": dollars_to_cents_per_kwh(
                source.get(
                    "local_electricity_price",
                    cents_to_dollars_per_kwh(st.session_state.get("map_local_electricity_price_cents", 8.0)),
                )
            ),
        }
        for source in sources
    ]
    edited = st.data_editor(
        table_rows,
        key="renewable_sources_editor_v3",
        hide_index=True,
        num_rows="fixed",
        width="stretch",
        disabled=["Estimated LCOE ($/kWh)", "Estimated penetration (%)"],
        column_config={
            "Plant": st.column_config.TextColumn("Plant"),
            "Plant type": st.column_config.SelectboxColumn(
                "Plant type",
                options=["Solar", "Wind"],
            ),
            "Size (MW)": st.column_config.NumberColumn(
                "Size (MW)",
                min_value=0.0,
                step=1.0,
                format="%.1f",
            ),
            "Estimated LCOE ($/kWh)": st.column_config.NumberColumn(
                "Estimated LCOE ($/kWh)",
                format="%.3f",
            ),
            "Estimated penetration (%)": st.column_config.NumberColumn(
                "Estimated penetration (%)",
                format="%.2f",
            ),
            "Local electricity price (c/kWh)": st.column_config.NumberColumn(
                "Local electricity price (c/kWh)",
                min_value=0.0,
                step=0.5,
                format="%.4f",
            ),
        },
    )

    updated_sources = []
    for source, row in zip(sources, edited):
        updated = dict(source)
        updated["name"] = str(row.get("Plant", source["name"]) or source["name"]).strip()
        plant_type = row.get("Plant type", source["plant_type"])
        updated["plant_type"] = plant_type
        updated["size_mw"] = float(row.get("Size (MW)", source["size_mw"]) or 0.0)
        updated["local_electricity_price"] = cents_to_dollars_per_kwh(
            row.get(
                "Local electricity price (c/kWh)",
                dollars_to_cents_per_kwh(source.get("local_electricity_price", 0.0)) or 0.0,
            )
        )
        feature = renewable_feature_at(updated["lon"], updated["lat"])
        if feature:
            properties = feature.get("properties", {})
            lcoe, geo_capacity = renewable_values_for_type(properties, plant_type)
            updated["estimated_lcoe"] = lcoe
            updated["geo_capacity_mw"] = geo_capacity
            updated["geo_penetration"] = renewable_penetration_value(properties, plant_type)
        updated_sources.append(updated)

    total_updated_capacity = sum(float(source.get("size_mw", 0.0) or 0.0) for source in updated_sources)
    for source in updated_sources:
        source["estimated_penetration_percent"] = estimated_penetration_percent(
            source,
            total_updated_capacity,
        )

    if updated_sources != sources:
        st.session_state.renewable_sources = updated_sources

    # render_electricity_rate_details(updated_sources)
    return updated_sources


def renewable_sources_electricity_price(sources):
    prices = [
        (
            float(source.get("local_electricity_price", 0.0) or 0.0),
            float(source.get("size_mw", 0.0) or 0.0),
        )
        for source in sources
        if float(source.get("local_electricity_price", 0.0) or 0.0) > 0.0
    ]
    if not prices:
        return 0.0
    total_size = sum(size for _, size in prices)
    if total_size > 0.0:
        return sum(price * size for price, size in prices) / total_size
    return sum(price for price, _ in prices) / len(prices)


def apply_electricity_price_to_tea(new_price):
    if "tea_results" not in st.session_state:
        return False

    results = copy.deepcopy(st.session_state.tea_results)
    context = st.session_state.setdefault("tea_context", {})
    old_price = float(context.get("electricity_price", st.session_state.get("tea_electricity_price", 0.08)) or 0.08)
    if old_price <= 0.0:
        return False

    annual_feed_volume = tea_annual_feed_volume()
    total_delta = 0.0
    for unit_result in results.get("unit_results", []):
        cost_results = unit_result.get("cost_results", {})
        if "energy_operating_cost" not in cost_results:
            continue
        old_energy_cost = result_entry_value(cost_results, "energy_operating_cost")
        new_energy_cost = old_energy_cost * float(new_price) / old_price
        delta = new_energy_cost - old_energy_cost
        cost_results["energy_operating_cost"]["value"] = new_energy_cost
        if "total_annual_operating_cost" in cost_results:
            cost_results["total_annual_operating_cost"]["value"] = (
                result_entry_value(cost_results, "total_annual_operating_cost") + delta
            )
        unit_result["total_annual_operating_cost"] = float(unit_result.get("total_annual_operating_cost", 0.0) or 0.0) + delta
        unit_result["opex_lcow_contribution"] = unit_result["total_annual_operating_cost"] / annual_feed_volume
        total_delta += delta

    results["total_annual_operating_cost"] = float(results.get("total_annual_operating_cost", 0.0) or 0.0) + total_delta
    results["total_annual_cost"] = float(results.get("annualized_capital_cost", 0.0) or 0.0) + results["total_annual_operating_cost"]
    results["levelized_cost_of_water"] = results["total_annual_cost"] / annual_feed_volume
    results["electricity_price"] = float(new_price)
    results["results_csv_rows"] = rebuild_results_csv_rows(results)

    context["electricity_price"] = float(new_price)
    st.session_state.tea_electricity_price = float(new_price)
    st.session_state.tea_results = results
    st.session_state.tea_results_csv = pd.DataFrame(results["results_csv_rows"]).to_csv(
        index=False
    ).encode("utf-8")
    return True


def apply_transportation_cost_to_tea(transportation_cost):
    if "tea_results" not in st.session_state:
        return False

    results = copy.deepcopy(st.session_state.tea_results)
    existing_transportation = [
        unit
        for unit in results.get("unit_results", [])
        if unit.get("section") == "Extension"
        and unit.get("unit_process") == "Transportation"
    ]
    previous_cost = sum(
        float(unit.get("total_annual_operating_cost", 0.0) or 0.0)
        for unit in existing_transportation
    )
    unit_results = [
        unit
        for unit in results.get("unit_results", [])
        if not (
            unit.get("section") == "Extension"
            and unit.get("unit_process") == "Transportation"
        )
    ]

    annual_cost = float(transportation_cost["annual_transportation_cost"])
    annual_feed_volume = tea_annual_feed_volume()
    lcow_unit = results.get("levelized_cost_unit", "$/bbl feed")
    sequence = max((int(unit.get("sequence", 0) or 0) for unit in unit_results), default=0) + 1
    if annual_cost > 0.0:
        unit_results.append(
            transportation_unit_result(
                transportation_cost,
                sequence,
                annual_feed_volume,
                lcow_unit,
            )
        )

    base_opex = float(results.get("total_annual_operating_cost", 0.0) or 0.0) - previous_cost
    results["unit_results"] = unit_results
    results["total_annual_operating_cost"] = base_opex + annual_cost
    results["total_annual_cost"] = (
        float(results.get("annualized_capital_cost", 0.0) or 0.0)
        + results["total_annual_operating_cost"]
    )
    results["levelized_cost_of_water"] = results["total_annual_cost"] / annual_feed_volume
    results["transportation_cost"] = transportation_cost
    results["results_csv_rows"] = rebuild_results_csv_rows(results)

    st.session_state.transportation_cost = transportation_cost
    st.session_state.tea_results = results
    st.session_state.tea_results_csv = pd.DataFrame(results["results_csv_rows"]).to_csv(
        index=False
    ).encode("utf-8")
    st.session_state.setdefault("tea_context", {})["transportation_cost"] = transportation_cost
    return True


def render_local_electricity_card():
    with st.expander("Electricity", expanded=False):
        st.markdown(
            '<span class="map-tool-panel-marker"></span>',
            unsafe_allow_html=True,
        )
        context = st.session_state.get("tea_context", {})

        st.session_state.setdefault("renewable_click_source_type", "Solar")
        is_renewable_mode = st.session_state.get("map_click_mode") == "renewable"
        action_cols = st.columns([0.38, 0.28, 1.34], gap="small")
        with action_cols[0]:
            if st.button(
                "Click to add renewable source",
                key="activate_renewable_source_click",
                type="primary" if is_renewable_mode else "secondary",
            ):
                st.session_state.map_click_mode = "renewable"
                st.session_state.map_click_notice = (
                    f"Click the map to add a {st.session_state.renewable_click_source_type} source."
                )
                st.rerun()
            st.markdown('<span class="map-mode-button-marker"></span>', unsafe_allow_html=True)
        with action_cols[1]:
            if st.button(
                "Clear selection",
                key="clear_renewable_selection",
                type="tertiary",
                disabled=not renewable_sources_state(),
            ):
                st.session_state.renewable_sources = []
                st.rerun()

        source_cols = st.columns([2, 1])
        with source_cols[0]:
            st.radio(
                "Renewable source type",
                ["Solar", "Wind"],
                key="renewable_click_source_type",
                horizontal=True,
                format_func=lambda source_type: RENEWABLE_SOURCE_MARKER_LABELS.get(source_type, source_type),
            )

        renewable_sources = renewable_sources_table()
        applied_price = renewable_sources_electricity_price(renewable_sources)
        if renewable_sources and applied_price > 0.0:
            st.markdown(
                f"""
                <div class="compact-route-cost">
                    <span>Selected electricity price</span>
                    <strong>{dollars_to_cents_per_kwh(applied_price):,.3f} c/kWh</strong>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("Apply electricity price to TEA", type="primary"):
                if apply_electricity_price_to_tea(applied_price):
                    st.success("Electricity price applied directly to the current TEA results.")
                else:
                    st.warning("Run the TEA model once before applying electricity price.")


def render_water_market_card():
    with st.expander("Water Market", expanded=False):
        st.markdown(
            '<span class="map-tool-panel-marker"></span>',
            unsafe_allow_html=True,
        )
        st.caption("Use this for local water price, avoided purchase cost, or potential product-water revenue screening.")
        water_price = st.number_input(
            "Local water price ($/bbl)",
            min_value=0.0,
            value=float(st.session_state.get("local_water_price", 1.0) or 1.0),
            step=0.1,
            format="%.2f",
            help="Placeholder until a local water price layer is connected.",
        )
        allocation = st.slider("Product water valued", min_value=0, max_value=100, value=100, step=5)
        annual_value = annual_product_volume_bbl() * (allocation / 100.0) * water_price
        metric_cols = st.columns(2)
        metric_cols[0].metric("Product water volume", f"{annual_product_volume_bbl():,.0f} bbl/yr")
        metric_cols[1].metric("Annual water value", f"${annual_value:,.0f}/yr")
        if st.button("Save water market assumption"):
            st.session_state.local_water_price = water_price
            st.session_state.water_market = {
                "local_water_price": water_price,
                "product_water_allocation_percent": allocation,
                "annual_water_value": annual_value,
            }
            st.success("Water market assumption saved.")


def render_map_extension_cards():
    render_local_electricity_card()
    render_water_market_card()


def render_route_setup():
    st.markdown("**Route setup**")
    migrate_transportation_defaults()
    sync_possible_routes()
    targets = map_targets_state()
    if len(targets) < 2:
        st.info("Add at least two facilities on the map to create routes.")
        return

    calculated_routes = route_calculations(map_routes_state())
    editor_rows = [
        {
            "from": row["from"],
            "to": row["to"],
            "transportation method": row["transportation method"],
            "volume": f"{row['volume']:,.1f}",
            "cost": row["cost"],
            "distance": row["distance"],
            "road factor": row["road factor"],
            "annual cost": f"{row['annual cost']:,.0f}",
        }
        for row in calculated_routes
    ]
    previous_routes = [dict(route) for route in map_routes_state()]
    edited_routes = st.data_editor(
        editor_rows,
        key="map_routes_editor_v3",
        hide_index=True,
        num_rows="fixed",
        width="stretch",
        disabled=["from", "to", "volume", "distance", "annual cost"],
        column_config={
            "from": st.column_config.TextColumn("From"),
            "to": st.column_config.TextColumn("To"),
            "transportation method": st.column_config.SelectboxColumn(
                "Transportation Method",
                options=["Truck", "Pipeline"],
                required=True,
            ),
            "volume": st.column_config.TextColumn("Volume (bbl/year)"),
            "cost": st.column_config.NumberColumn("Cost ($/bbl-mile)", format="%.3f"),
            "distance": st.column_config.NumberColumn("Distance (mile)", format="%.1f"),
            "road factor": st.column_config.NumberColumn("Road Factor", format="%.2f"),
            "annual cost": st.column_config.TextColumn("Annual Cost ($/year)"),
        },
    )
    if hasattr(edited_routes, "to_dict"):
        updated_routes = edited_routes.to_dict("records")
    else:
        updated_routes = [dict(route) for route in edited_routes]
    previous_by_route = {
        (
            route.get("from_id") or route.get("from"),
            route.get("to_id") or route.get("to"),
        ): route
        for route in previous_routes
    }
    normalized_routes = []
    for index, route in enumerate(updated_routes):
        normalized = {
            key: (
                float(str(value).replace(",", ""))
                if key in {"volume", "annual cost"}
                else value
            )
            for key, value in route.items()
            if key not in {"distance", "annual cost"}
        }
        route_ids = {}
        if index < len(previous_routes):
            route_ids = {
                "from_id": previous_routes[index].get("from_id"),
                "to_id": previous_routes[index].get("to_id"),
            }
            normalized.update({key: value for key, value in route_ids.items() if value})
        previous = previous_by_route.get(
            (
                normalized.get("from_id") or normalized.get("from"),
                normalized.get("to_id") or normalized.get("to"),
            ),
            {},
        )
        if (
            previous
            and previous.get("transportation method")
            != normalized.get("transportation method")
        ):
            normalized["cost"] = (
                0.008
                if normalized.get("transportation method") == "Pipeline"
                else 0.03
            )
            normalized["road factor"] = (
                1.1
                if normalized.get("transportation method") == "Pipeline"
                else 1.25
            )
        normalized_routes.append(normalized)
    updated_routes = normalized_routes
    st.session_state.map_routes = updated_routes

    calculated_routes = route_calculations(st.session_state.map_routes)
    if not calculated_routes:
        st.info("No valid routes are selected.")
        return

    total_annual_cost = sum(row["annual cost"] for row in calculated_routes)
    total_distance = sum(row["distance"] for row in calculated_routes)
    total_volume = sum(row["volume"] for row in calculated_routes)
    average_cost = (
        sum(row["cost"] * row["volume"] for row in calculated_routes) / total_volume
        if total_volume > 0.0
        else 0.0
    )
    st.markdown(
        f"""
        <div class="compact-route-cost">
            <span>Estimated annual transport cost</span>
            <strong>${total_annual_cost:,.0f}/yr</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Apply transportation cost to TEA", type="primary"):
        transportation_cost = {
            "annual_transportation_cost": total_annual_cost,
            "distance_miles": total_distance,
            "annual_transported_volume_bbl": total_volume,
            "transported_volume_bbl_day": (
                total_volume / operating_days_per_year()
                if operating_days_per_year() > 0.0
                else 0.0
            ),
            "cost_per_bbl_mile": average_cost,
            "route_name": "; ".join(f"{row['from']} -> {row['to']}" for row in calculated_routes),
            "routes": calculated_routes,
            "transportation_methods": sorted({row["transportation method"] for row in calculated_routes}),
        }
        if apply_transportation_cost_to_tea(transportation_cost):
            st.success("Transportation cost applied directly to the current TEA results.")
        else:
            st.warning("Run the TEA model once before applying transportation costs.")


def render_targets_panel():
    is_transportation_mode = st.session_state.get("map_click_mode") == "transportation"
    action_cols = st.columns([0.38, 0.28, 1.34], gap="small")
    with action_cols[0]:
        if st.button(
            "Click to add facility",
            key="activate_transportation_location_click",
            type="primary" if is_transportation_mode else "secondary",
        ):
            st.session_state.map_click_mode = "transportation"
            st.session_state.map_click_notice = (
                f"Click the map to add a {st.session_state.get('map_click_target', 'Water source')} location."
            )
            st.rerun()
        st.markdown('<span class="map-mode-button-marker"></span>', unsafe_allow_html=True)
    with action_cols[1]:
        if st.button(
            "Clear selection",
            key="clear_transportation_selection",
            type="tertiary",
            disabled=not (map_targets_state() or map_routes_state()),
        ):
            st.session_state.map_targets = []
            st.session_state.map_routes = []
            st.rerun()

    st.radio(
        "Click to add facility",
        ASSET_TYPES,
        key="map_click_target",
        horizontal=True,
        label_visibility="collapsed",
        format_func=lambda asset_type: ASSET_MARKER_LABELS.get(asset_type, asset_type),
    )
    ensure_target_ids()
    targets = map_targets_state()
    if not targets:
        st.info("Click the top button, chose a facility type, then click the map to add it.")
        return
    table_col, _ = st.columns([0.45, 0.55])
    with table_col:
        target_rows = [
            {
                "Facility": target["name"],
                "Type": ASSET_SHORT_LABELS.get(target["type"], target["type"]),
            }
            for target in targets
        ]
        edited_targets = st.data_editor(
            target_rows,
            key="map_targets_editor",
            hide_index=True,
            num_rows="fixed",
            width="stretch",
            disabled=["Type"],
            column_config={
                "Facility": st.column_config.TextColumn("Facility"),
                "Type": st.column_config.TextColumn("Type", width="small"),
            },
        )
    updated_targets = []
    for target, row in zip(targets, edited_targets):
        updated = dict(target)
        updated["name"] = str(row.get("Facility", target["name"]) or target["name"]).strip()
        updated_targets.append(updated)
    if updated_targets != targets:
        st.session_state.map_targets = updated_targets
        sync_possible_routes()
        st.rerun()


def renewable_lcoe_range(data):
    values = []
    for feature in data.get("features", []):
        try:
            value = float(renewable_lcoe_value(feature.get("properties", {})))
        except (TypeError, ValueError):
            continue
        if not math.isnan(value):
            values.append(value)
    if not values:
        return 0.0, 1.0
    return min(values), max(values)


class HoverInfoControl(MacroElement):
    """Leaflet-only hover info panel that avoids Streamlit reruns."""

    _template = Template(
        """
        {% macro html(this, kwargs) %}
        <style>
            .map-hover-info-control {
                background: rgba(255, 255, 255, 0.94);
                border: 1px solid rgba(15, 23, 42, 0.16);
                border-radius: 6px;
                box-shadow: 0 8px 24px rgba(15, 23, 42, 0.16);
                color: #0F172A;
                font-family: Arial, sans-serif;
                font-size: 12px;
                line-height: 1.35;
                max-width: 260px;
                min-width: 210px;
                padding: 10px 12px;
            }
            .map-hover-info-title {
                font-size: 13px;
                font-weight: 700;
                margin-bottom: 6px;
            }
            .map-hover-info-row {
                display: grid;
                grid-template-columns: minmax(88px, auto) 1fr;
                gap: 8px;
                margin: 3px 0;
            }
            .map-hover-info-label {
                color: #475569;
                font-weight: 700;
            }
            .map-hover-info-empty {
                color: #64748B;
            }
        </style>
        {% endmacro %}

        {% macro script(this, kwargs) %}
        (function() {
            var map = {{ this._parent.get_name() }};
            var defaultText = '<div class="map-hover-info-title">Info</div>'
                + '<div class="map-hover-info-empty">Hover over a map feature</div>';

            var control = L.control({position: 'topright'});
            control.onAdd = function() {
                var div = L.DomUtil.create('div', 'map-hover-info-control');
                div.innerHTML = defaultText;
                L.DomEvent.disableClickPropagation(div);
                L.DomEvent.disableScrollPropagation(div);
                return div;
            };
            control.addTo(map);

            function escapeHtml(value) {
                if (value === null || value === undefined || value === '') {
                    return 'N/A';
                }
                return String(value)
                    .replace(/&/g, '&amp;')
                    .replace(/</g, '&lt;')
                    .replace(/>/g, '&gt;')
                    .replace(/"/g, '&quot;')
                    .replace(/'/g, '&#039;');
            }

            function formatNumber(value, digits, unit) {
                var numeric = Number(value);
                if (!Number.isFinite(numeric)) {
                    return 'N/A';
                }
                return numeric.toLocaleString(undefined, {
                    minimumFractionDigits: digits,
                    maximumFractionDigits: digits
                }) + (unit ? ' ' + unit : '');
            }

            function row(label, value) {
                return '<div class="map-hover-info-row">'
                    + '<div class="map-hover-info-label">' + escapeHtml(label) + '</div>'
                    + '<div>' + escapeHtml(value) + '</div>'
                    + '</div>';
            }

            function htmlForProperties(props) {
                if (!props) {
                    return defaultText;
                }
                if (props.tooltip_label) {
                    return '<div class="map-hover-info-title">County Boundary</div>'
                        + row('County', props.tooltip_label);
                }
                if (props.LCOE_solar_label || props.LCOE_wind_label) {
                    return '<div class="map-hover-info-title">PV and wind (generated performance)</div>'
                        + row('Renewable LCOE', props.LCOE_renewable_label)
                        + row('Solar LCOE', props.LCOE_solar_label)
                        + row('Wind LCOE', props.LCOE_wind_label)
                        + row('Solar Capacity', props.Solar_capacity_label)
                        + row('Wind Capacity', props.Wind_capacity_label)
                        + row('Solar penetration', props.Solar_penetration_label)
                        + row('Wind penetration', props.Wind_penetration_label)
                        + row('Battery', props.Battery_label);
                }
                if (props.Production || props.Name) {
                    return '<div class="map-hover-info-title">Oil & Gas Production Area</div>'
                        + row('Area', props.Name)
                        + row('Production', props.Production);
                }
                if (props.State_HUC8 || props.Brack_Avai) {
                    return '<div class="map-hover-info-title">Brackish Groundwater</div>'
                        + row('Watershed', props.Name)
                        + row('State', props.State)
                        + row('HUC8', props.State_HUC8)
                        + row('Available', formatNumber(props.Brack_Avai, 0, 'AFY'))
                        + row('Depth', formatNumber(props.Average_Depth_to_Groundwater_Feet, 0, 'ft'));
                }
                if (props.status || props.measured_v || props.true_verti) {
                    return '<div class="map-hover-info-title">Produced Water Resource</div>'
                        + row('Well', props.name)
                        + row('Status', props.status)
                        + row('Measured depth', formatNumber(props.measured_v, 0, 'ft'))
                        + row('True vertical depth', formatNumber(props.true_verti, 0, 'ft'));
                }
                return defaultText;
            }

            function bindLayer(layer) {
                if (layer.feature && layer.feature.properties) {
                    layer.on('mouseover', function() {
                        var panel = document.querySelector('.map-hover-info-control');
                        if (panel) {
                            panel.innerHTML = htmlForProperties(layer.feature.properties);
                        }
                    });
                    layer.on('mouseout', function() {
                        var panel = document.querySelector('.map-hover-info-control');
                        if (panel) {
                            panel.innerHTML = defaultText;
                        }
                    });
                }
                if (layer.eachLayer) {
                    layer.eachLayer(bindLayer);
                }
            }

            setTimeout(function() {
                map.eachLayer(bindLayer);
            }, 0);
        })();
        {% endmacro %}
        """
    )


class MapViewPersistenceControl(MacroElement):
    """Persist Leaflet view in the browser without Streamlit reruns."""

    _template = Template(
        """
        {% macro script(this, kwargs) %}
        (function() {
            var map = {{ this._parent.get_name() }};
            var storageKey = 'tt_tea_interactive_map_view';

            try {
                var saved = JSON.parse(window.localStorage.getItem(storageKey) || 'null');
                if (saved && Number.isFinite(saved.lat) && Number.isFinite(saved.lng) && Number.isFinite(saved.zoom)) {
                    map.setView([saved.lat, saved.lng], saved.zoom, {animate: false});
                }
            } catch (error) {
                console.warn('Could not restore map view', error);
            }

            function saveView() {
                var center = map.getCenter();
                var payload = {
                    lat: center.lat,
                    lng: center.lng,
                    zoom: map.getZoom()
                };
                try {
                    window.localStorage.setItem(storageKey, JSON.stringify(payload));
                } catch (error) {
                    console.warn('Could not save map view', error);
                }
            }

            map.on('moveend zoomend', saveView);
            saveView();
        })();
        {% endmacro %}
        """
    )


def add_renewable_lcoe_layer(map_obj):
    if not RENEWABLE_LCOE_PATH.exists():
        return

    data = load_renewable_geojson(str(RENEWABLE_LCOE_PATH))
    min_lcoe, max_lcoe = renewable_lcoe_range(data)
    colormap = linear.Blues_09.scale(min_lcoe, max_lcoe).to_step(9)
    colormap.colors = list(reversed(colormap.colors))
    colormap.caption = "LCOE from renewable energy ($/kWh)"
    colormap.tick_labels = [
        f"{value:.3f}"
        for value in [min_lcoe, min_lcoe + (max_lcoe - min_lcoe) / 2, max_lcoe]
    ]

    def style_function(feature):
        value = renewable_lcoe_value(feature.get("properties", {}))
        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            numeric_value = None
        color = "#D1D5DB" if numeric_value is None or math.isnan(numeric_value) else colormap(numeric_value)
        return {
            "color": "#374151",
            "weight": 0.7,
            "fillColor": color,
            "fillOpacity": 0.72,
        }

    folium.GeoJson(
        data,
        name="PV and wind (generated performance)",
        style_function=style_function,
        tooltip=folium.GeoJsonTooltip(
            fields=[
                "LCOE_renewable_label",
                "LCOE_solar_label",
                "LCOE_wind_label",
                "Solar_capacity_label",
                "Wind_capacity_label",
                "Solar_penetration_label",
                "Wind_penetration_label",
                "Battery_label",
            ],
            aliases=[
                "Renewable LCOE ($/kWh)",
                "Solar LCOE ($/kWh)",
                "Wind LCOE ($/kWh)",
                "Solar Capacity (MW)",
                "Wind Capacity (MW)",
                "Solar penetration (%)",
                "Wind penetration (%)",
                "Battery (hour)",
            ],
            localize=True,
            labels=True,
            sticky=True,
        ),
    ).add_to(map_obj)
    colormap.add_to(map_obj)


def add_produced_water_resource_layer(map_obj):
    if not PRODUCED_WATER_RESOURCE_PATH.exists():
        return

    folium.GeoJson(
        load_geojson(str(PRODUCED_WATER_RESOURCE_PATH)),
        name="Produced water resource",
        marker=folium.CircleMarker(
            radius=3,
            color="#075985",
            weight=0.7,
            fill=True,
            fill_color="#0EA5E9",
            fill_opacity=0.82,
        ),
        tooltip=folium.GeoJsonTooltip(
            fields=["name", "status", "measured_v", "true_verti"],
            aliases=["Well", "Status", "Measured depth", "True vertical depth"],
            localize=True,
            sticky=True,
        ),
    ).add_to(map_obj)


def add_geojson_layers(map_obj, base_map, show_produced_water, show_brackish, show_renewable):
    if base_map == "County boundary" and COUNTY_BOUNDARY_PATH.exists():
        folium.GeoJson(
            load_county_geojson(str(COUNTY_BOUNDARY_PATH)),
            name="County boundary",
            style_function=lambda _: {
                "color": "#374151",
                "weight": 1,
                "fillColor": "#1F6FEB",
                "fillOpacity": 0.03,
            },
            tooltip=folium.GeoJsonTooltip(
                fields=["tooltip_label"],
                aliases=[""],
                labels=False,
                sticky=True,
            ),
        ).add_to(map_obj)

    if base_map == "Oil & Gas Production Area" and OIL_GAS_PRODUCTION_PATH.exists():
        folium.GeoJson(
            load_geojson(str(OIL_GAS_PRODUCTION_PATH)),
            name="Oil & Gas Production Area",
            style_function=lambda _: {
                "color": "#92400E",
                "weight": 1.2,
                "fillColor": "#92400E",
                "fillOpacity": 0.18,
            },
            tooltip=folium.GeoJsonTooltip(
                fields=["Name", "Production"],
                aliases=["Area", "Production"],
                localize=True,
                sticky=True,
            ),
        ).add_to(map_obj)

    if show_produced_water:
        add_produced_water_resource_layer(map_obj)

    if show_brackish and BRACKISH_GROUNDWATER_PATH.exists():
        folium.GeoJson(
            load_geojson(str(BRACKISH_GROUNDWATER_PATH)),
            name="Brackish groundwater",
            style_function=lambda _: {
                "color": "#0B5F62",
                "weight": 1,
                "fillColor": "#0D9488",
                "fillOpacity": 0.22,
            },
            tooltip=folium.GeoJsonTooltip(
                fields=[
                    "Name",
                    "State",
                    "State_HUC8",
                    "total_available_brackish_water_AFY",
                    "Average_Depth_to_Groundwater_Feet",
                ],
                aliases=[
                    "Watershed",
                    "State",
                    "HUC8",
                    "Available brackish water (AFY)",
                    "Depth to groundwater (ft)",
                ],
                localize=True,
                sticky=True,
            ),
        ).add_to(map_obj)

    if show_renewable:
        add_renewable_lcoe_layer(map_obj)

    if STATE_BOUNDARY_PATH.exists():
        folium.GeoJson(
            load_geojson(str(STATE_BOUNDARY_PATH)),
            name="State boundary",
            style_function=lambda _: {
                "color": "#0F172A",
                "weight": 2,
                "fillOpacity": 0,
            },
        ).add_to(map_obj)


def add_route_markers(map_obj, routes):
    for source in renewable_sources_state():
        plant_type = source.get("plant_type", "Solar")
        folium.RegularPolygonMarker(
            location=[source["lat"], source["lon"]],
            number_of_sides=4,
            radius=7,
            rotation=45,
            color="#FFFFFF",
            weight=1,
            fill=True,
            fill_color=RENEWABLE_SOURCE_COLORS.get(plant_type, "#0284C7"),
            fill_opacity=0.95,
            tooltip=f"{source['name']} ({plant_type})",
        ).add_to(map_obj)

    for point in map_targets_state():
        asset_type = point.get("type")
        folium.CircleMarker(
            location=[point["lat"], point["lon"]],
            radius=5,
            color="#FFFFFF",
            weight=1,
            fill=True,
            fill_color=ASSET_COLORS.get(asset_type, "#4B5563"),
            fill_opacity=0.95,
            tooltip=f"{point['name']} ({asset_type})",
        ).add_to(map_obj)

    for route in routes:
        folium.PolyLine(
            route["path"],
            color="#F59E0B",
            weight=2.5,
            opacity=0.9,
            tooltip=f"{route['from']} -> {route['to']}",
        ).add_to(map_obj)


def render_folium_map(base_map, show_produced_water, show_brackish, show_renewable, routes):
    view = map_view_state()
    center = view["center"]
    map_obj = folium.Map(
        location=[center["lat"], center["lng"]],
        zoom_start=view["zoom"],
        tiles="OpenStreetMap",
        control_scale=True,
    )
    map_obj.add_child(MapViewPersistenceControl())
    map_obj.get_root().html.add_child(
        folium.Element(
            """
            <style>
                .leaflet-tooltip {
                    display: none !important;
                }
                .legend {
                    background: rgba(255, 255, 255, 0.94) !important;
                    border: 1px solid rgba(15, 23, 42, 0.18) !important;
                    border-radius: 6px !important;
                    box-shadow: 0 6px 18px rgba(15, 23, 42, 0.16) !important;
                    color: #0F172A !important;
                    padding: 8px 10px !important;
                }
            </style>
            """
        )
    )
    add_geojson_layers(map_obj, base_map, show_produced_water, show_brackish, show_renewable)
    add_route_markers(map_obj, routes)
    map_obj.add_child(HoverInfoControl())
    return st_folium(
        map_obj,
        key="interactive_route_map",
        height=620,
        use_container_width=True,
        returned_objects=["last_clicked"],
    )


def render_map_workspace():
    control_cols = st.columns(2)
    with control_cols[0]:
        st.markdown("**Base Map**")
        base_map = st.radio(
            "Base Map",
            ["County boundary", "Oil & Gas Production Area"],
            index=1,
            label_visibility="collapsed",
        )
    with control_cols[1]:
        st.markdown("**Layers**")
        show_produced_water = st.checkbox("Produced water resource", value=False)
        show_brackish = st.checkbox("Brackish groundwater", value=False)
        show_renewable = st.checkbox("PV and wind (generated performance)", value=False)
        
    sync_possible_routes()
    calculated_routes = route_calculations(map_routes_state())
    map_data = render_folium_map(base_map, show_produced_water, show_brackish, show_renewable, calculated_routes)
    if apply_map_click(map_data):
        st.rerun()
    st.markdown(
        """
        <style>
            div[data-testid="stExpander"]:has(.map-tool-panel-marker) summary {
                background: #1F6FEB;
                color: #FFFFFF;
                font-weight: 700;
            }
            div[data-testid="stExpander"]:has(.map-tool-panel-marker) summary svg {
                fill: #FFFFFF;
                color: #FFFFFF;
            }
            button[data-testid="stBaseButton-tertiary"] {
                background: transparent;
                border: 1px solid #FCA5A5;
                color: #991B1B;
                font-size: 0.78rem;
                min-height: 2rem;
                padding: 0.18rem 0.45rem;
            }
            button[data-testid="stBaseButton-tertiary"]:hover {
                background: #FECACA;
                border-color: #F87171;
                color: #7F1D1D;
            }
            .compact-route-cost {
                align-items: baseline;
                display: flex;
                gap: 0.75rem;
                margin: 0.6rem 0;
            }
            .compact-route-cost span {
                color: #475569;
                font-size: 0.9rem;
            }
            .compact-route-cost strong {
                color: #0F172A;
                font-size: 1rem;
                font-weight: 700;
            }
            .map-mode-button-marker {
                height: 0;
                overflow: hidden;
                position: absolute;
                width: 0;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
    with st.expander("Transportation", expanded=False):
        st.markdown(
            '<span class="map-tool-panel-marker"></span>',
            unsafe_allow_html=True,
        )
        render_targets_panel()
        render_route_setup()
    render_map_extension_cards()


def render_interactive_map():
    st.subheader("Interactive map")

    with st.container(border=True):
        render_map_workspace()
