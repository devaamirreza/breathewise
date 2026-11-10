from agent.runner import run_agent
import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

st.set_page_config(
    page_title="BreatheWise",
    page_icon="🌿",
    layout="wide"
)

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
AIR_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

* { font-family: Inter, sans-serif; }

.stApp { background: #f8f7f7; }

header, footer, #MainMenu { visibility: hidden; }

.block-container {
    max-width: 1250px;
    padding: 1.5rem 1rem 3rem;
}

.brand {
    font-size: 27px;
    font-weight: 900;
    color: #193c32;
}

.tagline {
    color: #7c8580;
    font-size: 13px;
    margin-top: -5px;
}

.stTextInput input {
    border-radius: 12px;
    height: 44px;
    background: white;
    border: 1px solid #e6d9dc;
}

.stFormSubmitButton button {
    border-radius: 12px;
    height: 44px;
    background: #bd243d;
    color: white;
    border: none;
    font-weight: 700;
}

.stFormSubmitButton button:hover {
    background: #9f1c32;
    color: white;
}

.advisor {
    background: white;
    border: 1px solid #ece5e5;
    border-radius: 18px;
    padding: 24px;
    margin-top: 24px;
    font-family: Inter, sans-serif;
}

.advisor-title {
    color: #bd243d;
    font-weight: 800;
    font-size: 21px;
}

.advisor-text {
    color: #68736d;
    line-height: 1.8;
    font-size: 14px;
}

@media(max-width: 750px) {
    .block-container { padding: 1rem 0.7rem 2rem; }
}
</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# AQI HELPERS
# --------------------------------------------------

def get_aqi_category(aqi):

    if aqi is None:
        return "Unavailable", "#777777"

    if aqi <= 50:
        return "Good", "#36a66b"

    elif aqi <= 100:
        return "Moderate", "#d6b735"

    elif aqi <= 150:
        return "Unhealthy for Sensitive Groups", "#ed8740"

    elif aqi <= 200:
        return "Unhealthy", "#d9534f"

    elif aqi <= 300:
        return "Very Unhealthy", "#9b4b8d"

    return "Hazardous", "#8b285d"


def get_recommendation(aqi):

    if aqi is None:
        return (
            "INSUFFICIENT DATA",
            "We couldn't retrieve a valid AQI reading. "
            "Please try again later."
        )

    if aqi <= 100:
        return (
            "STAY",
            "Air quality is currently within the Good or "
            "Moderate range. Normal outdoor activities are "
            "generally reasonable."
        )

    elif aqi <= 200:
        return (
            "LIMIT OUTDOOR EXPOSURE",
            "Reduce prolonged or strenuous outdoor activity, "
            "especially if you are sensitive to air pollution."
        )

    return (
        "SEEK CLEANER AIR",
        "Air pollution is elevated. Avoid outdoor exertion, "
        "and consider spending time in a cleaner indoor environment."
    )


def safe_value(data, key, decimals=1):

    value = data.get(key)

    if value is None:
        return "N/A"

    try:
        return round(float(value), decimals)
    except (TypeError, ValueError):
        return "N/A"


# --------------------------------------------------
# API FUNCTIONS
# --------------------------------------------------

@st.cache_data(ttl=1800)
def search_city(city):

    response = requests.get(
        GEO_URL,
        params={
            "name": city,
            "count": 1,
            "language": "en",
            "format": "json"
        },
        timeout=15
    )

    response.raise_for_status()

    results = response.json().get("results", [])

    if not results:
        raise ValueError("City not found. Try another city name.")

    return results[0]


@st.cache_data(ttl=900)
def get_air_quality(latitude, longitude):

    response = requests.get(
        AIR_URL,
        params={
            "latitude": latitude,
            "longitude": longitude,
            "current": (
                "us_aqi,"
                "pm2_5,"
                "pm10,"
                "carbon_monoxide,"
                "nitrogen_dioxide,"
                "sulphur_dioxide,"
                "ozone"
            ),
            "timezone": "auto"
        },
        timeout=20
    )

    response.raise_for_status()

    return response.json()


@st.cache_data(ttl=1800)
def get_weather(latitude, longitude):

    response = requests.get(
        WEATHER_URL,
        params={
            "latitude": latitude,
            "longitude": longitude,
            "current": (
                "temperature_2m,"
                "relative_humidity_2m,"
                "wind_speed_10m,"
                "uv_index,"
                "weather_code"
            ),
            "timezone": "auto"
        },
        timeout=20
    )

    response.raise_for_status()

    return response.json()


def weather_description(code):

    descriptions = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Foggy",
        48: "Rime fog",
        51: "Light drizzle",
        53: "Drizzle",
        55: "Heavy drizzle",
        61: "Light rain",
        63: "Rain",
        65: "Heavy rain",
        71: "Light snowfall",
        73: "Snowfall",
        75: "Heavy snowfall",
        80: "Rain showers",
        81: "Rain showers",
        82: "Heavy rain showers",
        95: "Thunderstorm"
    }

    return descriptions.get(code, "Current conditions")


# --------------------------------------------------
# HEADER
# --------------------------------------------------

header_left, header_right = st.columns([3, 1])

with header_left:

    st.markdown("""
    <div class="brand">🌿 BreatheWise</div>
    <div class="tagline">
        Understand your air. Make smarter decisions.
    </div>
    """, unsafe_allow_html=True)

with header_right:

    india_col, agent_col = st.columns([3, 1])

    with india_col:
        st.markdown("""
        <div style="text-align:right;padding-top:10px;
        font-size:12px;font-weight:700;color:#53645c;">
            INDIA 🇮🇳
        </div>
        """, unsafe_allow_html=True)

    with agent_col:
        if st.button(
            "💬",
            key="toggle_breathewise_agent",
            help="Ask BreatheWise",
            use_container_width=True
        ):
            st.session_state.agent_open = not st.session_state.get("agent_open", False)
            st.rerun()


# --------------------------------------------------
# CITY SEARCH
# --------------------------------------------------

st.write("")

with st.form("city_search"):

    col1, col2 = st.columns([4, 1])

    with col1:
        city_input = st.text_input(
            "Search city",
            value=st.session_state.get("city", ""),
            placeholder="Enter city name"
        )

    with col2:
        st.write("")
        search_clicked = st.form_submit_button(
            "Search →",
            use_container_width=True
        )


if search_clicked:

    if city_input.strip():

        st.session_state["city"] = city_input.strip()

        # Clear cached results when the user searches again.
        search_city.clear()
        get_air_quality.clear()
        get_weather.clear()


city = st.session_state.get("city", "").strip()


# --------------------------------------------------
# INSTANT LOADING LAYOUT
# Render the visual first; API requests run afterwards.
# --------------------------------------------------

hero_slot = st.empty()
advisor_slot = st.empty()

loading_hero_html = f"""
<style>
.bw-loading-hero {{
    position: relative; overflow: hidden; border-radius: 32px;
    min-height: 365px; padding: 36px 6%; box-sizing: border-box;
    color: #34343a; font-family: Inter, sans-serif;
    background: linear-gradient(180deg, #fff5f6 0%, #f5cbd1 40%, #df7787 75%, #d74761 100%);
}}
.bw-loading-content {{ position: relative; z-index: 2; display: grid; grid-template-columns: 58% 42%; gap: 20px; }}
.bw-loading-number {{ font-size: clamp(65px, 9vw, 94px); font-weight: 900; color: #c91f3c; line-height: 1.05; letter-spacing: -5px; }}
.bw-loading-category {{ display: inline-block; padding: 10px 20px; border-radius: 10px; background: rgba(204,37,61,.12); color: #9b4b8d; font-size: 20px; font-weight: 800; }}
.bw-loading-weather {{ margin-top: 35px; padding: 26px 18px; border-radius: 23px; background: rgba(255,255,255,.32); border: 1px solid rgba(255,255,255,.65); text-align: center; }}
.bw-loading-muted {{ color: #805e65; font-size: 13px; }}
.bw-loading-pollutants {{ display:flex; gap:28px; flex-wrap:wrap; margin-top:24px; font-weight:600; }}
.bw-loading-scale {{ display:flex; height:7px; border-radius:20px; overflow:hidden; margin-top:28px; }}
.bw-loading-scale span {{ flex:1; }}
.bw-loading-skyline {{ position:absolute; bottom:0; left:0; width:100%; height:95px; opacity:.15; }}
@media(max-width:750px) {{ .bw-loading-content {{ grid-template-columns:1fr; }} .bw-loading-weather {{ margin-top:14px; }} .bw-loading-hero {{ padding:28px 22px; }} }}
</style>
<div class="bw-loading-hero">
  <div class="bw-loading-content">
    <div>
      <div style="font-size:14px;font-weight:600;">🟠 &nbsp; LIVE MODEL AQI · {city}</div>
      <div style="display:flex;align-items:center;gap:22px;flex-wrap:wrap;margin-top:12px;">
        <div><div class="bw-loading-number">--</div><div class="bw-loading-muted">US AQI · Open-Meteo</div></div>
        <div><div style="font-size:13px;font-weight:600;margin-bottom:8px;">Air quality is</div><div class="bw-loading-category">Fetching data...</div></div>
      </div>
      <div class="bw-loading-pollutants"><div>PM2.5 : <span class="bw-loading-muted">-- µg/m³</span></div><div>PM10 : <span class="bw-loading-muted">-- µg/m³</span></div></div>
      <div class="bw-loading-scale"><span style="background:#36ad58"></span><span style="background:#e4c447"></span><span style="background:#ed8740"></span><span style="background:#dc5252"></span><span style="background:#9b4b8d"></span><span style="background:#8b285d"></span></div>
      <div style="display:flex;justify-content:space-between;font-size:10px;margin-top:8px;color:#573e43;"><span>Good</span><span>Moderate</span><span>Sensitive</span><span>Unhealthy</span><span>Very Poor</span><span>Hazardous</span></div>
    </div>
    <div class="bw-loading-weather"><div style="font-size:34px;">🌤️</div><div style="font-size:25px;font-weight:800;margin:8px 0;">--°C</div><div class="bw-loading-muted">Loading local weather...</div><hr style="border:0;border-top:1px solid rgba(255,255,255,.5);margin:20px 0;"><div class="bw-loading-muted">💧 Humidity &nbsp; --%<br><br>🌬️ Wind speed &nbsp; -- km/h<br><br>☀️ UV index &nbsp; --</div></div>
  </div>
  <svg class="bw-loading-skyline" viewBox="0 0 1200 130" preserveAspectRatio="none"><g fill="#923f50"><path d="M20 130 V65 L60 30 L100 65 V130 Z"/><path d="M180 130 V60 L220 20 L260 60 V130 Z"/><path d="M350 130 V45 L390 5 L430 45 V130 Z"/><path d="M520 130 V60 L560 25 L600 60 V130 Z"/><path d="M750 130 V55 L790 10 L830 55 V130 Z"/><path d="M950 130 V65 L990 25 L1030 65 V130 Z"/></g></svg>
</div>
"""

loading_advisor_html = """
<div style="background:white;border:1px solid #ece5e5;border-radius:18px;padding:24px;margin-top:24px;font-family:Inter,sans-serif;">
  <div style="font-size:13px;font-weight:700;color:#89938d;">🌿 YOUR PERSONAL AIR QUALITY ADVISOR</div>
  <div style="margin-top:12px;color:#89938d;font-weight:800;font-size:21px;">Checking conditions...</div>
  <p style="color:#68736d;line-height:1.8;font-size:14px;margin-bottom:0;">Your recommendation will appear here as soon as the latest air-quality data is available.</p>
</div>
"""

with hero_slot.container():
    st.html(loading_hero_html)

with advisor_slot.container():
    st.html(loading_advisor_html)


# --------------------------------------------------
# FETCH DATA
# --------------------------------------------------

if city:
    try:

        with st.spinner(f"Fetching air quality for {city}..."):

            location = search_city(city)

            latitude = location["latitude"]
            longitude = location["longitude"]

            air_data = get_air_quality(latitude, longitude)
            weather_data = get_weather(latitude, longitude)

            air = air_data.get("current", {})
            weather = weather_data.get("current", {})

            aqi = air.get("us_aqi")

            if aqi is not None:
                aqi = int(round(aqi))

            pm25 = safe_value(air, "pm2_5")
            pm10 = safe_value(air, "pm10")
            no2 = safe_value(air, "nitrogen_dioxide")
            ozone = safe_value(air, "ozone")

            temperature = safe_value(weather, "temperature_2m")
            humidity = safe_value(weather, "relative_humidity_2m")
            wind_speed = safe_value(weather, "wind_speed_10m")
            uv_index = safe_value(weather, "uv_index")

            updated_at = air.get("time", "Unavailable")

            weather_code = weather.get("weather_code")
            weather_text = (
                weather_description(weather_code)
                if weather_code is not None
                else "Unavailable"
            )

            category, category_color = get_aqi_category(aqi)

            recommendation, explanation = get_recommendation(aqi)

            display_city = location.get("name", city)
            region = location.get("admin1", "")
            country = location.get("country", "")

            location_text = ", ".join(
                part for part in [display_city, region, country] if part
            )

    except requests.RequestException as error:

        st.error(f"Unable to connect to the data provider: {error}")
        st.stop()

    except ValueError as error:

        st.error(str(error))
        st.stop()

    except (KeyError, TypeError) as error:

        st.error(f"Unexpected API response: {error}")
        st.stop()
else:
    # Keep the dashboard visible before the user searches for a city.
    location_text = "Search for a city"
    aqi = None
    pm25 = pm10 = no2 = ozone = "N/A"
    temperature = humidity = wind_speed = uv_index = "N/A"
    updated_at = "Not available yet"
    weather_text = "Search for a city"
    category, category_color = get_aqi_category(None)
    recommendation = "SEARCH FOR A CITY"
    explanation = (
        "Enter a city above to see its current air-quality and weather conditions. "
        "Your BreatheWise dashboard and assistant are ready."
    )


# --------------------------------------------------
# HERO DESIGN
# --------------------------------------------------

aqi_display = aqi if aqi is not None else "--"

hero_html = f"""
<style>

.bw-hero {{
    position: relative;
    overflow: hidden;
    border-radius: 32px;
    min-height: 365px;
    padding: 36px 6%;
    color: #34343a;
    background: linear-gradient(
        180deg,
        #fff5f6 0%,
        #f5cbd1 40%,
        #df7787 75%,
        #d74761 100%
    );
    box-sizing: border-box;
    font-family: Inter, sans-serif;
}}

.bw-hero * {{ box-sizing: border-box; }}

.bw-content {{
    position: relative;
    z-index: 2;
    display: grid;
    grid-template-columns: 58% 42%;
    gap: 20px;
}}

.bw-live {{
    font-size: 14px;
    font-weight: 600;
}}

.bw-dot {{
    display: inline-block;
    width: 11px;
    height: 11px;
    background: #e65a38;
    border-radius: 50%;
    margin-right: 8px;
}}

.bw-number {{
    font-size: clamp(65px, 9vw, 94px);
    font-weight: 900;
    color: #c91f3c;
    line-height: 1.05;
    letter-spacing: -5px;
}}

.bw-unit {{
    color: #8c777c;
    font-size: 12px;
}}

.bw-category-label {{
    font-size: 13px;
    font-weight: 600;
    margin-bottom: 8px;
}}

.bw-category {{
    display: inline-block;
    padding: 10px 20px;
    background: rgba(204, 37, 61, .12);
    color: {category_color};
    font-size: 23px;
    font-weight: 800;
    border-radius: 10px;
}}

.bw-pollutants {{
    display: flex;
    gap: 35px;
    margin-top: 25px;
    flex-wrap: wrap;
}}

.bw-pollutant {{
    font-size: 17px;
    font-weight: 600;
}}

.bw-pollutant span {{
    color: #8b5661;
    margin-right: 8px;
}}

.bw-scale {{
    margin-top: 28px;
    max-width: 460px;
}}

.bw-scale-bar {{
    height: 7px;
    display: flex;
    border-radius: 20px;
    background: white;
    overflow: hidden;
}}

.bw-scale-bar div {{ flex: 1; }}

.bw-scale-labels {{
    display: flex;
    justify-content: space-between;
    gap: 5px;
    font-size: 10px;
    margin-top: 8px;
    color: #573e43;
}}

.bw-weather {{
    margin-top: 35px;
    background: rgba(255,255,255,.28);
    border: 1px solid rgba(255,255,255,.65);
    border-radius: 23px;
    backdrop-filter: blur(12px);
    overflow: hidden;
    align-self: start;
}}

.bw-weather-top {{
    display: flex;
    justify-content: space-around;
    align-items: center;
    padding: 24px 12px;
    font-size: 18px;
    gap: 10px;
}}

.bw-weather-bottom {{
    border-top: 1px solid rgba(255,255,255,.5);
    display: flex;
    justify-content: space-around;
    padding: 17px 5px;
    text-align: center;
    font-size: 12px;
}}

.bw-weather-bottom strong {{
    display: block;
    font-size: 15px;
    margin-top: 5px;
}}

.bw-skyline {{
    position: absolute;
    bottom: 0;
    left: 0;
    width: 100%;
    height: 95px;
    opacity: .15;
    z-index: 1;
}}

@media(max-width:750px) {{
    .bw-content {{ grid-template-columns: 1fr; }}
    .bw-weather {{ margin-top: 15px; }}
    .bw-hero {{ padding: 28px 22px; }}
    .bw-pollutants {{ gap: 18px; }}
    .bw-scale-labels {{ font-size: 8px; }}
}}

</style>

<div class="bw-hero">

    <div class="bw-content">

        <div>

            <div class="bw-live">
                <span class="bw-dot"></span>
                Live Model AQI · {location_text}
            </div>

            <div style="display:flex;align-items:center;gap:22px;margin-top:12px;flex-wrap:wrap;">

                <div>
                    <div class="bw-number">{aqi_display}</div>
                    <div class="bw-unit">US AQI · Open-Meteo</div>
                </div>

                <div>
                    <div class="bw-category-label">Air Quality is</div>
                    <div class="bw-category">{category}</div>
                </div>

            </div>

            <div class="bw-pollutants">

                <div class="bw-pollutant">
                    <span>PM2.5 :</span> {pm25}
                    <small>µg/m³</small>
                </div>

                <div class="bw-pollutant">
                    <span>PM10 :</span> {pm10}
                    <small>µg/m³</small>
                </div>

            </div>

            <div class="bw-scale">

                <div class="bw-scale-bar">
                    <div style="background:#36ad58;"></div>
                    <div style="background:#e4c447;"></div>
                    <div style="background:#ed8740;"></div>
                    <div style="background:#dc5252;"></div>
                    <div style="background:#9b4b8d;"></div>
                    <div style="background:#8b285d;"></div>
                </div>

                <div class="bw-scale-labels">
                    <span>Good</span>
                    <span>Moderate</span>
                    <span>Sensitive</span>
                    <span>Unhealthy</span>
                    <span>Very Poor</span>
                    <span>Hazardous</span>
                </div>

                <div class="bw-scale-labels">
                    <span>0</span>
                    <span>50</span>
                    <span>100</span>
                    <span>150</span>
                    <span>200</span>
                    <span>300+</span>
                </div>

            </div>

        </div>

        <div class="bw-weather">

            <div class="bw-weather-top">

                <span style="font-size:35px;">🌤️</span>

                <strong>{temperature}°C</strong>

                <span>{weather_text}</span>

            </div>

            <div class="bw-weather-bottom">

                <div>
                    💧 Humidity
                    <strong>{humidity}%</strong>
                </div>

                <div>
                    🌬️ Wind Speed
                    <strong>{wind_speed} km/h</strong>
                </div>

                <div>
                    ☀️ UV Index
                    <strong>{uv_index}</strong>
                </div>

            </div>

        </div>

    </div>

    <svg class="bw-skyline" viewBox="0 0 1200 130"
         preserveAspectRatio="none">

        <g fill="#923f50">
            <path d="M20 130 V65 L60 30 L100 65 V130 Z"/>
            <path d="M180 130 V60 L220 20 L260 60 V130 Z"/>
            <path d="M350 130 V45 L390 5 L430 45 V130 Z"/>
            <path d="M520 130 V60 L560 25 L600 60 V130 Z"/>
            <path d="M750 130 V55 L790 10 L830 55 V130 Z"/>
            <path d="M950 130 V65 L990 25 L1030 65 V130 Z"/>
        </g>

    </svg>

</div>
"""

with hero_slot.container():
    st.html(hero_html)


# --------------------------------------------------
# ESCAPE ADVISOR
# --------------------------------------------------

advisor_html = f"""
<style>
.bw-advisor {{
    background: white;
    border: 1px solid #ece5e5;
    border-radius: 18px;
    padding: 24px;
    margin-top: 24px;
    font-family: Inter, sans-serif;
}}

.bw-advisor-label {{
    font-size: 13px;
    font-weight: 700;
    color: #89938d;
}}

.bw-advisor-title {{
    margin-top: 12px;
    color: {category_color};
    font-weight: 800;
    font-size: 21px;
}}

.bw-advisor-text {{
    color: #68736d;
    line-height: 1.8;
    font-size: 14px;
}}

</style>

<div class="bw-advisor">

    <div class="bw-advisor-label">
        🌿 YOUR PERSONAL AIR QUALITY ADVISOR
    </div>

    <div class="bw-advisor-title">
        {recommendation}
    </div>

    <p class="bw-advisor-text">
        {explanation}
    </p>

    <div style="font-size:14px;font-weight:700;">
        Pollutant details
    </div>

    <div class="bw-advisor-text">
        PM2.5: {pm25} µg/m³<br>
        PM10: {pm10} µg/m³<br>
        Nitrogen dioxide: {no2} µg/m³<br>
        Ozone: {ozone} µg/m³
    </div>

    <p class="bw-advisor-text">
        Data timestamp: {updated_at}
    </p>

    <p class="bw-advisor-text">
        Source: Open-Meteo Air Quality API.
        Model-based estimates, not direct monitoring-station readings.
    </p>

</div>
"""

with advisor_slot.container():
    st.html(advisor_html)


# --------------------------------------------------
# BREATHEWISE AI AGENT
# --------------------------------------------------

if "agent_messages" not in st.session_state:
    st.session_state.agent_messages = []

if "agent_open" not in st.session_state:
    st.session_state.agent_open = False

if "agent_minimized" not in st.session_state:
    st.session_state.agent_minimized = False

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()


# Floating companion panel: compact, movable-feeling overlay that does not resize the dashboard.
sidebar_height = "76px" if st.session_state.agent_minimized else "min(560px, 58vh)"
mobile_sidebar_height = "76px" if st.session_state.agent_minimized else "min(62vh, 520px)"

st.markdown(f"""
<style>
.st-key-toggle_breathewise_agent button {{
    background: #bd243d !important; color: #fff !important; border: 0 !important;
    border-radius: 50% !important; width: 42px !important; height: 42px !important;
    min-height: 42px !important; padding: 0 !important; font-size: 19px !important;
}}
.st-key-toggle_breathewise_agent button:hover {{ background: #9f1c32 !important; color: #fff !important; }}
section[data-testid="stSidebar"] {{
    position: fixed !important; top: auto !important; bottom: 22px !important;
    right: 18px !important; left: auto !important;
    width: 390px !important; min-width: 330px !important; max-width: calc(100vw - 28px) !important;
    height: {sidebar_height} !important; min-height: {sidebar_height} !important;
    max-height: calc(100vh - 44px) !important;
    z-index: 1000000 !important; border: 1px solid #eadfe1 !important;
    border-radius: 20px !important; background: #fffafa !important;
    box-shadow: 0 18px 55px rgba(45, 28, 32, .20) !important;
    overflow: hidden !important; transform: none !important;
}}
section[data-testid="stSidebar"] > div {{
    height: 100% !important; padding: 14px 14px 12px !important;
    overflow-y: auto !important; overflow-x: hidden !important;
    scrollbar-width: none !important; -ms-overflow-style: none !important;
}}
section[data-testid="stSidebar"] > div::-webkit-scrollbar,
section[data-testid="stSidebar"] [data-testid="stSidebarContent"]::-webkit-scrollbar {{
    width: 0 !important; height: 0 !important; display: none !important;
}}
section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {{
    height: 100% !important; overflow-y: auto !important;
    scrollbar-width: none !important; -ms-overflow-style: none !important;
}}
section[data-testid="stSidebar"] [data-testid="stSidebarHeader"] {{ display: none !important; }}
.bw-agent-caption {{ color: #7c8580; font-size: 12px; line-height: 1.5; }}
.bw-agent-close button, .bw-agent-minimize button {{
    border-radius: 10px !important; border: 1px solid #eadfe1 !important;
    background: white !important; min-height: 34px !important;
}}
@media(max-width: 750px) {{
    section[data-testid="stSidebar"] {{
        top: auto !important; bottom: 12px !important; right: 10px !important; left: 10px !important;
        width: auto !important; min-width: 0 !important; max-width: none !important;
        height: {mobile_sidebar_height} !important; min-height: {mobile_sidebar_height} !important;
        max-height: calc(100vh - 24px) !important;
    }}
}}
</style>
""", unsafe_allow_html=True)

if st.session_state.agent_open:
    with st.sidebar:
        title_col, minimize_col, close_col = st.columns([5, 1, 1])
        with title_col:
            st.markdown("### 🌿 Ask BreatheWise")
        with minimize_col:
            if st.session_state.agent_minimized:
                if st.button("＋", key="expand_breathewise_agent", help="Expand chat"):
                    st.session_state.agent_minimized = False
                    st.rerun()
            else:
                if st.button("−", key="minimize_breathewise_agent", help="Collapse chat"):
                    st.session_state.agent_minimized = True
                    st.rerun()
        with close_col:
            if st.button("✕", key="close_breathewise_agent", help="Close chat"):
                st.session_state.agent_open = False
                st.session_state.agent_minimized = False
                st.rerun()

        if not st.session_state.agent_minimized:
            with st.container(key="agent_panel_body"):
                st.markdown(
                    '<div class="bw-agent-caption">Ask about your air quality, check other cities, or compare locations.</div>',
                    unsafe_allow_html=True
                )
                st.divider()

                if not OPENROUTER_API_KEY:
                    st.info("Add OPENROUTER_API_KEY=your_key to the .env file, then restart BreatheWise.")
                    st.markdown("Get a key from [OpenRouter](https://openrouter.ai/keys).")
                else:
                    if not st.session_state.agent_messages:
                        st.caption("Try asking:")
                        suggestions = [
                            "Is it okay to go for a morning walk?",
                            "What does PM2.5 mean?",
                            "How can I reduce my exposure today?"
                        ]
                        for index, suggestion in enumerate(suggestions):
                            if st.button(suggestion, key=f"agent_suggestion_{index}", use_container_width=True):
                                st.session_state.pending_agent_question = suggestion
                                st.rerun()

                    # Conversation is kept in session_state when the panel is closed/reopened.
                    for message in st.session_state.agent_messages:
                        with st.chat_message(message["role"]):
                            st.markdown(message["content"])

                    typed_question = st.chat_input("Ask about your air quality...", key="breathewise_chat_input")
                    question = typed_question or st.session_state.pop("pending_agent_question", None)

                    if question:
                        # Pass current dashboard readings as structured context.
                        # run_agent manages the user/assistant conversation history.
                        current_context = {
                            "city": location_text,
                            "aqi": aqi,
                            "aqi_scale": "US AQI",
                            "category": category,
                            "pm2_5": pm25,
                            "pm10": pm10,
                            "nitrogen_dioxide": no2,
                            "ozone": ozone,
                            "temperature_c": temperature,
                            "humidity_percent": humidity,
                            "wind_speed_kmh": wind_speed,
                            "uv_index": uv_index,
                            "timestamp": updated_at,
                            "source": "Open-Meteo",
                            "data_type": "Model-based estimate, not a direct monitoring-station reading"
                        }

                        with st.spinner("BreatheWise is thinking..."):
                            try:
                                answer, updated_history = run_agent(
                                    user_message=question,
                                    chat_history=st.session_state.agent_messages,
                                    dashboard_context=current_context
                                )

                                st.session_state.agent_messages = updated_history

                            except requests.RequestException as error:
                                st.error(f"Couldn't reach OpenRouter: {error}")

                            except Exception as error:
                                st.error(f"BreatheWise encountered an error: {error}")

                        st.rerun()

                    if st.session_state.agent_messages:
                        if st.button("Clear conversation", key="clear_agent_chat", use_container_width=True):
                            st.session_state.agent_messages = []
                            st.rerun()

# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.markdown("""
<div style="text-align:center;padding:25px;color:#89938d;font-size:12px;">
    BreatheWise · Breathe better. Live wiser.
    <br>
    Air-quality data by
    <a href="https://open-meteo.com/" target="_blank">Open-Meteo</a>
</div>
""", unsafe_allow_html=True)
