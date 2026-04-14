import streamlit as st
import requests
import plotly.graph_objects as go
from datetime import datetime, timezone
from collections import defaultdict

HEADERS = {"User-Agent": "weatherapp mmiller@teris.com"}

def celsius_to_fahrenheit(c):
    if c is None:
        return None
    return round((c * 9/5) + 32, 1)

def get_coordinates(city):
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"
    response = requests.get(url).json()
    if "results" not in response:
        return None
    result = response["results"][0]
    return result["latitude"], result["longitude"], result["name"], result["country"]

def get_nearest_station(lat, lon):
    url = f"https://api.weather.gov/points/{lat},{lon}"
    response = requests.get(url, headers=HEADERS).json()
    stations_url = response["properties"]["observationStations"]
    stations = requests.get(stations_url, headers=HEADERS).json()
    station_id = stations["features"][0]["properties"]["stationIdentifier"]
    return station_id

def get_observations(station_id):
    url = f"https://api.weather.gov/stations/{station_id}/observations?limit=240"
    response = requests.get(url, headers=HEADERS).json()
    return response["features"]

def process_observations(observations):
    daily = defaultdict(lambda: {"temps": [], "precip": 0.0})

    for obs in observations:
        props = obs["properties"]
        timestamp = props["timestamp"]
        date = datetime.fromisoformat(timestamp).astimezone(timezone.utc).strftime("%Y-%m-%d")

        temp_c = props["temperature"]["value"]
        precip = props["precipitationLastHour"]["value"]

        if temp_c is not None:
            daily[date]["temps"].append(celsius_to_fahrenheit(temp_c))
        if precip is not None:
            daily[date]["precip"] += precip

    results = []
    for date in sorted(daily.keys())[-10:]:
        temps = daily[date]["temps"]
        if temps:
            results.append({
                "date": date,
                "high": max(temps),
                "low": min(temps),
                "precip": round(daily[date]["precip"], 2)
            })

    return results

# --- UI ---
st.title("🌤️ Weather App")
st.write("Enter a city to see current conditions and a 10 day history.")

city = st.text_input("City name", placeholder="e.g. Austin, London, Tokyo")

if city:
    with st.spinner("Fetching weather data..."):
        coords = get_coordinates(city)

        if not coords:
            st.error("City not found. Please check the spelling and try again.")
        else:
            lat, lon, city_name, country = coords
            st.subheader(f"📍 {city_name}, {country}")

            try:
                # Current conditions from wttr.in
                wttr = requests.get(f"https://wttr.in/{city}?format=j1").json()
                current = wttr["current_condition"][0]
                temp_f = current["temp_F"]
                precip_mm = current["precipMM"]
                description = current["weatherDesc"][0]["value"]

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(label="🌡️ Current Temp", value=f"{temp_f}°F")
                with col2:
                    st.metric(label="🌧️ Precipitation", value=f"{precip_mm} mm")
                with col3:
                    st.metric(label="🌥️ Conditions", value=description)

                # Historical chart from NOAA
                st.subheader("📊 Last 10 Days")
                station_id = get_nearest_station(lat, lon)
                observations = get_observations(station_id)
                daily_data = process_observations(observations)

                if daily_data:
                    dates = [d["date"] for d in daily_data]
                    highs = [d["high"] for d in daily_data]
                    lows = [d["low"] for d in daily_data]
                    precips = [d["precip"] for d in daily_data]

                    # Temperature chart
                    fig_temp = go.Figure()
                    fig_temp.add_trace(go.Scatter(
                        x=dates, y=highs,
                        name="High °F",
                        line=dict(color="#E8593C", width=2),
                        fill=None
                    ))
                    fig_temp.add_trace(go.Scatter(
                        x=dates, y=lows,
                        name="Low °F",
                        line=dict(color="#3B8BD4", width=2),
                        fill="tonexty",
                        fillcolor="rgba(59,139,212,0.1)"
                    ))
                    fig_temp.update_layout(
                        title="Daily High / Low Temperature (°F)",
                        xaxis_title="Date",
                        yaxis_title="Temperature (°F)",
                        legend=dict(orientation="h"),
                        height=350
                    )
                    st.plotly_chart(fig_temp, use_container_width=True)

                    # Rainfall chart
                    fig_rain = go.Figure()
                    fig_rain.add_trace(go.Bar(
                        x=dates, y=precips,
                        name="Rainfall (mm)",
                        marker_color="#3B8BD4"
                    ))
                    fig_rain.update_layout(
                        title="Daily Rainfall Total (mm)",
                        xaxis_title="Date",
                        yaxis_title="Rainfall (mm)",
                        height=300
                    )
                    st.plotly_chart(fig_rain, use_container_width=True)

                else:
                    st.warning("Historical data not available for this location.")

            except Exception as e:
                st.error(f"Something went wrong: {e}")