"""
Astrology MCP Server
====================
Exposes two tools to Claude:
  - get_natal_chart   : Natal chart for any person
  - get_solar_return  : Solar Return (Revolucion Solar) for any year/location
"""

import os
import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route
from mcp.server.fastmcp import FastMCP
from kerykeion import AstrologicalSubject

from .geocode import geocode_city
from .chart import render_natal_chart, render_solar_return
from .solar_return import compute_solar_return

mcp = FastMCP(
    "astro-mcp",
    instructions=(
        "Astrology server providing natal charts and solar returns. "
        "Supports English and Spanish output. "
        "Use get_natal_chart for birth charts and get_solar_return for yearly solar returns."
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
    birth_date   : Date of birth in YYYY-MM-DD format (e.g. 1973-07-25)
    birth_time   : Time of birth in HH:MM format, 24h (e.g. 17:25)
    city         : City of birth (e.g. Buenos Aires, London, Cordoba)
    country_code : ISO 2-letter country code (e.g. AR, ES, MX)
    lat          : Latitude override (decimal degrees)
    lng          : Longitude override (decimal degrees)
    tz_str       : Timezone override (e.g. America/Argentina/Buenos_Aires)
    language     : en for English, es for Spanish (default: en)
    """
    try:
        year, month, day = (int(p) for p in birth_date.split("-"))
        hour, minute = (int(p) for p in birth_time.split(":"))

        if lat is None or lng is None or tz_str is None:
            resolved_lat, resolved_lng, resolved_tz = geocode_city(city, country_code)
            lat    = lat    or resolved_lat
            lng    = lng    or resolved_lng
            tz_str = tz_str or resolved_tz

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
    birth_date         : Date of birth YYYY-MM-DD (e.g. 1973-07-25)
    birth_time         : Time of birth HH:MM 24h (e.g. 17:25)
    birth_city         : City of birth
    return_year        : Year for the Solar Return (e.g. 2025)
    birth_country_code : ISO 2-letter code for birth city
    birth_lat/lng/tz_str : Coordinate overrides for birth city
    return_city        : City where SR is cast (defaults to birth city)
    return_country_code: ISO 2-letter code for return city
    return_lat/lng/tz_str : Coordinate overrides for return city
    language           : en for English, es for Spanish
    """
    try:
        b_year, b_month, b_day = (int(p) for p in birth_date.split("-"))
        b_hour, b_minute = (int(p) for p in birth_time.split(":"))

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

        natal_subject = AstrologicalSubject(
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
            natal_subject=natal_subject,
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

    mcp_app = mcp.streamable_http_app()

    # RFC 9728: Protected Resource Metadata with empty authorization_servers
    # tells Claude.ai that this server requires NO authentication.
    async def protected_resource_meta(request: Request) -> JSONResponse:
        base = str(request.base_url).rstrip("/")
        return JSONResponse({
            "resource": f"{base}/mcp",
            "authorization_servers": [],
            "bearer_methods_supported": [],
            "scopes_supported": [],
        })

    # Fallback OAuth discovery endpoint - returns empty to signal no auth
    async def oauth_server_meta(request: Request) -> JSONResponse:
        return JSONResponse({})

    app = Starlette(
        routes=[
            Route(
                "/.well-known/oauth-protected-resource/mcp",
                protected_resource_meta,
                methods=["GET"],
            ),
            Route(
                "/.well-known/oauth-authorization-server",
                oauth_server_meta,
                methods=["GET"],
            ),
            Mount("/", app=mcp_app),
        ]
    )

    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
