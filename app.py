import streamlit as st
import requests

st.title("🌤️ Weather App")
st.write("Enter a city to see the current temperature and today's rainfall.")

city = st.text_input("City name", placeholder="e.g. Austin, London, Tokyo")

if city:
    # Step 1: Look up city coordinates
    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"
    geo_response = requests.get(geo_url).json()

    if "results" not in geo_response:
        st.error("City not found. Please check the spelling and try again.")
    else:
        location = geo_response["results"][0]
        lat = location["latitude"]
        lon = location["longitude"]
        country = location["country"]

        st.subheader(f"📍 {location['name']}, {country}")

        # Step 2: Fetch weather data
        weather_url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            f"&current=temperature_2m,rain"
            f"&daily=rain_sum"
            f"&temperature_unit=fahrenheit"
            f"&timezone=auto"
        )
        weather = requests.get(weather_url).json()

        temp = weather["current"]["temperature_2m"]
        rain_today = weather["daily"]["rain_sum"][0]

        # Step 3: Display results
        col1, col2 = st.columns(2)

        with col1:
            st.metric(label="🌡️ Current Temperature", value=f"{temp}°F")

        with col2:
            st.metric(label="🌧️ Today's Rainfall", value=f"{rain_today} mm")