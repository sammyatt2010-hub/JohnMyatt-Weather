# Dad's Weather Station
# A personalised two-home weather app: Middle Farm (Fairoak, Eccleshall) and Salcombe.
# Forecast data: Open-Meteo (free, no API key needed) - https://open-meteo.com

import datetime as dt
import re

import altair as alt
import pandas as pd
import requests
import streamlit as st

# ---------------------------------------------------------------------------
# Personalise here
# ---------------------------------------------------------------------------
DAD_NAME = "Dad"  # change to his name if you like, e.g. "John"

LOCATIONS = {
    "Middle Farm": {
        "icon": "🚜",
        "subtitle": "Fairoak, Eccleshall, Staffordshire · ST21 6NT",
        "lat": 52.8943,
        "lon": -2.3515,
        "coastal": False,
    },
    "Salcombe": {
        "icon": "⛵",
        "subtitle": "Salcombe, South Devon",
        "lat": 50.2380,
        "lon": -3.7700,
        "coastal": True,
        # Sea point just off Bolt Head, used for wave & sea temperature data
        "sea_lat": 50.200,
        "sea_lon": -3.780,
    },
}

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
MARINE_URL = "https://marine-api.open-meteo.com/v1/marine"
TZ = "Europe/London"

st.set_page_config(page_title=f"{DAD_NAME}'s Weather", page_icon="🪷", layout="wide")

# ---------------------------------------------------------------------------
# Styling - big, friendly, easy to read on a phone
# ---------------------------------------------------------------------------
# Two Monet palettes: a sunlit pond for light mode, a moonlit pond for dark mode.
PALETTES = {
    "light": {
        "bg": "#f2f5ef", "text": "#23343a", "muted": "rgba(35,52,58,.70)", "heading": "#2f5560",
        "card": "rgba(255,255,255,.62)", "border": "rgba(94,143,163,.22)", "shadow": "rgba(47,85,96,.10)",
        "wash": ".40,.28,.35,.35,.22", "warn_bg": "rgba(255,240,228,.80)", "alert_bg": "rgba(255,228,233,.85)",
        "rain": "#3f7690", "link": "#2f5560",
    },
    "dark": {
        "bg": "#121f24", "text": "#e9efe9", "muted": "rgba(233,239,233,.68)", "heading": "#d9cdf3",
        "card": "rgba(24,42,48,.72)", "border": "rgba(169,155,209,.22)", "shadow": "rgba(0,0,0,.35)",
        "wash": ".28,.22,.30,.20,.12", "warn_bg": "rgba(217,144,95,.18)", "alert_bg": "rgba(184,71,94,.22)",
        "rain": "#8cc3db", "link": "#c9bdf0",
    },
}


def theme_mode() -> str:
    try:
        return "dark" if st.context.theme.type == "dark" else "light"
    except Exception:
        return "light"


def apply_theme():
    p = PALETTES[theme_mode()]
    w = p["wash"].split(",")
    css = """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,600;0,700;1,600&family=Nunito+Sans:wght@400;600;700&display=swap');
      :root {
        --pond: #2f5560; --water: #5e8fa3; --lilac: #a99bd1; --lily: #e3a1b5; --pad: #6f9a5b;
        --bg: __BG__; --text: __TEXT__; --muted: __MUTED__; --heading: __HEADING__; --card: __CARD__; --border: __BORDER__;
        --shadow: __SHADOW__; --warn-bg: __WARNBG__; --alert-bg: __ALERTBG__; --rain: __RAIN__; --link: __LINK__;
      }
      /* An impressionist wash behind everything: lilac sky, green pads, blue water, pink lilies */
      .stApp {
        background:
          radial-gradient(ellipse 60% 40% at 8% 0%,   rgba(169,155,209,__W0__), transparent 70%),
          radial-gradient(ellipse 50% 35% at 92% 6%,  rgba(111,154,91,__W1__),  transparent 70%),
          radial-gradient(ellipse 70% 45% at 50% 100%, rgba(94,143,163,__W2__), transparent 70%),
          radial-gradient(ellipse 30% 25% at 85% 75%, rgba(227,161,181,__W3__), transparent 70%),
          radial-gradient(ellipse 25% 20% at 15% 60%, rgba(232,196,122,__W4__), transparent 70%),
          var(--bg) !important;
        background-attachment: fixed !important;
        color: var(--text);
      }
      .stApp, .stApp p, .stApp li, .stApp label, .stApp span, .stCaption, .stMarkdown {font-family: 'Nunito Sans', sans-serif;}
      .stApp p, .stApp li, .stApp label, .stMarkdown, div[data-testid="stMetricValue"] {color: var(--text) !important;}
      .stCaption, .stCaption p, div[data-testid="stMetricLabel"] p, .muted {color: var(--muted) !important;}
      .stApp a {color: var(--link) !important;}
      h1, h2, h3, .serif {font-family: 'Cormorant Garamond', Georgia, serif !important; color: var(--heading) !important;}
      h1 {font-size: 3rem !important; font-weight: 700 !important;}
      h2, h3 {font-weight: 700 !important;}
      .block-container {padding-top: 1.6rem; max-width: 1150px;}

      /* Cards (any st.container with a key starting "card") */
      [class*="st-key-card"] {
        background: var(--card); border: 1px solid var(--border); border-radius: 22px;
        padding: 18px 22px 20px 22px; backdrop-filter: blur(8px); box-shadow: 0 6px 20px var(--shadow);
      }
      [class*="st-key-card"] h3 {margin-top: 0 !important; padding-top: 0 !important;}

      .hero {
        position: relative; border-radius: 26px; padding: 30px 32px; color: #fff; margin-bottom: 6px;
        --hero-img: none; background-color: var(--pond);
        background-image: var(--hero-overlay), var(--hero-img),
          linear-gradient(135deg, #2f5560 0%, #5e8fa3 45%, #a99bd1 80%, #e3a1b5 100%);
        background-size: cover; background-position: center;
        box-shadow: 0 10px 30px var(--shadow);
        text-shadow: 0 2px 10px rgba(0,0,0,.45);
        --hero-overlay: linear-gradient(100deg, rgba(25,48,56,.72) 0%, rgba(25,48,56,.38) 55%, rgba(25,48,56,.10) 100%);
      }
      .hero.night {--hero-overlay: linear-gradient(100deg, rgba(12,20,40,.85) 0%, rgba(20,30,60,.65) 60%, rgba(20,30,60,.45) 100%);}
      .hero.wet   {--hero-overlay: linear-gradient(100deg, rgba(40,52,62,.80) 0%, rgba(55,70,82,.55) 60%, rgba(55,70,82,.30) 100%);}
      .hero, .hero * {color: #fff !important;}
      .hero .place {font-size: 1.05rem; opacity: .95; margin: 0 0 6px 0;}
      .hero .row {display: flex; align-items: center; gap: 24px; flex-wrap: wrap;}
      .hero .emoji {font-size: 5.2rem; line-height: 1;}
      .hero .temp {font-family: 'Cormorant Garamond', Georgia, serif; font-size: 5.4rem; font-weight: 700; line-height: .95;}
      .hero .desc {font-size: 1.5rem; font-weight: 700;}
      .hero .sub  {font-size: 1.08rem;}
      .backdrop {font-size: .85rem; color: var(--muted); margin: 0 0 14px 6px; font-style: italic;}

      div[data-testid="stMetric"] {
        background: var(--card); border-radius: 16px; padding: 10px 14px;
        border: 1px solid var(--border); backdrop-filter: blur(6px);
      }
      [class*="st-key-card"] div[data-testid="stMetric"] {background: transparent;}
      div[data-testid="stMetricValue"] {font-size: 1.7rem;}

      .tip {
        border-radius: 14px; padding: 12px 16px; margin: 6px 0; font-size: 1.08rem; color: var(--text);
        background: var(--card); border: 1px solid var(--border); border-left: 5px solid var(--pad);
      }
      .tip.warn  {border-left-color: #d9905f; background: var(--warn-bg);}
      .tip.alert {border-left-color: #b8475e; background: var(--alert-bg);}

      .day {
        display: grid; grid-template-columns: 92px 44px 1fr 150px 110px;
        align-items: center; gap: 10px; padding: 10px 6px; border-bottom: 1px solid var(--border);
        font-size: 1.05rem; color: var(--text);
      }
      .day:last-child {border-bottom: none;}
      .day .name {font-weight: 700; color: var(--heading);}
      .day .ico {font-size: 1.7rem; text-align: center;}
      .bar-wrap {display: flex; align-items: center; gap: 8px;}
      .bar-track {flex: 1; height: 9px; border-radius: 6px; background: var(--border); position: relative;}
      .bar-fill  {position: absolute; height: 9px; border-radius: 6px;
                  background: linear-gradient(90deg, var(--water), var(--lilac), var(--lily));}
      .muted {font-size: .92rem;}
      .rain {color: var(--rain); font-weight: 700;}
      .hour {text-align: center; color: var(--text);}

      header[data-testid="stHeader"] {background: transparent !important;}
      header a[data-testid="stTopNavLink"] p, header a p {font-weight: 700; font-size: 1.02rem;}
      .footer {text-align: center; padding: 8px 0 4px 0;}
      .footer .serif {font-size: 1.35rem; font-style: italic;}

      @media (max-width: 640px) {
        h1 {font-size: 2.3rem !important;}
        .hero {padding: 22px 20px;}
        [class*="st-key-card"] {padding: 14px 14px 16px 14px;}
        .hero .emoji {font-size: 3.6rem;} .hero .temp {font-size: 3.8rem;}
        .day {grid-template-columns: 70px 34px 1fr 92px; font-size: .95rem;}
        .day .wind {display: none;}
      }
    </style>
    """
    for k, v in {"BG": p["bg"], "TEXT": p["text"], "MUTED": p["muted"], "HEADING": p["heading"],
                 "CARD": p["card"], "BORDER": p["border"], "SHADOW": p["shadow"], "WARNBG": p["warn_bg"],
                 "ALERTBG": p["alert_bg"], "RAIN": p["rain"], "LINK": p["link"]}.items():
        css = css.replace(f"__{k}__", v)
    for i, v in enumerate(w):
        css = css.replace(f"__W{i}__", v)
    st.markdown(css, unsafe_allow_html=True)


apply_theme()

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
@st.cache_data(ttl=900, show_spinner=False)  # refresh every 15 minutes
def get_forecast(lat: float, lon: float) -> dict:
    params = {
        "latitude": lat,
        "longitude": lon,
        "timezone": TZ,
        "wind_speed_unit": "mph",
        "forecast_days": 14,
        "current": ",".join([
            "temperature_2m", "relative_humidity_2m", "apparent_temperature", "is_day",
            "precipitation", "weather_code", "cloud_cover", "pressure_msl",
            "wind_speed_10m", "wind_direction_10m", "wind_gusts_10m",
        ]),
        "hourly": ",".join([
            "temperature_2m", "apparent_temperature", "precipitation_probability",
            "precipitation", "weather_code", "wind_speed_10m", "wind_gusts_10m",
            "wind_direction_10m", "is_day",
        ]),
        "daily": ",".join([
            "weather_code", "temperature_2m_max", "temperature_2m_min", "precipitation_sum",
            "precipitation_probability_max", "wind_speed_10m_max", "wind_gusts_10m_max",
            "wind_direction_10m_dominant", "sunrise", "sunset", "uv_index_max",
        ]),
    }
    r = requests.get(FORECAST_URL, params=params, timeout=20)
    r.raise_for_status()
    return r.json()


@st.cache_data(ttl=1800, show_spinner=False)
def get_marine(lat: float, lon: float) -> dict | None:
    params = {
        "latitude": lat,
        "longitude": lon,
        "timezone": TZ,
        "forecast_days": 7,
        "hourly": "wave_height,wave_direction,wave_period,sea_surface_temperature",
        "daily": "wave_height_max",
    }
    try:
        r = requests.get(MARINE_URL, params=params, timeout=20)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def to_frames(data: dict):
    hourly = pd.DataFrame(data["hourly"])
    hourly["time"] = pd.to_datetime(hourly["time"])
    hourly["precipitation_probability"] = hourly["precipitation_probability"].fillna(0)
    daily = pd.DataFrame(data["daily"])
    daily["precipitation_probability_max"] = daily["precipitation_probability_max"].fillna(0)
    daily["uv_index_max"] = daily["uv_index_max"].fillna(0)
    daily["time"] = pd.to_datetime(daily["time"])
    for c in ("sunrise", "sunset"):
        daily[c] = pd.to_datetime(daily[c])
    return data["current"], hourly, daily


# ---------------------------------------------------------------------------
# Wikipedia / Wikimedia Commons (Monet backdrop + Painting Finder)
# ---------------------------------------------------------------------------
WIKI_API = "https://en.wikipedia.org/w/api.php"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
WIKI_HEADERS = {"User-Agent": "DadsWeatherApp/1.0 (personal Streamlit app)"}

# Monet water-garden paintings used as the weather card backdrop (one per day, rotating)
MONET_PAINTINGS = [
    "Water Lilies (Monet series)",
    "Bridge over a Pond of Water Lilies",
    "Le Bassin Aux Nymphéas",
    "The Water Lily Pond",
    "Water Lilies and Japanese Bridge",
]


def wiki_get(url: str, params: dict) -> dict:
    params = {"format": "json", "formatversion": 2, **params}
    r = requests.get(url, params=params, headers=WIKI_HEADERS, timeout=20)
    r.raise_for_status()
    return r.json()


def strip_html(text) -> str:
    return re.sub(r"<[^>]+>", "", str(text or "")).strip()


@st.cache_data(ttl=86400, show_spinner=False)
def monet_backdrops() -> list[dict]:
    """Large images of Monet water-lily paintings from Wikipedia (cached for a day)."""
    try:
        data = wiki_get(WIKI_API, {
            "action": "query", "titles": "|".join(MONET_PAINTINGS), "redirects": 1,
            "prop": "pageimages|info", "piprop": "thumbnail", "pithumbsize": 1600, "inprop": "url",
        })
    except Exception:
        return []
    out = []
    for p in data.get("query", {}).get("pages", []):
        thumb = (p.get("thumbnail") or {}).get("source")
        if thumb:
            out.append({"title": p["title"], "img": thumb, "url": p.get("fullurl", "")})
    return out


def todays_backdrop() -> dict | None:
    options = monet_backdrops()
    if not options:
        return None
    return options[dt.date.today().toordinal() % len(options)]


@st.cache_data(ttl=3600, show_spinner=False)
def search_wikipedia(query: str) -> list[dict]:
    data = wiki_get(WIKI_API, {
        "action": "query", "generator": "search", "gsrsearch": query, "gsrlimit": 18, "gsrnamespace": 0,
        "prop": "pageimages|description|info", "piprop": "thumbnail|original", "pithumbsize": 500,
        "pilicense": "any", "inprop": "url",
    })
    results = []
    for p in sorted(data.get("query", {}).get("pages", []), key=lambda x: x.get("index", 99)):
        orig = p.get("original")
        if not orig:
            continue
        results.append({
            "title": p["title"],
            "subtitle": p.get("description", ""),
            "thumb": (p.get("thumbnail") or {}).get("source", orig["source"]),
            "full": orig["source"],
            "width": orig.get("width"), "height": orig.get("height"), "bytes": None,
            "page": p.get("fullurl", ""), "page_label": "📖 Wikipedia page",
        })
    return results


@st.cache_data(ttl=3600, show_spinner=False)
def search_commons(query: str, min_px: int) -> list[dict]:
    data = wiki_get(COMMONS_API, {
        "action": "query", "generator": "search", "gsrsearch": f"{query} filetype:bitmap",
        "gsrnamespace": 6, "gsrlimit": 40,
        "prop": "imageinfo", "iiprop": "url|size|extmetadata", "iiurlwidth": 500,
        "iiextmetadatafilter": "Artist|DateTimeOriginal|ObjectName",
    })
    results = []
    for p in sorted(data.get("query", {}).get("pages", []), key=lambda x: x.get("index", 99)):
        info = (p.get("imageinfo") or [None])[0]
        if not info or max(info.get("width", 0), info.get("height", 0)) < min_px:
            continue
        meta = info.get("extmetadata", {})
        title = strip_html(meta.get("ObjectName", {}).get("value")) or p["title"].removeprefix("File:").rsplit(".", 1)[0]
        bits = [strip_html(meta.get("Artist", {}).get("value")), strip_html(meta.get("DateTimeOriginal", {}).get("value"))]
        results.append({
            "title": title[:120],
            "subtitle": " · ".join(b[:60] for b in bits if b),
            "thumb": info.get("thumburl", info["url"]),
            "full": info["url"],
            "width": info.get("width"), "height": info.get("height"), "bytes": info.get("size"),
            "page": info.get("descriptionurl", ""), "page_label": "🗂️ Commons page",
        })
    return results


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
WMO = {
    0: ("☀️", "🌙", "Clear sky"),
    1: ("🌤️", "🌙", "Mostly clear"),
    2: ("⛅", "☁️", "Partly cloudy"),
    3: ("☁️", "☁️", "Overcast"),
    45: ("🌫️", "🌫️", "Fog"),
    48: ("🌫️", "🌫️", "Freezing fog"),
    51: ("🌦️", "🌧️", "Light drizzle"),
    53: ("🌦️", "🌧️", "Drizzle"),
    55: ("🌧️", "🌧️", "Heavy drizzle"),
    56: ("🌧️", "🌧️", "Freezing drizzle"),
    57: ("🌧️", "🌧️", "Freezing drizzle"),
    61: ("🌦️", "🌧️", "Light rain"),
    63: ("🌧️", "🌧️", "Rain"),
    65: ("🌧️", "🌧️", "Heavy rain"),
    66: ("🌧️", "🌧️", "Freezing rain"),
    67: ("🌧️", "🌧️", "Heavy freezing rain"),
    71: ("🌨️", "🌨️", "Light snow"),
    73: ("🌨️", "🌨️", "Snow"),
    75: ("❄️", "❄️", "Heavy snow"),
    77: ("🌨️", "🌨️", "Snow grains"),
    80: ("🌦️", "🌧️", "Light showers"),
    81: ("🌧️", "🌧️", "Showers"),
    82: ("⛈️", "⛈️", "Heavy showers"),
    85: ("🌨️", "🌨️", "Snow showers"),
    86: ("❄️", "❄️", "Heavy snow showers"),
    95: ("⛈️", "⛈️", "Thunderstorms"),
    96: ("⛈️", "⛈️", "Thunderstorms with hail"),
    99: ("⛈️", "⛈️", "Severe thunderstorms with hail"),
}


def describe(code, is_day=1):
    day_icon, night_icon, text = WMO.get(int(code), ("🌡️", "🌡️", "Unknown"))
    return (day_icon if is_day else night_icon), text


def compass(deg) -> str:
    points = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
              "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    return points[int((float(deg) % 360) / 22.5 + 0.5) % 16]


def beaufort(mph: float) -> str:
    scale = [(1, "Calm"), (4, "Light air"), (8, "Light breeze"), (13, "Gentle breeze"),
             (19, "Moderate breeze"), (25, "Fresh breeze"), (32, "Strong breeze"),
             (39, "Near gale"), (47, "Gale"), (55, "Severe gale"), (64, "Storm"),
             (73, "Violent storm")]
    for limit, name in scale:
        if mph < limit:
            return name
    return "Hurricane force"


def fmt_hour(t: pd.Timestamp) -> str:
    h = t.hour
    if h == 0:
        return "midnight"
    if h == 12:
        return "midday"
    return f"{h % 12}{'am' if h < 12 else 'pm'}"


def day_name(t: pd.Timestamp, today: dt.date) -> str:
    if t.date() == today:
        return "Today"
    if t.date() == today + dt.timedelta(days=1):
        return "Tomorrow"
    return t.strftime("%a %d")


def build_tips(place: dict, now_t, hourly, daily, marine) -> list[tuple[str, str]]:
    """Plain-English notes for the day. Returns (css_class, text)."""
    tips = []
    next24 = hourly[(hourly["time"] >= now_t) & (hourly["time"] < now_t + pd.Timedelta(hours=24))]
    today, tomorrow = daily.iloc[0], daily.iloc[1]

    # Rain timing
    wet = next24[(next24["precipitation_probability"] >= 50) & (next24["precipitation"] >= 0.2)]
    if wet.empty:
        tips.append(("tip", "☂️ No proper rain expected in the next 24 hours."))
    else:
        first = wet.iloc[0]["time"]
        when = "now" if first <= now_t + pd.Timedelta(hours=1) else f"from about {fmt_hour(first)}"
        if first.date() != now_t.date():
            when += " tomorrow"
        total = next24["precipitation"].sum()
        tips.append(("tip", f"🌧️ Rain likely {when} — around {total:.1f} mm over the next 24 hours."))

    # Driest daylight window in the next 12 hours
    window = next24[(next24["time"] < now_t + pd.Timedelta(hours=12)) & (next24["is_day"] == 1)]
    best, run = [], []
    for _, row in window.iterrows():
        if row["precipitation_probability"] < 25:
            run.append(row["time"])
            if len(run) > len(best):
                best = list(run)
        else:
            run = []
    if len(best) >= 2 and not wet.empty:
        end = best[-1] + pd.Timedelta(hours=1)
        tips.append(("tip", f"🚶 Best dry spell to get out: {fmt_hour(best[0])} – {fmt_hour(end)}."))

    # Frost (tonight = tomorrow morning's minimum)
    low = round(min(today["temperature_2m_min"], tomorrow["temperature_2m_min"])) + 0  # +0 avoids '-0'
    if low <= 0:
        tips.append(("tip warn", f"❄️ Frost likely — dropping to {low:.0f}°C. Watch for ice on the lanes."))
    elif low <= 3:
        tips.append(("tip", f"🌡️ Chilly night ahead ({low:.0f}°C) — a ground frost is possible in sheltered spots."))

    # Wind
    gust = today["wind_gusts_10m_max"]
    if gust >= 50:
        tips.append(("tip alert", f"🌪️ Damaging gusts possible — up to {gust:.0f} mph. Secure anything loose."))
    elif gust >= 38:
        tips.append(("tip warn", f"💨 Gale-force gusts up to {gust:.0f} mph today."))
    elif gust >= 28:
        tips.append(("tip", f"🍃 Blustery, gusting to {gust:.0f} mph."))

    # Drying day
    if (today["precipitation_probability_max"] <= 20 and today["wind_speed_10m_max"] >= 6
            and today["temperature_2m_max"] >= 8):
        tips.append(("tip", "👕 A good drying day — get the washing out."))

    # Heavy rain
    if today["precipitation_sum"] >= 15:
        tips.append(("tip warn", f"🌊 A very wet day — {today['precipitation_sum']:.0f} mm forecast. Puddles and possible flooding."))

    # UV
    if today["uv_index_max"] >= 6:
        tips.append(("tip warn", f"🧴 High UV today ({today['uv_index_max']:.0f}) — hat and sun cream."))

    # Sea (Salcombe)
    if place.get("coastal") and marine and marine.get("daily"):
        waves = marine["daily"].get("wave_height_max") or []
        if waves and waves[0] is not None:
            w = waves[0]
            if w >= 3:
                tips.append(("tip warn", f"🌊 Rough sea off the Bar today — waves up to {w:.1f} m."))
            elif w <= 0.8:
                tips.append(("tip", f"⛵ Calm sea today — waves under {max(w, 0.1):.1f} m. Lovely for the water."))
    return tips


def hourly_chart(df: pd.DataFrame) -> alt.Chart:
    df = df.copy()
    df["label"] = df["time"].dt.strftime("%a %H:%M")
    df["rain_chance"] = df["precipitation_probability"].fillna(0)
    base = alt.Chart(df).encode(alt.X("time:T", title=None, axis=alt.Axis(format="%a %Hh", labelAngle=0, tickCount=8)))
    bars = base.mark_bar(opacity=0.35, color="#5e8fa3", width=6).encode(
        alt.Y("rain_chance:Q", title="Chance of rain (%)", scale=alt.Scale(domain=[0, 100])),
        tooltip=[alt.Tooltip("label:N", title="Time"), alt.Tooltip("rain_chance:Q", title="Rain chance %"),
                 alt.Tooltip("precipitation:Q", title="Rain (mm)", format=".1f")],
    )
    line = base.mark_line(color="#c76b8a", strokeWidth=3, interpolate="monotone").encode(
        alt.Y("temperature_2m:Q", title="Temperature (°C)", scale=alt.Scale(zero=False)),
        tooltip=[alt.Tooltip("label:N", title="Time"),
                 alt.Tooltip("temperature_2m:Q", title="Temp °C", format=".1f"),
                 alt.Tooltip("apparent_temperature:Q", title="Feels like °C", format=".1f")],
    )
    return alt.layer(bars, line).resolve_scale(y="independent").properties(height=320)


def wind_chart(df: pd.DataFrame) -> alt.Chart:
    long = df.melt(id_vars="time", value_vars=["wind_speed_10m", "wind_gusts_10m"], var_name="kind", value_name="mph")
    long["kind"] = long["kind"].map({"wind_speed_10m": "Wind", "wind_gusts_10m": "Gusts"})
    return (
        alt.Chart(long)
        .mark_line(strokeWidth=2.5, interpolate="monotone")
        .encode(
            alt.X("time:T", title=None, axis=alt.Axis(format="%a %Hh", labelAngle=0, tickCount=8)),
            alt.Y("mph:Q", title="mph"),
            alt.Color("kind:N", title=None, scale=alt.Scale(domain=["Wind", "Gusts"], range=["#4f7d3e", "#a99bd1"]),
                      legend=alt.Legend(orient="top")),
            tooltip=[alt.Tooltip("time:T", title="Time", format="%a %H:%M"), "kind:N",
                     alt.Tooltip("mph:Q", format=".0f")],
        )
        .properties(height=240)
    )


def daily_rows_html(daily: pd.DataFrame, today: dt.date, days: int) -> str:
    d = daily.head(days)
    lo_all, hi_all = d["temperature_2m_min"].min(), d["temperature_2m_max"].max()
    span = max(hi_all - lo_all, 1)
    rows = []
    for _, r in d.iterrows():
        icon, text = describe(r["weather_code"])
        left = (r["temperature_2m_min"] - lo_all) / span * 100
        width = max((r["temperature_2m_max"] - r["temperature_2m_min"]) / span * 100, 4)
        rain_pct = r["precipitation_probability_max"]
        rain_pct = 0 if pd.isna(rain_pct) else rain_pct
        rain = f"<span class='rain'>💧 {rain_pct:.0f}%</span>" if rain_pct >= 20 else "<span class='muted'>dry</span>"
        if r["precipitation_sum"] >= 0.5:
            rain += f" <span class='muted'>{r['precipitation_sum']:.0f}mm</span>"
        rows.append(
            f"<div class='day' title='{text}'>"
            f"<div class='name'>{day_name(r['time'], today)}</div>"
            f"<div class='ico'>{icon}</div>"
            f"<div class='bar-wrap'><span class='muted'>{r['temperature_2m_min']:.0f}°</span>"
            f"<div class='bar-track'><div class='bar-fill' style='left:{left:.0f}%;width:{width:.0f}%'></div></div>"
            f"<b>{r['temperature_2m_max']:.0f}°</b></div>"
            f"<div>{rain}</div>"
            f"<div class='wind muted'>💨 {r['wind_speed_10m_max']:.0f} mph {compass(r['wind_direction_10m_dominant'])}</div>"
            f"</div>"
        )
    return "".join(rows)


def hero_html(name: str, place: dict, current: dict, today_row, backdrop: dict | None) -> str:
    icon, text = describe(current["weather_code"], current["is_day"])
    cls = "hero"
    if not current["is_day"]:
        cls += " night"
    elif current["weather_code"] >= 51:
        cls += " wet"
    style = f"--hero-img: url('{backdrop['img'].replace(chr(39), '%27')}');" if backdrop else ""
    return f"""
    <div class="{cls}" style="{style}">
      <p class="place">{place['icon']} <b>{name}</b> · {place['subtitle']}</p>
      <div class="row">
        <div class="emoji">{icon}</div>
        <div>
          <div class="temp">{current['temperature_2m']:.0f}°C</div>
          <div class="desc">{text}</div>
        </div>
        <div class="sub">
          Feels like <b>{current['apparent_temperature']:.0f}°C</b><br>
          Today: high <b>{today_row['temperature_2m_max']:.0f}°</b> · low <b>{today_row['temperature_2m_min']:.0f}°</b><br>
          Wind {current['wind_speed_10m']:.0f} mph from the {compass(current['wind_direction_10m'])}
          ({beaufort(current['wind_speed_10m']).lower()})
        </div>
      </div>
    </div>
    """


# ---------------------------------------------------------------------------
# Weather page
# ---------------------------------------------------------------------------
def weather_page():
    hello_hour = dt.datetime.now().hour  # server time is UTC; close enough for a greeting
    greeting = "Good morning" if hello_hour < 12 else "Good afternoon" if hello_hour < 18 else "Good evening"

    top_l, top_r = st.columns([4, 1], vertical_alignment="bottom")
    with top_l:
        st.title(f"🪷 {DAD_NAME}'s Weather")
        st.caption(f"{greeting}, {DAD_NAME}! Genuine forecasts for Middle Farm and Salcombe — no fakes here 😉")
    with top_r:
        if st.button("🔄 Refresh", width="stretch"):
            st.cache_data.clear()
            st.rerun()

    choice = st.segmented_control(
        "Which home?",
        options=list(LOCATIONS.keys()),
        format_func=lambda k: f"{LOCATIONS[k]['icon']} {k}",
        default="Middle Farm",
        label_visibility="collapsed",
    )
    choice = choice or "Middle Farm"
    place = LOCATIONS[choice]

    try:
        with st.spinner("Checking the skies..."):
            data = get_forecast(place["lat"], place["lon"])
            marine = get_marine(place["sea_lat"], place["sea_lon"]) if place.get("coastal") else None
    except Exception as e:
        st.error("Sorry — couldn't reach the weather service just now. Please try Refresh in a minute.")
        st.caption(f"Details: {e}")
        st.stop()

    current, hourly, daily = to_frames(data)
    now_t = pd.Timestamp(current["time"]).floor("h")
    today = now_t.date()
    today_row = daily.iloc[0]

    # --- Now & today -----------------------------------------------------------
    if True:
        backdrop = todays_backdrop()
        st.markdown(hero_html(choice, place, current, today_row, backdrop), unsafe_allow_html=True)
        if backdrop:
            st.markdown(f"<div class='backdrop'>Today's backdrop: <a href='{backdrop['url']}' target='_blank'>{backdrop['title']}</a> — Claude Monet</div>", unsafe_allow_html=True)

        m = st.columns(4)
        m[0].metric("💨 Gusts", f"{current['wind_gusts_10m']:.0f} mph")
        m[1].metric("💧 Rain chance today", f"{(today_row['precipitation_probability_max'] or 0):.0f}%",
                    help=f"{today_row['precipitation_sum']:.1f} mm expected today")
        m[2].metric("💦 Humidity", f"{current['relative_humidity_2m']:.0f}%")
        m[3].metric("🧭 Pressure", f"{current['pressure_msl']:.0f} hPa")

        m = st.columns(4)
        m[0].metric("🌅 Sunrise", today_row["sunrise"].strftime("%H:%M"))
        m[1].metric("🌇 Sunset", today_row["sunset"].strftime("%H:%M"))
        daylight = today_row["sunset"] - today_row["sunrise"]
        hrs, mins = divmod(int(daylight.total_seconds() // 60), 60)
        m[2].metric("🕰️ Daylight", f"{hrs}h {mins}m")
        m[3].metric("😎 UV max", f"{today_row['uv_index_max']:.0f}")

    with st.container(key="card_expect"):
        st.subheader("☀️ What to expect today")
        for css, text in build_tips(place, now_t, hourly, daily, marine):
            st.markdown(f"<div class='{css}'>{text}</div>", unsafe_allow_html=True)

    with st.container(key="card_rest"):
        st.subheader("🕰️ The next 12 hours")
        rest = hourly[(hourly["time"] >= now_t) & (hourly["time"] < now_t + pd.Timedelta(hours=12))]
        cols = st.columns(6)
        for i, (_, r) in enumerate(rest.iloc[::2].head(6).iterrows()):
            icon, text = describe(r["weather_code"], r["is_day"])
            with cols[i]:
                st.markdown(
                    f"<div class='hour'><div class='muted'>{fmt_hour(r['time'])}</div>"
                    f"<div style='font-size:2rem'>{icon}</div><b>{r['temperature_2m']:.0f}°</b>"
                    f"<div class='muted'>💧{r['precipitation_probability']:.0f}%</div></div>",
                    unsafe_allow_html=True,
                )

    # --- Next 48 hours ---------------------------------------------------------
    with st.container(key="card_48h"):
        next48 = hourly[(hourly["time"] >= now_t) & (hourly["time"] < now_t + pd.Timedelta(hours=48))]
        st.subheader("⏱️ Next 48 hours")
        st.markdown("**Temperature & chance of rain**")
        st.altair_chart(hourly_chart(next48), width="stretch")
        st.markdown("**Wind & gusts**")
        st.altair_chart(wind_chart(next48), width="stretch")
        with st.expander("Hour-by-hour table"):
            table = pd.DataFrame({
                "Time": next48["time"].dt.strftime("%a %H:%M"),
                "Weather": [" ".join(describe(c, d)) for c, d in zip(next48["weather_code"], next48["is_day"])],
                "Temp °C": next48["temperature_2m"].round(0),
                "Feels °C": next48["apparent_temperature"].round(0),
                "Rain %": next48["precipitation_probability"],
                "Rain mm": next48["precipitation"].round(1),
                "Wind mph": next48["wind_speed_10m"].round(0),
                "Gust mph": next48["wind_gusts_10m"].round(0),
                "From": next48["wind_direction_10m"].map(compass),
            })
            st.dataframe(table, hide_index=True, width="stretch")

    # --- 14-day outlook --------------------------------------------------------
    with st.container(key="card_14d"):
        st.subheader(f"📅 The fortnight ahead at {choice}")
        st.markdown(daily_rows_html(daily, today, 14), unsafe_allow_html=True)
        st.caption("Forecasts beyond about 7 days are a rough guide — check back nearer the time.")

    # --- Sea (Salcombe only) ---------------------------------------------------
    if place.get("coastal"):
        with st.container(key="card_sea"):
            st.subheader("🌊 Sea conditions off Salcombe")
            if not marine or not marine.get("hourly"):
                st.info("Sea data isn't available right now — try again later.")
            else:
                mh = pd.DataFrame(marine["hourly"])
                mh["time"] = pd.to_datetime(mh["time"])
                nowrow = mh[mh["time"] >= now_t].head(1)
                if not nowrow.empty:
                    r = nowrow.iloc[0]
                    c = st.columns(3)
                    c[0].metric("🌊 Waves now", f"{r['wave_height']:.1f} m" if pd.notna(r["wave_height"]) else "–")
                    c[1].metric("⏲️ Wave period", f"{r['wave_period']:.0f} s" if pd.notna(r["wave_period"]) else "–")
                    sst = r.get("sea_surface_temperature")
                    c[2].metric("🌡️ Sea temperature", f"{sst:.1f}°C" if pd.notna(sst) else "–")
                seven = mh[mh["time"] >= now_t]
                st.altair_chart(
                    alt.Chart(seven).mark_area(opacity=0.5, color="#5e8fa3", line={"color": "#2f5560"}, interpolate="monotone")
                    .encode(
                        alt.X("time:T", title=None, axis=alt.Axis(format="%a %d", labelAngle=0)),
                        alt.Y("wave_height:Q", title="Wave height (m)"),
                        tooltip=[alt.Tooltip("time:T", format="%a %H:%M", title="Time"),
                                 alt.Tooltip("wave_height:Q", format=".1f", title="Waves (m)")],
                    ).properties(height=260),
                    width="stretch",
                )
                st.caption("Open-sea waves just off Bolt Head — the estuary itself is usually calmer. "
                           "Always check official tide times and the inshore waters forecast before going out.")

    # --- Both homes ------------------------------------------------------------
    with st.container(key="card_both"):
        st.subheader("🏡 Middle Farm vs Salcombe — the week ahead")
        frames = {}
        cols = st.columns(2)
        for col, (name, p) in zip(cols, LOCATIONS.items()):
            try:
                cur, _, dly = to_frames(get_forecast(p["lat"], p["lon"]))
            except Exception:
                col.warning(f"Couldn't load {name}.")
                continue
            frames[name] = dly.head(7).assign(place=name)
            icon, text = describe(cur["weather_code"], cur["is_day"])
            with col:
                st.markdown(f"<h3 class='serif' style='margin:0'>{p['icon']} {name}</h3>", unsafe_allow_html=True)
                st.metric(f"{icon} {text}", f"{cur['temperature_2m']:.0f}°C",
                          help=f"Feels like {cur['apparent_temperature']:.0f}°C")
                st.markdown(daily_rows_html(dly, today, 7), unsafe_allow_html=True)

        if len(frames) == 2:
            both = pd.concat(frames.values())
            st.markdown("**Daytime highs**")
            st.altair_chart(
                alt.Chart(both).mark_line(point=True, strokeWidth=3)
                .encode(
                    alt.X("time:T", title=None, axis=alt.Axis(format="%a %d", labelAngle=0)),
                    alt.Y("temperature_2m_max:Q", title="High (°C)", scale=alt.Scale(zero=False)),
                    alt.Color("place:N", title=None, scale=alt.Scale(domain=list(LOCATIONS), range=["#6f9a5b", "#5e8fa3"]),
                              legend=alt.Legend(orient="top")),
                    tooltip=["place:N", alt.Tooltip("time:T", format="%A %d %b", title="Day"),
                             alt.Tooltip("temperature_2m_max:Q", format=".0f", title="High °C")],
                ).properties(height=260),
                width="stretch",
            )
            warmer = (frames["Salcombe"]["temperature_2m_max"].mean()
                      - frames["Middle Farm"]["temperature_2m_max"].mean())
            wetter = (frames["Salcombe"]["precipitation_sum"].sum()
                      - frames["Middle Farm"]["precipitation_sum"].sum())
            st.markdown(
                f"<div class='tip'>☀️ Salcombe is set to be <b>{abs(warmer):.1f}°C {'warmer' if warmer >= 0 else 'cooler'}</b> "
                f"on average this week, with <b>{abs(wetter):.0f} mm {'more' if wetter >= 0 else 'less'}</b> rain than Middle Farm.</div>",
                unsafe_allow_html=True,
            )

    st.divider()
    st.caption(f"Last updated {pd.Timestamp(current['time']).strftime('%H:%M, %A %d %B')} · "
               "Forecast data by [Open-Meteo](https://open-meteo.com) (includes Met Office models) · Refreshes every 15 minutes")
    show_footer()



def show_footer():
    c = st.columns([2, 1, 2])
    c[1].page_link("https://www.johnmyatt.com", label="johnmyatt.com", icon="🎨", width="stretch")


# ---------------------------------------------------------------------------
# Painting Finder page
# ---------------------------------------------------------------------------
SUGGESTIONS = [
    "Monet Water Lilies", "Turner Fighting Temeraire", "Constable The Hay Wain",
    "Van Gogh Starry Night", "Vermeer Girl with a Pearl Earring", "Renoir Luncheon of the Boating Party",
]


def human_size(n) -> str:
    if not n:
        return ""
    return f" · {n / 1_048_576:.1f} MB" if n >= 1_048_576 else f" · {n / 1024:.0f} KB"


def _use_suggestion():
    if st.session_state.get("suggestion"):
        st.session_state.painting_query = st.session_state.suggestion


def paintings_page():
    st.title("🖼️ Painting Finder")
    st.caption("High-resolution images of paintings from Wikipedia and Wikimedia Commons.")

    st.text_input("Painting or artist", key="painting_query",
                  placeholder="e.g. Monet Impression Sunrise  ·  Turner Rain Steam and Speed")
    st.pills("Try one of these", SUGGESTIONS, key="suggestion", on_change=_use_suggestion)

    c1, c2 = st.columns([2, 1])
    source = c1.segmented_control(
        "Search", ["Wikipedia articles", "Wikimedia Commons (more versions)"],
        default="Wikimedia Commons (more versions)",
        help="Commons usually has several scans of each painting, often at very high resolution. "
             "Wikipedia gives the main image from each article.",
    ) or "Wikimedia Commons (more versions)"
    min_label = c2.selectbox("Minimum size (longest side)", ["Any", "1,000 px", "2,000 px", "4,000 px", "6,000 px"], index=2,
                             disabled=source.startswith("Wikipedia"))
    min_px = 0 if min_label == "Any" else int(min_label.split()[0].replace(",", ""))

    query = (st.session_state.get("painting_query") or "").strip()
    if not query:
        st.info("Type a painting or artist above, or tap a suggestion, to find high-resolution images.")
        show_footer_back()
        return

    try:
        with st.spinner("Searching the galleries..."):
            results = search_wikipedia(query) if source.startswith("Wikipedia") else search_commons(query, min_px)
    except Exception as e:
        st.error("Couldn't reach Wikipedia just now — please try again in a moment.")
        st.caption(f"Details: {e}")
        return

    if not results:
        st.warning("No images found. Try adding the artist's name, a lower minimum size, or the other search.")
        show_footer_back()
        return

    st.caption(f"{len(results)} result{'s' if len(results) != 1 else ''} for “{query}” — "
               "tap **Full resolution** to open the original image (then save it from there).")
    for i in range(0, len(results), 3):
        cols = st.columns(3)
        for j, (col, r) in enumerate(zip(cols, results[i:i + 3])):
            with col.container(key=f"card_result_{i + j}"):
                st.image(r["thumb"])
                st.markdown(f"**{r['title']}**")
                if r["subtitle"]:
                    st.caption(r["subtitle"])
                if r["width"] and r["height"]:
                    st.caption(f"📐 {r['width']:,} × {r['height']:,} px{human_size(r['bytes'])}")
                b1, b2 = st.columns(2)
                b1.link_button("🔍 Full resolution", r["full"], width="stretch")
                if r["page"]:
                    b2.link_button(r["page_label"], r["page"], width="stretch")
    st.caption("Images come from Wikimedia. Most old-master paintings are public domain; "
               "check the Commons page for the licence of anything more recent.")
    show_footer_back()


def show_footer_back():
    st.divider()
    show_footer()


# ---------------------------------------------------------------------------
# Navigation
# ---------------------------------------------------------------------------
WEATHER_PAGE = st.Page(weather_page, title=f"{DAD_NAME}'s Weather", icon="🪷", url_path="weather", default=True)
PAINTINGS_PAGE = st.Page(paintings_page, title="Painting Finder", icon="🖼️", url_path="paintings")
st.navigation([WEATHER_PAGE, PAINTINGS_PAGE], position="top").run()
