import streamlit as st
import requests
from datetime import datetime

st.title("🌍 Family Flight Deal Finder")

# --- Inputs ---
origin = st.selectbox("Departure Airport", ["DTW", "YQG"])
date_from = st.date_input("Earliest Departure Date", datetime(2025, 8, 15))
date_to = st.date_input("Latest Return Date", datetime(2025, 12, 31))

if st.button("🔍 Search Deals"):
    url = "https://kiwi-com-cheap-flights.p.rapidapi.com/roundtrip"

    querystring = {
        "from": origin,
        "adults": "2",
        "children": "2",
        "currency": "USD",
        "departureDate": date_from.strftime("%Y-%m-%d"),
        "returnDate": date_to.strftime("%Y-%m-%d")
    }

    headers = {
        "X-RapidAPI-Key": "215a6826f2mshc7e99c81ebbe6e0p129a86jsn13e40defdfae",
        "X-RapidAPI-Host": "kiwi-com-cheap-flights.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)

    if response.status_code == 200:
        data = response.json()
        itineraries = data.get("Itineraries", [])
        if itineraries:
            for flight in itineraries:
                dest = flight.get("to", "Unknown")
                price = flight.get("price", "N/A")
                st.markdown(f"""
                **✈️ Destination: {dest} — ${price}**  
                ---
                """)
        else:
            st.warning("No flights found for the given parameters.")
    else:
        st.error(f"API request failed with status code {response.status_code}")



