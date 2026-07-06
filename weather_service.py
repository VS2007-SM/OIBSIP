"""
weather_service.py
Oasis Infobyte Python Programming Internship - Project 3 (Advanced)

The "brain" of the Weather App. Handles:
  - Geocoding (place name -> latitude/longitude), with "did you mean?"
    suggestions when a place can't be resolved at all
  - Fetching current, hourly, and daily weather data
  - Fetching air quality (AQI) data
  - Local caching to avoid redundant API calls
  - Graceful fallback to cached data when offline
  - Favorite/saved locations (persisted to disk)
  - Simple day-over-day trend comparison

This module has ZERO knowledge of how the data will be displayed.
It could be plugged into a CLI, a Tkinter GUI, or a web app without
any changes here. That separation is intentional -- see README for
the reasoning ("separation of concerns").

Data source: Open-Meteo (https://open-meteo.com) -- chosen because it
requires no API key and is free for non-commercial use, which removes
a whole category of setup friction for a learning project.
"""

import json
import os
import time
import socket
import difflib
from datetime import datetime, timedelta
from urllib.request import urlopen
from urllib.parse import urlencode
from urllib.error import URLError, HTTPError

# Belt-and-suspenders network timeout: some Windows network stacks
# (especially behind antivirus/firewall software) don't fully respect
# urlopen's per-call timeout during DNS resolution, which can otherwise
# cause requests to hang far longer than intended.
socket.setdefaulttimeout(10)

# --- Paths for local persistence ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(BASE_DIR, "cache")
FAVORITES_FILE = os.path.join(BASE_DIR, "favorites.json")

CACHE_TTL_SECONDS = 15 * 60  # cached data is considered "fresh" for 15 minutes

os.makedirs(CACHE_DIR, exist_ok=True)


class WeatherServiceError(Exception):
    """Raised when weather data cannot be obtained, even from cache."""
    pass


class LocationNotFoundError(WeatherServiceError):
    """
    Raised when a place name cannot be resolved to any location at all.

    Carries an optional list of "did you mean?" suggestions (found via
    looser fallback searches) so the caller can offer them to the user
    instead of just saying "not found" and leaving them stuck.
    """

    def __init__(self, query: str, suggestions: list | None = None):
        self.query = query
        self.suggestions = suggestions or []

        if self.suggestions:
            names = "; ".join(
                f"{s['name']}"
                + (f", {s['admin1']}" if s.get("admin1") else "")
                + f", {s['country']}"
                for s in self.suggestions
            )
            message = f"'{query}' doesn't match any known location. Did you mean: {names}?"
        else:
            message = (
                f"'{query}' doesn't match any known location. "
                "Please check the spelling, or try the name of a nearby city or town instead."
            )

        super().__init__(message)


# ---------------------------------------------------------------------
# Low-level HTTP helper
# ---------------------------------------------------------------------

def _fetch_json(url: str, params: dict, timeout: int = 8) -> dict:
    """Fetch a URL with query params and parse the JSON response."""
    full_url = f"{url}?{urlencode(params)}"
    try:
        with urlopen(full_url, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw)
    except (URLError, HTTPError, TimeoutError) as exc:
        raise WeatherServiceError(f"Network error: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise WeatherServiceError(f"Received malformed data: {exc}") from exc


# ---------------------------------------------------------------------
# Geocoding: place name -> coordinates
# ---------------------------------------------------------------------

_LOCATION_STOPWORDS = {"city", "town", "village", "district", "state", "region", "the", "of", "near", "area"}


def _is_close_match(query: str, resolved_name: str, admin1: str, country: str) -> bool:
    """
    Heuristic check: does the geocoded result actually correspond to
    what the user typed, or did the API silently fall back to a
    broader/nearby place?

    This matters because Open-Meteo's geocoding database only knows
    cities, towns, and villages -- it has NO concept of institutions,
    landmarks, or street addresses. Searching "IIT Dharwad" resolves
    to the city "Dharwad" (matching only on the word "Dharwad" and
    dropping "IIT" entirely), not the specific campus. Without a check
    like this, the user would see real data with no indication that a
    substitution happened.

    Requires ALL significant words from the query to appear in the
    resolved name/region/country -- partial overlap (like "Dharwad"
    matching but "IIT" not matching) is deliberately treated as NOT
    an exact match, so the caller can warn the user accordingly.
    """
    raw_words = [w.lower() for w in query.replace(",", " ").split() if len(w) > 2]
    query_words = [w for w in raw_words if w not in _LOCATION_STOPWORDS] or raw_words

    if not query_words:
        return True

    haystack = f"{resolved_name} {admin1} {country}".lower()
    matched_words = sum(1 for w in query_words if w in haystack)
    full_word_coverage = matched_words == len(query_words)

    # Backup signal: overall string similarity (catches near-spellings
    # like "Bhopl" -> "Bhopal" that wouldn't pass a strict word match)
    similarity = difflib.SequenceMatcher(None, query.lower(), resolved_name.lower()).ratio()

    return full_word_coverage or similarity >= 0.85


def suggest_alternative_locations(query: str, max_suggestions: int = 3) -> list:
    """
    When an exact geocoding lookup finds NOTHING at all, try a couple
    of looser fallback strategies to come up with plausible
    "did you mean?" candidates instead of just giving up:

      1. Re-search the same query but ask for more results (count=5
         instead of 1) -- occasionally the top-1 search and a wider
         search return different candidate sets.
      2. Search each individual significant word in the query on its
         own -- helps when the query mixes a real place name with an
         unrecognized word (e.g. "Bhopal Xyzzy" or "IIT Dharwad").

    Every candidate found this way is scored by string similarity to
    the ORIGINAL query, and only returned if reasonably similar --
    this stops truly random/gibberish input from being paired with
    an unrelated "suggestion" that would be more confusing than
    helpful.
    """
    candidates = {}

    def _try_search(term):
        try:
            data = _fetch_json(
                "https://geocoding-api.open-meteo.com/v1/search",
                {"name": term, "count": 5, "language": "en", "format": "json"},
            )
            for result in data.get("results", []):
                key = (result.get("name"), result.get("country"))
                candidates[key] = result
        except WeatherServiceError:
            pass  # ignore network hiccups during best-effort suggestions

    _try_search(query)

    significant_words = [w for w in query.split() if len(w) > 2]
    if len(significant_words) > 1:
        for word in significant_words:
            _try_search(word)

    scored = []
    for (name, _country), result in candidates.items():
        similarity = difflib.SequenceMatcher(None, query.lower(), name.lower()).ratio()
        scored.append((similarity, result))

    scored.sort(key=lambda pair: pair[0], reverse=True)

    suggestions = []
    for similarity, result in scored[:max_suggestions]:
        if similarity >= 0.35:  # filter out wildly unrelated noise
            suggestions.append({
                "name": result.get("name"),
                "admin1": result.get("admin1", ""),
                "country": result.get("country", ""),
                "latitude": result["latitude"],
                "longitude": result["longitude"],
            })
    return suggestions


def geocode_city(city_name: str) -> dict:
    """
    Look up a place name and return its coordinates and resolved name.

    Returns a dict with an extra "is_exact_match" flag:
      - True  -> the resolved place genuinely corresponds to the query
      - False -> the API could only resolve a broader/nearby place
                 (e.g. an institution name resolving to its host city)

    Raises LocationNotFoundError if NO place could be resolved at all.
    That exception carries a "suggestions" list (possibly empty) of
    "did you mean?" candidates found via looser fallback searches.
    """
    data = _fetch_json(
        "https://geocoding-api.open-meteo.com/v1/search",
        {"name": city_name, "count": 1, "language": "en", "format": "json"},
    )
    results = data.get("results")

    if not results:
        suggestions = suggest_alternative_locations(city_name)
        raise LocationNotFoundError(city_name, suggestions)

    top = results[0]
    resolved_name = top.get("name", city_name)
    admin1 = top.get("admin1", "")
    country = top.get("country", "")

    return {
        "name": resolved_name,
        "country": country,
        "admin1": admin1,  # state/region, if available
        "latitude": top["latitude"],
        "longitude": top["longitude"],
        "query": city_name,
        "is_exact_match": _is_close_match(city_name, resolved_name, admin1, country),
    }


# ---------------------------------------------------------------------
# Caching
# ---------------------------------------------------------------------

def _cache_path(cache_key: str) -> str:
    safe_key = cache_key.replace("/", "_").replace(" ", "_").lower()
    return os.path.join(CACHE_DIR, f"{safe_key}.json")


def _read_cache(cache_key: str) -> dict | None:
    """Return cached payload dict {'timestamp':..., 'data':...} or None."""
    path = _cache_path(cache_key)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _write_cache(cache_key: str, data: dict) -> None:
    path = _cache_path(cache_key)
    payload = {"timestamp": time.time(), "data": data}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f)


def _is_fresh(cached_payload: dict) -> bool:
    age = time.time() - cached_payload.get("timestamp", 0)
    return age < CACHE_TTL_SECONDS


# ---------------------------------------------------------------------
# Weather + Air Quality fetching (with caching + graceful fallback)
# ---------------------------------------------------------------------

def get_weather(latitude: float, longitude: float, cache_key: str) -> dict:
    """
    Fetch current + hourly + daily weather, and air quality, for the
    given coordinates. Uses a 15-minute cache. If the network call
    fails, falls back to the most recent cached copy (if any) and
    flags the result as stale so the UI can warn the user.
    """
    cached = _read_cache(cache_key)
    if cached and _is_fresh(cached):
        result = cached["data"]
        result["_stale"] = False
        return result

    try:
        weather = _fetch_json(
            "https://api.open-meteo.com/v1/forecast",
            {
                "latitude": latitude,
                "longitude": longitude,
                "current": ",".join([
                    "temperature_2m", "relative_humidity_2m", "apparent_temperature",
                    "wind_speed_10m", "wind_direction_10m", "precipitation",
                    "weather_code", "is_day",
                ]),
                "hourly": ",".join([
                    "temperature_2m", "precipitation_probability", "uv_index",
                ]),
                "daily": ",".join([
                    "sunrise", "sunset", "temperature_2m_max", "temperature_2m_min",
                    "uv_index_max", "precipitation_probability_max",
                ]),
                "timezone": "auto",
                "past_days": 1,  # needed for day-over-day trend comparison
            },
        )

        air_quality = _fetch_json(
            "https://air-quality-api.open-meteo.com/v1/air-quality",
            {
                "latitude": latitude,
                "longitude": longitude,
                "current": "us_aqi,pm2_5,pm10",
                "timezone": "auto",
            },
        )

        combined = {"weather": weather, "air_quality": air_quality}
        _write_cache(cache_key, combined)
        combined["_stale"] = False
        return combined

    except WeatherServiceError:
        if cached:
            # Offline / API down -- fall back to last known data
            result = cached["data"]
            result["_stale"] = True
            return result
        raise  # no cache to fall back on; nothing we can do


# ---------------------------------------------------------------------
# Interpretation helpers (turn raw numbers into human meaning)
# ---------------------------------------------------------------------

WEATHER_CODE_DESCRIPTIONS = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
    80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
    95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail",
}


def describe_weather_code(code: int) -> str:
    return WEATHER_CODE_DESCRIPTIONS.get(code, "Unknown conditions")


def interpret_aqi(us_aqi: float | None) -> tuple[str, str]:
    """
    Convert a US AQI number into a category and a plain-language
    health recommendation. Scale: 0-500, per US EPA standard.
    """
    if us_aqi is None:
        return "Unknown", "Air quality data unavailable."
    if us_aqi <= 50:
        return "Good", "Air quality is satisfactory. Great day to be outside."
    elif us_aqi <= 100:
        return "Moderate", "Acceptable for most people. Unusually sensitive people should consider limiting prolonged outdoor exertion."
    elif us_aqi <= 150:
        return "Unhealthy for Sensitive Groups", "Sensitive groups (children, elderly, asthma) should limit prolonged outdoor exertion."
    elif us_aqi <= 200:
        return "Unhealthy", "Everyone may begin to experience health effects. Limit prolonged outdoor exertion."
    elif us_aqi <= 300:
        return "Very Unhealthy", "Health alert: everyone may experience more serious health effects. Avoid outdoor exertion."
    else:
        return "Hazardous", "Health warning of emergency conditions. Avoid all outdoor exertion."


def interpret_uv(uv_index: float | None) -> tuple[str, str]:
    """
    Convert a UV index number into a category and exposure guidance.
    Scale per the WHO/EPA UV Index standard.
    """
    if uv_index is None:
        return "Unknown", "UV data unavailable."
    if uv_index < 3:
        return "Low", "No protection needed for most people."
    elif uv_index < 6:
        return "Moderate", "Wear sunglasses; use SPF 30+ sunscreen if outside for extended periods."
    elif uv_index < 8:
        return "High", "Reduce time in the sun 10am-4pm. Sunscreen, hat, and sunglasses recommended."
    elif uv_index < 11:
        return "Very High", "Extra precautions needed. Unprotected skin can burn quickly."
    else:
        return "Extreme", "Avoid sun exposure during midday hours. Skin can burn in minutes."


def feels_like_explanation(actual_temp: float, feels_like_temp: float) -> str:
    """
    Explain WHY the "feels like" temperature differs from the actual
    reading -- this is genuine meteorology, not just a second number.
    """
    diff = feels_like_temp - actual_temp
    if abs(diff) < 1:
        return "Feels about the same as the actual temperature."
    elif diff < 0 and actual_temp < 10:
        return f"Feels {abs(diff):.1f}\u00b0 colder due to wind chill."
    elif diff > 0 and actual_temp > 25:
        return f"Feels {diff:.1f}\u00b0 warmer due to humidity (heat index effect)."
    elif diff < 0:
        return f"Feels {abs(diff):.1f}\u00b0 colder, likely due to wind."
    else:
        return f"Feels {diff:.1f}\u00b0 warmer, likely due to humidity."


def compute_trend(hourly_times: list, hourly_temps: list) -> str | None:
    """
    Compare the current hour's temperature to the same hour yesterday,
    using the past_days=1 data Open-Meteo already gave us for free.
    This is simple arithmetic comparison -- NOT machine learning --
    and is described that way deliberately, to avoid overstating it.
    """
    if not hourly_times or not hourly_temps:
        return None

    now = datetime.now()
    now_hour_str = now.strftime("%Y-%m-%dT%H:00")
    yesterday_hour_str = (now - timedelta(days=1)).strftime("%Y-%m-%dT%H:00")

    try:
        today_idx = hourly_times.index(now_hour_str)
        yesterday_idx = hourly_times.index(yesterday_hour_str)
    except ValueError:
        return None  # exact hour not found in the returned data

    today_temp = hourly_temps[today_idx]
    yesterday_temp = hourly_temps[yesterday_idx]
    diff = today_temp - yesterday_temp

    if abs(diff) < 0.5:
        return "About the same as this time yesterday."
    elif diff > 0:
        return f"{diff:.1f}\u00b0 warmer than this time yesterday."
    else:
        return f"{abs(diff):.1f}\u00b0 cooler than this time yesterday."


# ---------------------------------------------------------------------
# Favorite locations (persisted to disk as JSON)
# ---------------------------------------------------------------------

def load_favorites() -> list:
    if not os.path.exists(FAVORITES_FILE):
        return []
    try:
        with open(FAVORITES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def save_favorite(city_info: dict) -> None:
    favorites = load_favorites()
    # Avoid duplicates (same name + country)
    for fav in favorites:
        if fav["name"] == city_info["name"] and fav["country"] == city_info["country"]:
            return
    favorites.append(city_info)
    with open(FAVORITES_FILE, "w", encoding="utf-8") as f:
        json.dump(favorites, f, indent=2)


def remove_favorite(city_name: str) -> None:
    favorites = load_favorites()
    favorites = [f for f in favorites if f["name"] != city_name]
    with open(FAVORITES_FILE, "w", encoding="utf-8") as f:
        json.dump(favorites, f, indent=2)