"""
Astrology MCP Server
====================
Tools: get_natal_chart, get_solar_return
OAuth: custom minimal implementation, accepts all clients
"""

import os
import secrets
import time
import uvicorn

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse
from starlette.routing import Mount, Route
from starlette.middleware.cors import CORSMiddleware
from urllib.parse import urlencode

from mcp.server.fastmcp import FastMCP
from kerykeion import AstrologicalSubject

from .geocode import geocode_city
from .chart import render_natal_chart, render_solar_return
from .solar_return import compute_solar_return


# ---------------------------------------------------------------------------
# MCP server (no auth - our custom OAuth layer handles that separately)
# ---------------------------------------------------------------------------

mcp = FastMCP(
    "astro-mcp",
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
# Custom minimal OAuth 2.0 layer
# Accepts all clients, issues tokens freely. No real authentication needed.
# ---------------------------------------------------------------------------

_clients: dict = {}
_codes:   dict = {}
_tokens:  dict = {}


async def oauth_discovery(request: Request) -> JSONResponse:
    base = str(request.base_url).rstrip("/")
    return JSONResponse({
        "issuer":                                base,
        "authorization_endpoint":                f"{base}/authorize",
        "token_endpoint":                        f"{base}/token",
        "registration_endpoint":                 f"{base}/register",
        "response_types_supported":              ["code"],
        "grant_types_supported":                 ["authorization_code", "refresh_token"],
        "token_endpoint_auth_methods_supported": ["none", "client_secret_post", "client_secret_basic"],
        "code_challenge_methods_supported":      ["S256"],
    })


async def register(request: Request) -> JSONResponse:
    """Accept any client registration without validation."""
    try:
        body = await request.json()
    except Exception:
        body = {}
    client_id     = secrets.token_urlsafe(16)
    client_secret = secrets.token_urlsafe(32)
    _clients[client_id] = {**body, "client_id": client_id}
    return JSONResponse({
        "client_id":                  client_id,
        "client_secret":              client_secret,
        "client_id_issued_at":        int(time.time()),
        "grant_types":                body.get("grant_types", ["authorization_code"]),
        "response_types":             body.get("response_types", ["code"]),
        "redirect_uris":              body.get("redirect_uris", []),
        "token_endpoint_auth_method": body.get("token_endpoint_auth_method", "none"),
    }, status_code=201)


async def authorize(request: Request) -> RedirectResponse:
    """Immediately issue an auth code and redirect back. No login page needed."""
    params      = dict(request.query_params)
    code        = secrets.token_urlsafe(32)
    redirect_uri = params.get("redirect_uri", "/")
    _codes[code] = {
        "client_id":    params.get("client_id"),
        "redirect_uri": redirect_uri,
        "expires_at":   time.time() + 300,
    }
    sep = "&" if "?" in redirect_uri else "?"
    qp  = {"code": code}
    if "state" in params:
        qp["state"] = params["state"]
    return RedirectResponse(redirect_uri + sep + urlencode(qp), status_code=302)


async def token_endpoint(request: Request) -> JSONResponse:
    """Issue an access token for any valid-looking request."""
    try:
        form = dict(await request.form())
    except Exception:
        form = {}
    access_token  = secrets.token_urlsafe(32)
    refresh_token = secrets.token_urlsafe(32)
    _tokens[access_token] = {"expires_at": time.time() + 3600}
    return JSONResponse({
        "access_token":  access_token,
        "token_type":    "bearer",
        "expires_in":    3600,
        "refresh_token": refresh_token,
    })


# ---------------------------------------------------------------------------
# Entry point: assemble the full app
# ---------------------------------------------------------------------------

def main():
    port    = int(os.environ.get("PORT", 8080))
    mcp_app = mcp.streamable_http_app()

    app = Starlette(routes=[
        Route("/.well-known/oauth-authorization-server", oauth_discovery, methods=["GET", "OPTIONS"]),
        Route("/register",  register,        methods=["POST", "OPTIONS"]),
        Route("/authorize", authorize,        methods=["GET",  "OPTIONS"]),
        Route("/token",     token_endpoint,   methods=["POST", "OPTIONS"]),
        Mount("/", app=mcp_app),
    ])

    # Wide-open CORS so Claude.ai (browser-based) can reach all endpoints
    app = CORSMiddleware(
        app,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
