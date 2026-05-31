"""
Solar Return calculator using pyswisseph.
Finds the exact Julian Day when the Sun returns to its natal longitude
in the given year, then builds a kerykeion chart for that moment.
"""

from datetime import datetime, timezone, timedelta

try:
    import swisseph as swe
    from kerykeion import AstrologicalSubject
    MOCK_MODE = False
except ImportError:
    from .kerykeion_mock import AstrologicalSubject
    MOCK_MODE = True


def _jd_from_datetime(dt: datetime) -> float:
    """Convert a UTC datetime to Julian Day Number."""
    return swe.julday(
        dt.year, dt.month, dt.day,
        dt.hour + dt.minute / 60.0 + dt.second / 3600.0
    )


def _sun_longitude(jd: float) -> float:
    """Return the Sun's ecliptic longitude for a given Julian Day."""
    result = swe.calc_ut(jd, swe.SUN)
    return result[0][0]


def _find_solar_return_jd(natal_sun_lon: float, year: int,
                           birth_month: int, birth_day: int) -> float:
    """
    Binary-search for the exact JD when Sun longitude = natal_sun_lon
    in the given year. Searches a 40-day window centred around the
    birthday in that year (handles leap year edge cases).
    """
    # Start 20 days before the estimated birthday
    try:
        approx_date = datetime(year, birth_month, birth_day, tzinfo=timezone.utc)
    except ValueError:
        # Feb 29 in non-leap year
        approx_date = datetime(year, birth_month, 28, tzinfo=timezone.utc)

    start = approx_date - timedelta(days=20)
    jd_start = _jd_from_datetime(start)

    target = natal_sun_lon
    step = 0.05  # days (~1.2 hours)
    max_steps = int(40 / step)

    prev_lon = _sun_longitude(jd_start)
    crossing_jd = None

    for i in range(1, max_steps + 1):
        jd_curr = jd_start + i * step
        curr_lon = _sun_longitude(jd_curr)

        diff_prev = (target - prev_lon + 360) % 360
        diff_curr = (target - curr_lon + 360) % 360

        # Crossing detected: prev was approaching from below, curr passed it
        if diff_prev < 1.0 and diff_curr > 359.0:
            # We just crossed; bracket is [jd_curr - step, jd_curr]
            crossing_jd = jd_curr - step
            break
        if diff_prev > 359.0 and diff_curr < 1.0:
            crossing_jd = jd_curr - step
            break
        # Normal crossing
        if diff_prev <= 180 and diff_curr > 180:
            crossing_jd = jd_curr - step
            break

        prev_lon = curr_lon

    if crossing_jd is None:
        raise ValueError(
            f"Solar Return for {year} not found. "
            f"Natal Sun at {natal_sun_lon:.4f}°. Check inputs."
        )

    # Refine with bisection to sub-minute accuracy
    lo = crossing_jd
    hi = crossing_jd + step

    for _ in range(60):
        mid = (lo + hi) / 2.0
        mid_lon = _sun_longitude(mid)
        diff_mid = (target - mid_lon + 360) % 360
        if diff_mid <= 180:
            hi = mid
        else:
            lo = mid

    return (lo + hi) / 2.0


def _jd_to_datetime_utc(jd: float) -> datetime:
    """Convert a Julian Day to a UTC datetime."""
    result = swe.jdut1_to_utc(jd, 1)  # 1 = Gregorian
    year, month, day, hour_frac = result[0], result[1], result[2], result[3]
    hour = int(hour_frac)
    minute_frac = (hour_frac - hour) * 60
    minute = int(minute_frac)
    second = int((minute_frac - minute) * 60)
    return datetime(year, month, day, hour, minute, second, tzinfo=timezone.utc)


def compute_solar_return(
    name: str,
    birth_year: int,
    birth_month: int,
    birth_day: int,
    birth_hour: int,
    birth_minute: int,
    birth_lat: float,
    birth_lng: float,
    birth_tz: str,
    return_year: int,
    return_lat: float,
    return_lng: float,
    return_tz: str,
) -> tuple[AstrologicalSubject, datetime]:
    """
    Compute the Solar Return chart for the given year.

    Returns:
        (AstrologicalSubject for the SR chart, UTC datetime of exact SR)
    """
    if MOCK_MODE:
        sr_utc = datetime(return_year, birth_month, birth_day, birth_hour, birth_minute, tzinfo=timezone.utc) - timedelta(hours=6)
        sr_subject = AstrologicalSubject(
            f"{name} SR {return_year}",
            sr_utc.year, sr_utc.month, sr_utc.day,
            sr_utc.hour, sr_utc.minute,
            "sr_city",
            "XX",
            lat=return_lat,
            lng=return_lng,
            tz_str="UTC",
            zodiac_type="Tropic",
            online=False,
        )
        return sr_subject, sr_utc

    # Step 1: get natal Sun longitude
    natal_subject = AstrologicalSubject(
        name,
        birth_year, birth_month, birth_day,
        birth_hour, birth_minute,
        "birth_city",
        "XX",
        lat=birth_lat,
        lng=birth_lng,
        tz_str=birth_tz,
        zodiac_type="Tropic",
        online=False,
    )
    natal_sun_lon = natal_subject.sun.abs_pos

    # Step 2: find the exact JD of the SR
    sr_jd = _find_solar_return_jd(natal_sun_lon, return_year, birth_month, birth_day)

    # Step 3: convert JD to local time components
    sr_utc = _jd_to_datetime_utc(sr_jd)

    # Step 4: build the SR chart at the return location
    sr_subject = AstrologicalSubject(
        f"{name} SR {return_year}",
        sr_utc.year, sr_utc.month, sr_utc.day,
        sr_utc.hour, sr_utc.minute,
        "sr_city",
        "XX",
        lat=return_lat,
        lng=return_lng,
        tz_str="UTC",  # we pass UTC time directly
        zodiac_type="Tropic",
        online=False,
    )

    return sr_subject, sr_utc
