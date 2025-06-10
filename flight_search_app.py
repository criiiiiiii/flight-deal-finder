import streamlit as st
import requests
from datetime import date, timedelta

st.title("🛫 Flight Finder (Flights Sky API)")

# --- User Inputs ---
trip_type = st.radio("Trip Type", ["One-way", "Round-trip"])

origin = st.text_input("Origin Airport Code (e.g. DTW)", "DTW")
destination = st.text_input("Destination Airport Code (e.g. LAX)", "LAX")

departure_date = st.date_input("Departure Date", date.today() + timedelta(days=30))

if trip_type == "Round-trip":
    return_date = st.date_input("Return Date", departure_date + timedelta(days=7))
else:
    return_date = None

adults = st.slider("Adults", 1, 6, 2)
children = st.slider("Children", 0, 4, 0)

currency = st.selectbox("Currency", ["USD", "CAD", "EUR"], index=0)

# --- API Call ---
if st.button("🔍 Search Flights"):
    url = "https://flights-sky.p.rapidapi.com/web/flights/search"

    querystring = {
        "origin": origin,
        "destination": destination,
        "depart": departure_date.strftime("%Y-%m-%d"),
        "adults": str(adults),
        "children": str(children),
        "currency": currency
    }

    if trip_type == "Round-trip":
        querystring["return"] = return_date.strftime("%Y-%m-%d")

    headers = {
        "x-rapidapi-key": "215a6826f2mshc7e99c81ebbe6e0p129a86jsn13e40defdfae",
        "x-rapidapi-host": "flights-sky.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)

    if response.status_code == 200:
        data = response.json()
        results = data.get("data", [])
        if results:
            for flight in results:
                price = flight.get("price", {}).get("raw", "N/A")
                from_code = flight.get("origin", {}).get("code", "")
                to_code = flight.get("destination", {}).get("code", "")
                airline = flight.get("airline", {}).get("name", "Unknown")

                st.markdown(f"""
                **✈️ {from_code} → {to_code}**  
                Airline: {airline}  
                Price: {currency} {price}  
                ---
                """)
        else:
            st.warning("No flights found.")
    else:
        st.error(f"API request failed: {response.status_code} — {response.text}")
