import requests
import streamlit as st


GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"

AIR_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

WEATHER_URL = "https://api.open-meteo.com/v1/forecast"


def get_aqi_category(aqi):

    if aqi is None:
        return "Unavailable"

    if aqi <= 50:
        return "Good"

    elif aqi <= 100:
        return "Moderate"

    elif aqi <= 150:
        return "Unhealthy for Sensitive Groups"

    elif aqi <= 200:
        return "Unhealthy"

    elif aqi <= 300:
        return "Very Unhealthy"

    return "Hazardous"


@st.cache_data(ttl=900)
def get_city_conditions(city_name):

    # 1. Find city coordinates
    geo_response = requests.get(
        GEO_URL,
        params={
            "name": city_name,
            "count": 1,
            "language": "en",
            "format": "json"
        },
        timeout=15
    )

    geo_response.raise_for_status()

    locations = geo_response.json().get("results", [])

    if not locations:
        return {
            "error": f"Could not find city: {city_name}"
        }

    location = locations[0]

    latitude = location["latitude"]
    longitude = location["longitude"]

    # 2. Fetch air quality
    air_response = requests.get(
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

    air_response.raise_for_status()

    air = air_response.json().get("current", {})

    # 3. Fetch weather
    weather_response = requests.get(
        WEATHER_URL,
        params={
            "latitude": latitude,
            "longitude": longitude,
            "current": (
                "temperature_2m,"
                "relative_humidity_2m,"
                "wind_speed_10m,"
                "weather_code"
            ),
            "timezone": "auto"
        },
        timeout=20
    )

    weather_response.raise_for_status()

    weather = weather_response.json().get("current", {})

    aqi = air.get("us_aqi")

    return {
        "city": location.get("name"),
        "region": location.get("admin1"),
        "country": location.get("country"),

        "latitude": latitude,
        "longitude": longitude,

        "aqi": aqi,
        "aqi_category": get_aqi_category(aqi),

        "pm2_5": air.get("pm2_5"),
        "pm10": air.get("pm10"),
        "nitrogen_dioxide": air.get("nitrogen_dioxide"),
        "sulphur_dioxide": air.get("sulphur_dioxide"),
        "ozone": air.get("ozone"),
        "carbon_monoxide": air.get("carbon_monoxide"),

        "temperature": weather.get("temperature_2m"),
        "humidity": weather.get("relative_humidity_2m"),
        "wind_speed": weather.get("wind_speed_10m"),

        "timestamp": air.get("time"),

        "source": "Open-Meteo",
        "aqi_scale": "US AQI",
        "data_type": "Model-based estimate"
    }