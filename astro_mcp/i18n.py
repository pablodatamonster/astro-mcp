"""
Bilingual labels and formatters for the Astrology MCP.
Supports English (en) and Spanish (es).
"""

SIGNS = {
    "en": {
        "Ari": "Aries",   "Tau": "Taurus",  "Gem": "Gemini",
        "Can": "Cancer",  "Leo": "Leo",      "Vir": "Virgo",
        "Lib": "Libra",   "Sco": "Scorpio",  "Sag": "Sagittarius",
        "Cap": "Capricorn","Aqu": "Aquarius","Pis": "Pisces",
    },
    "es": {
        "Ari": "Aries",   "Tau": "Tauro",   "Gem": "Géminis",
        "Can": "Cáncer",  "Leo": "Leo",     "Vir": "Virgo",
        "Lib": "Libra",   "Sco": "Escorpio","Sag": "Sagitario",
        "Cap": "Capricornio","Aqu": "Acuario","Pis": "Piscis",
    },
}

PLANETS = {
    "en": {
        "Sun": "Sun", "Moon": "Moon", "Mercury": "Mercury",
        "Venus": "Venus", "Mars": "Mars", "Jupiter": "Jupiter",
        "Saturn": "Saturn", "Uranus": "Uranus", "Neptune": "Neptune",
        "Pluto": "Pluto", "True Node": "True Node", "Chiron": "Chiron",
    },
    "es": {
        "Sun": "Sol", "Moon": "Luna", "Mercury": "Mercurio",
        "Venus": "Venus", "Mars": "Marte", "Jupiter": "Júpiter",
        "Saturn": "Saturno", "Uranus": "Urano", "Neptune": "Neptuno",
        "Pluto": "Plutón", "True Node": "Nodo Norte", "Chiron": "Quirón",
    },
}

ASPECTS = {
    "en": {
        "conjunction": "conjunction", "opposition": "opposition",
        "trine": "trine", "square": "square", "sextile": "sextile",
        "quincunx": "quincunx", "semisquare": "semisquare",
        "sesquisquare": "sesquisquare",
    },
    "es": {
        "conjunction": "conjunción", "opposition": "oposición",
        "trine": "trígono", "square": "cuadratura", "sextile": "sextil",
        "quincunx": "quincuncio", "semisquare": "semicuadratura",
        "sesquisquare": "sesquicuadratura",
    },
}

HOUSES = {
    "en": {
        "First_House": "H1", "Second_House": "H2", "Third_House": "H3",
        "Fourth_House": "H4", "Fifth_House": "H5", "Sixth_House": "H6",
        "Seventh_House": "H7", "Eighth_House": "H8", "Ninth_House": "H9",
        "Tenth_House": "H10", "Eleventh_House": "H11", "Twelfth_House": "H12",
    },
    "es": {
        "First_House": "Casa 1", "Second_House": "Casa 2", "Third_House": "Casa 3",
        "Fourth_House": "Casa 4", "Fifth_House": "Casa 5", "Sixth_House": "Casa 6",
        "Seventh_House": "Casa 7", "Eighth_House": "Casa 8", "Ninth_House": "Casa 9",
        "Tenth_House": "Casa 10", "Eleventh_House": "Casa 11", "Twelfth_House": "Casa 12",
    },
}

LABELS = {
    "en": {
        "natal_title":      "NATAL CHART",
        "sr_title":         "SOLAR RETURN",
        "born":             "Born",
        "location":         "Location",
        "sr_location":      "SR Location",
        "sr_date":          "SR Date",
        "planets":          "PLANETS",
        "angles":           "ANGLES",
        "houses":           "HOUSE CUSPS",
        "aspects":          "KEY ASPECTS (orb ≤ 8°)",
        "ascendant":        "Ascendant",
        "mc":               "MC (Midheaven)",
        "descendant":       "Descendant",
        "ic":               "IC (Nadir)",
        "house_col":        "House",
        "degree_col":       "Degree",
        "orb":              "orb",
        "retrograde":       "℞",
        "planet_col":       "Planet",
        "sign_col":         "Sign",
        "at":               "at",
        "in":               "in",
    },
    "es": {
        "natal_title":      "CARTA NATAL",
        "sr_title":         "REVOLUCIÓN SOLAR",
        "born":             "Nacido/a",
        "location":         "Lugar",
        "sr_location":      "Lugar RS",
        "sr_date":          "Fecha RS",
        "planets":          "PLANETAS",
        "angles":           "ÁNGULOS",
        "houses":           "CÚSPIDES DE CASAS",
        "aspects":          "ASPECTOS CLAVE (orbe ≤ 8°)",
        "ascendant":        "Ascendente",
        "mc":               "MC (Medio Cielo)",
        "descendant":       "Descendente",
        "ic":               "IC (Fondo del Cielo)",
        "house_col":        "Casa",
        "degree_col":       "Grado",
        "orb":              "orbe",
        "retrograde":       "℞",
        "planet_col":       "Planeta",
        "sign_col":         "Signo",
        "at":               "a las",
        "in":               "en",
    },
}

MONTHS = {
    "en": {
        1: "January", 2: "February", 3: "March", 4: "April",
        5: "May", 6: "June", 7: "July", 8: "August",
        9: "September", 10: "October", 11: "November", 12: "December",
    },
    "es": {
        1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
        5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
        9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre",
    },
}


def t(key: str, lang: str) -> str:
    """Get a translated label."""
    lang = lang if lang in LABELS else "en"
    return LABELS[lang].get(key, LABELS["en"].get(key, key))


def sign_name(abbr: str, lang: str) -> str:
    lang = lang if lang in SIGNS else "en"
    return SIGNS[lang].get(abbr, abbr)


def planet_name(name: str, lang: str) -> str:
    lang = lang if lang in PLANETS else "en"
    return PLANETS[lang].get(name, name)


def aspect_name(name: str, lang: str) -> str:
    lang = lang if lang in ASPECTS else "en"
    return ASPECTS[lang].get(name, name)


def house_label(house_str: str, lang: str) -> str:
    lang = lang if lang in HOUSES else "en"
    return HOUSES[lang].get(str(house_str), str(house_str))


def format_date(year: int, month: int, day: int, hour: int, minute: int, lang: str) -> str:
    lang = lang if lang in MONTHS else "en"
    month_name = MONTHS[lang][month]
    if lang == "es":
        return f"{day} de {month_name} de {year}, {hour:02d}:{minute:02d}"
    return f"{day} {month_name} {year}, {hour:02d}:{minute:02d}"
