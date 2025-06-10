import streamlit as st
import requests
from datetime import datetime

st.title("🌍 Family Flight Deal Finder")

# --- Search Inputs ---
origin = st.selectbox("Departure Airport", ["DTW", "YQG"])
date_from = st.date_input("Earliest Departure Date", datetime(2025, 8, 15))
date_to = st.date_input("Latest Return Date", datetime(2025, 12, 31))

if st.button("🔍 Search Deals"):
    url = "https://kiwi-flight-search.p.rapidapi.com/flights"

    querystring = {
        "fly_from": origin,
        "date_from": date_from.strftime("%d/%m/%Y"),
        "date_to": date_to.strftime("%d/%m/%Y"),
        "nights_in_dst_from": "7",
        "nights_in_dst_to": "14",
        "adults": "2",
        "children": "2",
        "curr": "USD",
        "limit": "5",
        "max_stopovers": "1"
    }

    headers = {
        "X-RapidAPI-Key": "215a6826f2mshc7e99c81ebbe6e0p129a86jsn13e40defdfae",  # your actual key
        "X-RapidAPI-Host": "kiwi-flight-search.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)

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

