import streamlit as st
import requests
from datetime import date, timedelta

st.title("🛫 Flight Deal Finder ")

# --- Input: Search Filters ---
origin_map = {
    "Detroit (DTW)": "DTMI",
    "Windsor (YQG)": "YQGI",
    "Toronto (YYZ)": "YYZI"
}
origin_choice = st.selectbox("Origin Airport", list(origin_map.keys()))
origin_sky_id = origin_map[origin_choice]

# Placeholder destination list for now (we'll improve this later)
destination = st.text_input("Destination SkyID (e.g. NYCA, MSYA, LONA)", "NYCA")

# Trigger search
if st.button("🔍 Search Flights"):
    url = "https://fly-scraper.p.rapidapi.com/flights/search-one-way"
    querystring = {
        "originSkyId": origin_sky_id,
        "destinationSkyId": destination
    }
    headers = {
        "x-rapidapi-host": "fly-scraper.p.rapidapi.com",
        "x-rapidapi-key": "215a6826f2mshc7e99c81ebbe6e0p129a86jsn13e40defdfae"
    }

    response = requests.get(url, headers=headers, params=querystring)

    if response.status_code == 200:
        data = response.json()
        results = data.get("results", [])
        if results:
            for result in results:
                airline = result.get("airline", "Unknown")
                from_city = result.get("fromCity", "Unknown")
                to_city = result.get("toCity", "Unknown")
                price = result.get("price", "N/A")
                departure = result.get("departureTime", "N/A")
                arrival = result.get("arrivalTime", "N/A")

                st.markdown(f"""
                **✈️ {from_city} → {to_city}**  
                Airline: {airline}  
                Price: ${price}  
                Departure: {departure}  
                Arrival: {arrival}  
                ---
                """)
        else:
            st.warning("No flights found.")
    else:
        st.error(f"API request failed with status code {response.status_code}")
