"""
Geocoding utilities: city name -> lat, lng, timezone string.
Uses Nominatim (OpenStreetMap, no API key needed) + timezonefinder.
Falls back gracefully if offline.
"""

from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
from timezonefinder import TimezoneFinder

_geocoder = Nominatim(user_agent="astro-mcp/1.0")
_tf = TimezoneFinder()

# Fallback table for common cities (used when network is unavailable)
KNOWN_CITIES: dict[str, tuple[float, float, str]] = {
    # Argentina
    "buenos aires":      (-34.6037, -58.3816, "America/Argentina/Buenos_Aires"),
    "moron":             (-34.6534, -58.6198, "America/Argentina/Buenos_Aires"),
    "cordoba":           (-31.4201, -64.1888, "America/Argentina/Cordoba"),
    "rosario":           (-32.9442, -60.6505, "America/Argentina/Cordoba"),
    "mendoza":           (-32.8908, -68.8272, "America/Argentina/Mendoza"),
    "tucuman":           (-26.8241, -65.2226, "America/Argentina/Tucuman"),
    "salta":             (-24.7859, -65.4116, "America/Argentina/Salta"),
    "mar del plata":     (-37.9964, -57.5534, "America/Argentina/Buenos_Aires"),
    "la plata":          (-34.9215, -57.9545, "America/Argentina/Buenos_Aires"),
    # Spain
    "madrid":            (40.4168, -3.7038,   "Europe/Madrid"),
    "barcelona":         (41.3851, 2.1734,    "Europe/Madrid"),
    "valencia":          (39.4699, -0.3763,   "Europe/Madrid"),
    "seville":           (37.3891, -5.9845,   "Europe/Madrid"),
    "sevilla":           (37.3891, -5.9845,   "Europe/Madrid"),
    # Mexico
    "mexico city":       (19.4326, -99.1332,  "America/Mexico_City"),
    "ciudad de mexico":  (19.4326, -99.1332,  "America/Mexico_City"),
    "guadalajara":       (20.6597, -103.3496, "America/Mexico_City"),
    "monterrey":         (25.6866, -100.3161, "America/Monterrey"),
    # Colombia
    "bogota":            (4.7110,  -74.0721,  "America/Bogota"),
    "medellin":          (6.2442,  -75.5812,  "America/Bogota"),
    # Chile
    "santiago":          (-33.4489, -70.6693, "America/Santiago"),
    # Peru
    "lima":              (-12.0464, -77.0428, "America/Lima"),
    # Venezuela
    "caracas":           (10.4806, -66.9036,  "America/Caracas"),
    # UK
    "london":            (51.5074, -0.1278,   "Europe/London"),
    # USA
    "new york":          (40.7128, -74.0060,  "America/New_York"),
    "los angeles":       (34.0522, -118.2437, "America/Los_Angeles"),
    "chicago":           (41.8781, -87.6298,  "America/Chicago"),
    "san diego":         (32.7157, -117.1611, "America/Los_Angeles"),
}


def geocode_city(city: str, country_code: str = "") -> tuple[float, float, str]:
    """
    Returns (lat, lng, tz_str) for a given city name.
    Tries Nominatim first, falls back to KNOWN_CITIES table.
    Raises ValueError if city cannot be resolved.
    """
    query = f"{city}, {country_code}" if country_code else city

    # Try Nominatim (live geocoding)
    try:
        location = _geocoder.geocode(query, timeout=5)
        if location:
            lat, lng = location.latitude, location.longitude
            tz_str = _tf.timezone_at(lat=lat, lng=lng)
            if tz_str:
                return lat, lng, tz_str
    except (GeocoderTimedOut, GeocoderUnavailable):
        pass

    # Fall back to known cities table
    key = city.lower().strip()
    if key in KNOWN_CITIES:
        return KNOWN_CITIES[key]

    # Try partial match
    for known_key, coords in KNOWN_CITIES.items():
        if key in known_key or known_key in key:
            return coords

    raise ValueError(
        f"Could not resolve location for '{city}'. "
        "Please provide lat, lng, and tz_str directly."
    )
