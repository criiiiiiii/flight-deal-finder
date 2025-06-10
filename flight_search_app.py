import streamlit as st
import requests
from datetime import date, timedelta

st.title("🛫 Flight Deal Finder (Fly Scraper API)")

# --- Origin Selection ---
origin_map = {
    "Detroit (DTW)": "DTMI",
    "Windsor (YQG)": "YQGI",
    "Toronto (YYZ)": "YYZI"
}
origin_choice = st.selectbox("Origin Airport", list(origin_map.keys()))
origin_sky_id = origin_map[origin_choice]

# --- Destination Input ---
destination = st.text_input("Destination SkyID (e.g. NYCA, MSYA, LONA)", "NYCA")

# --- Trip Type ---
trip_type = st.radio("Trip Type", ["One-way", "Round-trip"])

# --- Dates ---
departure_date = st.date_input("Departure Date", date.today() + timedelta(days=30))
trip_length = st.slider("Trip Length (days)", min_value=3, max_value=21, value=7)
return_date = departure_date + timedelta(days=trip_length)

# --- Passengers ---
adults = st.slider("Adults", min_value=1, max_value=6, value=2)
children = st.slider("Children", min_value=0, max_value=4, value=2)

# --- Trip Summary ---
if trip_type == "Round-trip":
    st.caption(f"🗓️ Round-trip: {departure_date.strftime('%Y-%m-%d')} → {return_date.strftime('%Y-%m-%d')}")
else:
    st.caption(f"🗓️ One-way trip on {departure_date.strftime('%Y-%m-%d')}")

# --- API Call ---
if st.button("🔍 Search Flights"):
    url = "https://fly-scraper.p.rapidapi.com/flights/search-one-way"

    querystring = {
        "originSkyId": origin_sky_id,
        "destinationSkyId": destination,
        "adults": str(adults),
        "children": str(children)
    }

    headers = {
        "x-rapidapi-host": "fly-scraper.p.rapidapi.com",
        "x-rapidapi-key": "215a6826f2mshc7e99c81ebbe6e0p129a86jsn13e40defdfae"
    }

    if trip_type == "Round-trip":
        st.info("🔁 Round-trip selected, but only one-way results are supported for now.")

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


