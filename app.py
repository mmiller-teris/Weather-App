import streamlit as st
import requests

st.title("🌤️ Weather App")
st.write("Enter a city to see the current temperature and today's rainfall.")

city = st.text_input("City name", placeholder="e.g. Austin, London, Tokyo")

if city:
    url = f"https://wttr.in/{city}?format=j1"
    response = requests.get(url)

    if response.status_code != 200:
        st.error("City not found. Please check the spelling and try again.")
    else:
        data = response.json()

        current = data["current_condition"][0]
        nearest = data["nearest_area"][0]

        city_name = nearest["areaName"][0]["value"]
        country = nearest["country"][0]["value"]
        temp_f = current["temp_F"]
        rain_mm = current["precipMM"]

        st.subheader(f"📍 {city_name}, {country}")

        col1, col2 = st.columns(2)

        with col1:
            st.metric(label="🌡️ Current Temperature", value=f"{temp_f}°F")

        with col2:
            st.metric(label="🌧️ Today's Rainfall", value=f"{rain_mm} mm")