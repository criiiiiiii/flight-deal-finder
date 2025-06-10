import streamlit as st
import requests
from datetime import datetime

st.title("🌍 Family Flight Deal Finder")

# --- Search Inputs ---
origin = st.selectbox("Departure Airport", ["DTW", "YQG"])
date_from = st.date_input("Earliest Departure Date", datetime(2025, 8, 15))
date_to = st.date_input("Latest Return Date", datetime(2025, 12, 31))

if st.button("🔍 Search Deals"):
    url = "https://api.skypicker.com/flights"
    params = {
        "fly_from": origin,
        "date_from": date_from.strftime("%d/%m/%Y"),
        "date_to": date_to.strftime("%d/%m/%Y"),
        "partner": "picky",
        "limit": 5,
        "curr": "USD"
    }

    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        flights = data.get("data", [])
        if flights:
            for flight in flights:
                city_to = flight["cityTo"]
                price = flight["price"]
                route = " ➔ ".join([r["cityTo"] for r in flight["route"]])
                dtime = datetime.fromtimestamp(flight["dTimeUTC"]).strftime("%Y-%m-%d %H:%M")
                atime = datetime.fromtimestamp(flight["aTimeUTC"]).strftime("%Y-%m-%d %H:%M")
                st.markdown(f"""
                **✈️ To {city_to} — ${price}**  
                Route: {route}  
                Departure: {dtime} UTC  
                Arrival: {atime} UTC  
                ---
                """)
        else:
            st.warning("No flights found for the given parameters.")
    else:
        st.error(f"API request failed with status code {response.status_code}")

