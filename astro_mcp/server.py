"""
Astrology MCP Server
====================
Tools: get_natal_chart, get_solar_return
OAuth: fastmcp InMemoryOAuthProvider (permissive, accepts all clients)
"""

import os

from fastmcp import FastMCP
from fastmcp.server.auth.providers.in_memory import InMemoryOAuthProvider
from mcp.server.auth.settings import ClientRegistrationOptions
try:
    from kerykeion import AstrologicalSubject
except ImportError:
    from .kerykeion_mock import AstrologicalSubject

from .geocode import geocode_city
from .chart import render_natal_chart, render_solar_return
from .solar_return import compute_solar_return


BASE_URL = os.environ.get(
    "BASE_URL",
    "https://astro-mcp-187388165727.europe-west1.run.app",
)

auth = InMemoryOAuthProvider(
    base_url=BASE_URL,
    client_registration_options=ClientRegistrationOptions(enabled=True),
)

mcp = FastMCP(
    "astro-mcp",
    auth=auth,
    instructions=(
        "Astrology server providing natal charts and solar returns. "
        "Supports English and Spanish output. "
        "Use get_natal_chart for birth charts, get_solar_return for yearly solar returns."
    ),
)


# ---------------------------------------------------------------------------
# Tool 1: Natal Chart
# ---------------------------------------------------------------------------

@mcp.tool()
def get_natal_chart(
    name: str,
    birth_date: str,
    birth_time: str,
    city: str,
    country_code: str = "",
    lat: float = None,
    lng: float = None,
    tz_str: str = None,
    language: str = "en",
) -> str:
    """
    Generate a full natal (birth) chart.

    Parameters
    ----------
    name         : Person's name
    birth_date   : YYYY-MM-DD  (e.g. 1973-07-25)
    birth_time   : HH:MM 24h   (e.g. 17:25)
    city         : City of birth
    country_code : ISO 2-letter code (e.g. AR, ES, MX, GB)
    lat          : Latitude override
    lng          : Longitude override
    tz_str       : Timezone override (e.g. America/Argentina/Buenos_Aires)
    language     : en or es (default: en)
    """
    try:
        year, month, day = (int(p) for p in birth_date.split("-"))
        hour, minute     = (int(p) for p in birth_time.split(":"))

        if lat is None or lng is None or tz_str is None:
            r_lat, r_lng, r_tz = geocode_city(city, country_code)
            lat    = lat    or r_lat
            lng    = lng    or r_lng
            tz_str = tz_str or r_tz

        subject = AstrologicalSubject(
            name, year, month, day, hour, minute,
            city, country_code or "XX",
            lat=lat, lng=lng, tz_str=tz_str,
            zodiac_type="Tropic", online=False,
        )
        return render_natal_chart(
            subject=subject,
            birth_year=year, birth_month=month, birth_day=day,
            birth_hour=hour, birth_minute=minute,
            city=city, lat=lat, lng=lng,
            lang=language,
        )
    except Exception as e:
        return f"Error generating natal chart: {e}"


# ---------------------------------------------------------------------------
# Tool 2: Solar Return
# ---------------------------------------------------------------------------

@mcp.tool()
def get_solar_return(
    name: str,
    birth_date: str,
    birth_time: str,
    birth_city: str,
    return_year: int,
    birth_country_code: str = "",
    birth_lat: float = None,
    birth_lng: float = None,
    birth_tz_str: str = None,
    return_city: str = None,
    return_country_code: str = "",
    return_lat: float = None,
    return_lng: float = None,
    return_tz_str: str = None,
    language: str = "en",
) -> str:
    """
    Generate a Solar Return (Revolucion Solar) chart for a given year.

    Parameters
    ----------
    name               : Person's name
    birth_date         : YYYY-MM-DD
    birth_time         : HH:MM 24h
    birth_city         : City of birth
    return_year        : Year for the Solar Return (e.g. 2026)
    birth_country_code : ISO 2-letter code for birth city
    birth_lat/lng/tz_str : Coordinate overrides for birth city
    return_city        : City where SR is cast (defaults to birth city)
    return_country_code: ISO 2-letter code for return city
    return_lat/lng/tz_str : Coordinate overrides for return city
    language           : en or es
    """
    try:
        b_year, b_month, b_day = (int(p) for p in birth_date.split("-"))
        b_hour, b_minute       = (int(p) for p in birth_time.split(":"))

        if birth_lat is None or birth_lng is None or birth_tz_str is None:
            r_lat, r_lng, r_tz = geocode_city(birth_city, birth_country_code)
            birth_lat    = birth_lat    or r_lat
            birth_lng    = birth_lng    or r_lng
            birth_tz_str = birth_tz_str or r_tz

        if return_city is None:
            return_city   = birth_city
            return_lat    = return_lat    or birth_lat
            return_lng    = return_lng    or birth_lng
            return_tz_str = return_tz_str or birth_tz_str
        else:
            if return_lat is None or return_lng is None or return_tz_str is None:
                rr_lat, rr_lng, rr_tz = geocode_city(return_city, return_country_code)
                return_lat    = return_lat    or rr_lat
                return_lng    = return_lng    or rr_lng
                return_tz_str = return_tz_str or rr_tz

        natal = AstrologicalSubject(
            name, b_year, b_month, b_day, b_hour, b_minute,
            birth_city, birth_country_code or "XX",
            lat=birth_lat, lng=birth_lng, tz_str=birth_tz_str,
            zodiac_type="Tropic", online=False,
        )
        sr_subject, sr_utc = compute_solar_return(
            name=name,
            birth_year=b_year, birth_month=b_month, birth_day=b_day,
            birth_hour=b_hour, birth_minute=b_minute,
            birth_lat=birth_lat, birth_lng=birth_lng, birth_tz=birth_tz_str,
            return_year=return_year,
            return_lat=return_lat, return_lng=return_lng, return_tz=return_tz_str,
        )
        return render_solar_return(
            sr_subject=sr_subject,
            natal_subject=natal,
            sr_utc_datetime=sr_utc,
            return_year=return_year,
            return_city=return_city,
            return_lat=return_lat,
            return_lng=return_lng,
            name=name,
            lang=language,
        )
    except Exception as e:
        return f"Error generating Solar Return: {e}"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    port = int(os.environ.get("PORT", 8080))
    mcp.run(transport="streamable-http", host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
