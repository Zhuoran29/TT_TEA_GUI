"""OpenEI utility-rate lookup helpers for map extensions."""

import json
import os
import urllib.parse
import urllib.request
from functools import lru_cache


DEFAULT_OPENEI_KEY = "NrYesSRYplmSurhuPtNPqbqC0CwAKtifeBQ7dXX0"
OPENEI_UTILITY_RATES_URL = "https://api.openei.org/utility_rates?"


def _first_tier_energy_price(period):
    if not period:
        return None
    tier = period[0]
    try:
        return float(tier.get("rate", 0.0) or 0.0) + float(tier.get("adj", 0.0) or 0.0)
    except (TypeError, ValueError):
        return None


def _schedule_period_counts(rate):
    counts = {}
    for schedule_name in ("energyweekdayschedule", "energyweekendschedule"):
        schedule = rate.get(schedule_name) or []
        for month in schedule:
            for period_index in month:
                counts[period_index] = counts.get(period_index, 0) + 1
    return counts


def estimate_energy_price(rate):
    """Estimate a representative energy charge in $/kWh from one OpenEI rate."""
    structure = rate.get("energyratestructure") or []
    if not structure:
        return None

    period_prices = {
        index: price
        for index, period in enumerate(structure)
        if (price := _first_tier_energy_price(period)) is not None
    }
    if not period_prices:
        return None

    counts = _schedule_period_counts(rate)
    weighted_total = 0.0
    total_count = 0
    for period_index, price in period_prices.items():
        count = counts.get(period_index, 0)
        weighted_total += price * count
        total_count += count

    if total_count > 0:
        return weighted_total / total_count
    return sum(period_prices.values()) / len(period_prices)


def energy_price_range(rate):
    """Return min and max first-tier energy charges across OpenEI periods."""
    structure = rate.get("energyratestructure") or []
    prices = [
        price
        for period in structure
        if (price := _first_tier_energy_price(period)) is not None
    ]
    if not prices:
        return None, None
    return min(prices), max(prices)


@lru_cache(maxsize=256)
def lookup_local_electricity_price(lat, lon, sector="Industrial", radius=None, limit=1):
    """Return a representative OpenEI electricity price and metadata for a location."""
    api_key = os.environ.get("OPENEI_API_KEY", DEFAULT_OPENEI_KEY)
    params = {
        "api_key": api_key,
        "version": "8",
        "lat": round(float(lat), 5),
        "lon": round(float(lon), 5),
        "format": "json",
        "is_default": "false",
        "sector": sector,
        "limit": limit,
        "detail": "full",
    }
    if radius is not None:
        params["radius"] = radius

    url = OPENEI_UTILITY_RATES_URL + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=20) as response:
        payload = json.load(response)

    items = payload.get("items") or []
    if not items:
        return {
            "price": None,
            "sector": sector,
            "utility": "",
            "rate_name": "",
            "uri": "",
            "status": "No OpenEI rate records returned.",
        }

    rate = items[0]
    price = estimate_energy_price(rate)
    if price is None:
        return {
            "price": None,
            "sector": rate.get("sector") or sector,
            "utility": rate.get("utility", ""),
            "rate_name": rate.get("name", ""),
            "uri": rate.get("uri", ""),
            "status": "Rate found, but no usable energy rate structure.",
        }
    min_price, max_price = energy_price_range(rate)

    return {
        "price": price,
        "min_price": min_price,
        "max_price": max_price,
        "sector": rate.get("sector") or sector,
        "utility": rate.get("utility", ""),
        "rate_name": rate.get("name", ""),
        "uri": rate.get("uri", ""),
        "status": "OK",
    }


def lookup_best_local_electricity_price(lat, lon):
    """Try industrial first, then commercial, matching the old DOE helper behavior."""
    last_result = None
    for sector in ("Industrial", "Commercial"):
        try:
            result = lookup_local_electricity_price(lat, lon, sector=sector)
        except Exception as error:
            result = {
                "price": None,
                "sector": sector,
                "utility": "",
                "rate_name": "",
                "uri": "",
                "status": f"OpenEI request failed: {error}",
            }
        last_result = result
        if result and result.get("price") is not None:
            return result
    return last_result


def lookup_best_local_electricity_price_or_none(lat, lon):
    result = lookup_best_local_electricity_price(lat, lon)
    if result and result.get("price") is not None:
        return result
    return None
