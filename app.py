import streamlit as st
import requests
import plotly.graph_objects as go
from datetime import datetime, timezone, timedelta
from collections import defaultdict

HEADERS = {"User-Agent": "weatherapp mmiller@teris.com"}

def celsius_to_fahrenheit(c):
    if c is None:
        return None
    return round((c * 9/5) + 32, 1)

def mm_to_inches(mm):
    if mm is None:
        return 0
    return round(mm / 25.4, 2)

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

def get_noaa_temperatures(station_id):
    url = f"https://api.weather.gov/stations/{station_id}/observations?limit=240"
    response = requests.get(url, headers=HEADERS).json()
    observations = response["features"]

    daily = defaultdict(list)
    for obs in observations:
        props = obs["properties"]
        timestamp = props["timestamp"]
        date = datetime.fromisoformat(timestamp).astimezone(timezone.utc).strftime("%Y-%m-%d")
        temp_c = props["temperature"]["value"]
        if temp_c is not None:
            daily[date].append(celsius_to_fahrenheit(temp_c))

    results = {}
    for date in sorted(daily.keys())[-10:]:
        temps = daily[date]
        if temps:
            results[date] = {"high": max(temps), "low": min(temps)}
    return results

def get_rainfall(lat, lon):
    end_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
    url = (
        f"https://archive-api.open-meteo.com/v1/archive"
        f"?latitude={lat}&longitude={lon}"
        f"&start_date={start_date}&end_date={end_date}"
        f"&daily=precipitation_sum"
        f"&timezone=America/Chicago"
    )
    response = requests.get(url).json()
    dates = response["daily"]["time"]
    precips = response["daily"]["precipitation_sum"]
    return {date: mm_to_inches(precip) for date, precip in zip(dates, precips)}

# --- UI ---
st.title("🌤️ Weather App")
st.write("Enter a US city to see current conditions and a 10 day history.")

city = st.text_input("City name", placeholder="e.g. Austin, Dallas, Chicago")

if city:
    with st.spinner("Fetching weather data..."):
        coords = get_coordinates(city)

        if not coords:
            st.error("City not found. Please check the spelling and try again.")
        else:
            lat, lon, city_name, country = coords
            st.subheader(f"📍 {city_name}, {country}")

            try:
                # Current conditions
                wttr = requests.get(f"https://wttr.in/{city}?format=j1").json()
                current = wttr["current_condition"][0]
                temp_f = current["temp_F"]
                precip_mm = current["precipMM"]
                description = current["weatherDesc"][0]["value"]

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(label="🌡️ Current Temp", value=f"{temp_f}°F")
                with col2:
                    st.metric(label="🌧️ Precipitation", value=f"{mm_to_inches(float(precip_mm))} in")
                with col3:
                    st.metric(label="🌥️ Conditions", value=description)

                st.divider()
                st.subheader("📊 Last 10 Days")

                # Temperature data from NOAA
                station_id = get_nearest_station(lat, lon)
                temp_data = get_noaa_temperatures(station_id)
                temp_dates = sorted(temp_data.keys())
                highs = [temp_data[d]["high"] for d in temp_dates]
                lows = [temp_data[d]["low"] for d in temp_dates]

                # Rainfall data from Open-Meteo archive
                rain_data = get_rainfall(lat, lon)
                rain_dates = sorted(rain_data.keys())
                precips = [rain_data[d] for d in rain_dates]

                # Temperature chart
                fig_temp = go.Figure()
                fig_temp.add_trace(go.Scatter(
                    x=temp_dates, y=highs,
                    name="High °F",
                    line=dict(color="#E8593C", width=2),
                    fill=None
                ))
                fig_temp.add_trace(go.Scatter(
                    x=temp_dates, y=lows,
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
                    x=rain_dates, y=precips,
                    name="Rainfall (in)",
                    marker_color="#3B8BD4"
                ))
                fig_rain.update_layout(
                    title="Daily Rainfall Total (inches)",
                    xaxis_title="Date",
                    yaxis_title="Rainfall (inches)",
                    height=300
                )
                st.plotly_chart(fig_rain, use_container_width=True)

            except Exception as e:
                st.error(f"Something went wrong: {e}")