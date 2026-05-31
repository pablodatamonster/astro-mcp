"""
Chart rendering: takes kerykeion AstrologicalSubject objects and
formats them as readable text in English or Spanish.
"""

from kerykeion import AstrologicalSubject, NatalAspects
from .i18n import (
    t, sign_name, planet_name, aspect_name, house_label, format_date
)

# Planets to include in output (in display order)
PLANET_KEYS = [
    ("Sun",       "sun"),
    ("Moon",      "moon"),
    ("Mercury",   "mercury"),
    ("Venus",     "venus"),
    ("Mars",      "mars"),
    ("Jupiter",   "jupiter"),
    ("Saturn",    "saturn"),
    ("Uranus",    "uranus"),
    ("Neptune",   "neptune"),
    ("Pluto",     "pluto"),
    ("True Node", "true_north_lunar_node"),
    ("Chiron",    "chiron_model"),   # special: from _model
]

# Aspects to include (filtering noise)
MAJOR_ASPECTS = {
    "conjunction", "opposition", "trine", "square", "sextile", "quincunx"
}


def _get_planets(subject: AstrologicalSubject) -> list[tuple[str, object]]:
    """Extract all planet objects from a subject, including Chiron."""
    result = []
    chiron_data = subject._model.model_dump().get("chiron")
    chiron_obj = type("Point", (), chiron_data)() if chiron_data else None

    for label, attr in PLANET_KEYS:
        if attr == "chiron_model":
            if chiron_obj:
                result.append((label, chiron_obj))
        else:
            obj = getattr(subject, attr, None)
            if obj:
                result.append((label, obj))
    return result


def _divider(char: str = "-", width: int = 60) -> str:
    return char * width


def render_natal_chart(
    subject: AstrologicalSubject,
    birth_year: int,
    birth_month: int,
    birth_day: int,
    birth_hour: int,
    birth_minute: int,
    city: str,
    lat: float,
    lng: float,
    lang: str = "en",
) -> str:
    """Render a full natal chart as a formatted string."""
    lines = []
    name = subject.name

    lines.append(_divider("="))
    lines.append(f"  {t('natal_title', lang)}: {name}")
    born_str = format_date(birth_year, birth_month, birth_day, birth_hour, birth_minute, lang)
    lines.append(f"  {t('born', lang)}: {born_str}")
    lines.append(f"  {t('location', lang)}: {city}  ({lat:.4f}, {lng:.4f})")
    lines.append(_divider("="))

    # Planets
    lines.append("")
    lines.append(t("planets", lang))
    lines.append(_divider())
    p_col  = t("planet_col", lang)
    s_col  = t("sign_col",   lang)
    h_col  = t("house_col",  lang)
    d_col  = t("degree_col", lang)
    lines.append(f"{'':1} {p_col:<14} {s_col:<14} {d_col:>9}   {h_col:<10}")
    lines.append(_divider())

    planets = _get_planets(subject)
    for label, planet in planets:
        retro = t("retrograde", lang) if planet.retrograde else " "
        pname = planet_name(label, lang)
        sname = sign_name(getattr(planet, "sign", ""), lang)
        pos   = getattr(planet, "position", 0.0)
        house = house_label(str(getattr(planet, "house", "")), lang)
        lines.append(f"{retro:1} {pname:<14} {sname:<14} {pos:>8.4f}°  {house:<10}")

    # Angles
    lines.append("")
    lines.append(t("angles", lang))
    lines.append(_divider())
    angle_pairs = [
        (t("ascendant",  lang), subject.first_house),
        (t("mc",         lang), subject.tenth_house),
        (t("descendant", lang), subject.seventh_house),
        (t("ic",         lang), subject.fourth_house),
    ]
    for label, angle in angle_pairs:
        sname = sign_name(angle.sign, lang)
        lines.append(f"  {label:<22} {sname:<14} {angle.position:>8.4f}°")

    # House cusps
    lines.append("")
    lines.append(t("houses", lang))
    lines.append(_divider())
    house_objs = [
        subject.first_house,  subject.second_house, subject.third_house,
        subject.fourth_house, subject.fifth_house,  subject.sixth_house,
        subject.seventh_house, subject.eighth_house, subject.ninth_house,
        subject.tenth_house,  subject.eleventh_house, subject.twelfth_house,
    ]
    for i, h in enumerate(house_objs, 1):
        sname = sign_name(h.sign, lang)
        lines.append(f"  {i:>2}: {sname:<14} {h.position:>8.4f}°")

    # Aspects
    lines.append("")
    lines.append(t("aspects", lang))
    lines.append(_divider())
    aspects_calc = NatalAspects(subject)
    filtered = [
        a for a in aspects_calc.all_aspects
        if a["orbit"] <= 8 and a["aspect"] in MAJOR_ASPECTS
    ]
    filtered.sort(key=lambda a: a["orbit"])
    for asp in filtered:
        p1   = asp["p1_name"].replace("_", " ").replace("True North Lunar Node", "True Node")
        p2   = asp["p2_name"].replace("_", " ").replace("True North Lunar Node", "True Node")
        asp_name = aspect_name(asp["aspect"], lang)
        orb_label = t("orb", lang)
        lines.append(
            f"  {p1:<22} {asp_name:<16} {p2:<22}  {orb_label}: {asp['orbit']:.2f}°"
        )

    lines.append(_divider("="))
    return "\n".join(lines)


def render_solar_return(
    sr_subject: AstrologicalSubject,
    natal_subject: AstrologicalSubject,
    sr_utc_datetime,
    return_year: int,
    return_city: str,
    return_lat: float,
    return_lng: float,
    name: str,
    lang: str = "en",
) -> str:
    """Render a Solar Return chart with natal Sun reference."""
    from datetime import timezone as _tz
    lines = []

    lines.append(_divider("="))
    lines.append(f"  {t('sr_title', lang)}: {name} ({return_year})")
    sr_dt = sr_utc_datetime
    sr_date_str = format_date(
        sr_dt.year, sr_dt.month, sr_dt.day,
        sr_dt.hour, sr_dt.minute, lang
    )
    lines.append(f"  {t('sr_date', lang)}: {sr_date_str} UTC")
    lines.append(f"  {t('sr_location', lang)}: {return_city}  ({return_lat:.4f}, {return_lng:.4f})")
    natal_sun = natal_subject.sun
    natal_sun_sign = sign_name(natal_sun.sign, lang)
    lines.append(
        f"  Natal Sun: {natal_sun_sign} {natal_sun.position:.4f}°"
    )
    lines.append(_divider("="))

    # SR Planets
    lines.append("")
    lines.append(t("planets", lang))
    lines.append(_divider())
    p_col = t("planet_col", lang)
    s_col = t("sign_col",   lang)
    h_col = t("house_col",  lang)
    d_col = t("degree_col", lang)
    lines.append(f"{'':1} {p_col:<14} {s_col:<14} {d_col:>9}   {h_col:<10}")
    lines.append(_divider())

    planets = _get_planets(sr_subject)
    for label, planet in planets:
        retro = t("retrograde", lang) if planet.retrograde else " "
        pname = planet_name(label, lang)
        sname = sign_name(getattr(planet, "sign", ""), lang)
        pos   = getattr(planet, "position", 0.0)
        house = house_label(str(getattr(planet, "house", "")), lang)
        lines.append(f"{retro:1} {pname:<14} {sname:<14} {pos:>8.4f}°  {house:<10}")

    # SR Angles
    lines.append("")
    lines.append(t("angles", lang))
    lines.append(_divider())
    angle_pairs = [
        (t("ascendant",  lang), sr_subject.first_house),
        (t("mc",         lang), sr_subject.tenth_house),
        (t("descendant", lang), sr_subject.seventh_house),
        (t("ic",         lang), sr_subject.fourth_house),
    ]
    for label, angle in angle_pairs:
        sname = sign_name(angle.sign, lang)
        lines.append(f"  {label:<22} {sname:<14} {angle.position:>8.4f}°")

    # SR House cusps
    lines.append("")
    lines.append(t("houses", lang))
    lines.append(_divider())
    house_objs = [
        sr_subject.first_house,  sr_subject.second_house, sr_subject.third_house,
        sr_subject.fourth_house, sr_subject.fifth_house,  sr_subject.sixth_house,
        sr_subject.seventh_house, sr_subject.eighth_house, sr_subject.ninth_house,
        sr_subject.tenth_house,  sr_subject.eleventh_house, sr_subject.twelfth_house,
    ]
    for i, h in enumerate(house_objs, 1):
        sname = sign_name(h.sign, lang)
        lines.append(f"  {i:>2}: {sname:<14} {h.position:>8.4f}°")

    # SR Aspects
    lines.append("")
    lines.append(t("aspects", lang))
    lines.append(_divider())
    aspects_calc = NatalAspects(sr_subject)
    filtered = [
        a for a in aspects_calc.all_aspects
        if a["orbit"] <= 8 and a["aspect"] in MAJOR_ASPECTS
    ]
    filtered.sort(key=lambda a: a["orbit"])
    for asp in filtered:
        p1 = asp["p1_name"].replace("_", " ").replace("True North Lunar Node", "True Node")
        p2 = asp["p2_name"].replace("_", " ").replace("True North Lunar Node", "True Node")
        asp_name  = aspect_name(asp["aspect"], lang)
        orb_label = t("orb", lang)
        lines.append(
            f"  {p1:<22} {asp_name:<16} {p2:<22}  {orb_label}: {asp['orbit']:.2f}°"
        )

    lines.append(_divider("="))
    return "\n".join(lines)
