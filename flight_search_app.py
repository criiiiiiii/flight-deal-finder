import streamlit as st
import requests
import time
from datetime import datetime, timedelta

# --- UI Setup ---
st.set_page_config(page_title="Family Flight Finder", layout="centered")
st.title("✈️ Family Flight Finder (Sky API)")

# --- User Inputs ---
airports = {"DTW": "DTW", "YQG": "YQG", "YYZ": "YYZ"}
origin = st.selectbox("Select Departure Airport", list(airports.keys()))
destination = st.text_input("Enter Destination Airport Code (e.g. LAX, JFK)")
trip_type = st.radio("Trip Type", ["Roundtrip", "One-way"])
departure_date = st.date_input("Departure Date", value=datetime.today())
trip_length = st.slider("Trip Length (Days)", min_value=1, max_value=21, value=7) if trip_type == "Roundtrip" else None
adults = st.slider("Adults", 1, 6, 1)
children = st.slider("Children", 0, 6, 0)
min_price = st.number_input("Minimum Price ($)", min_value=0, value=0)
max_price = st.number_input("Maximum Price ($)", min_value=0, value=1500)

# --- API Config ---
API_HOST = "flights-sky.p.rapidapi.com"
API_KEY = "215a6826f2mshc7e99c81ebbe6e0p129a86jsn13e40defdfae"
HEADERS = {
    "x-rapidapi-host": API_HOST,
    "x-rapidapi-key": API_KEY,
    "content-type": "application/json"
}

# --- Helper Functions ---
def get_place_id(query):
    url = f"https://{API_HOST}/web/flights/auto-complete?q={query}"
    r = requests.get(url, headers=HEADERS)
    results = r.json().get("data", [])
    return results[0].get("placeId") if results else None

def poll_until_complete(session_id):
    url = f"https://{API_HOST}/web/flights/search-incomplete?sessionId={session_id}"
    for _ in range(10):
        time.sleep(2)
        r = requests.get(url, headers=HEADERS)
        data = r.json().get("data", {})
        if data.get("context", {}).get("status") == "complete":
            return data.get("itineraries", {}).get("results", [])
    return []

# --- Search Button ---
if st.button("🔍 Search Flights"):
    if not destination:
        st.error("Please enter a destination airport code.")
    else:
        st.info("Searching for flights...")

        place_from = get_place_id(airports[origin])
        place_to = get_place_id(destination)

        if not place_from or not place_to:
            st.error("Could not resolve airport codes. Try different values.")
        else:
            base_url = f"https://{API_HOST}/web/flights/search-{trip_type.lower()}"
            params = {
                "market": "US",
                "locale": "en-US",
                "currency": "USD",
                "adults": adults,
                "children": children,
                "placeIdFrom": place_from,
                "placeIdTo": place_to,
                "departDate": departure_date.strftime("%Y-%m-%d")
            }

            if trip_type == "Roundtrip":
                return_date = departure_date + timedelta(days=trip_length)
                params["returnDate"] = return_date.strftime("%Y-%m-%d")

            r = requests.get(base_url, headers=HEADERS, params=params)
            response_data = r.json().get("data", {})

            if response_data.get("context", {}).get("status") == "incomplete":
                session_id = response_data["context"]["sessionId"]
                results = poll_until_complete(session_id)
            else:
                results = response_data.get("itineraries", {}).get("results", [])

            # --- Display Results ---
            if not results:
                st.warning("No flights found.")
            else:
                for flight in results:
                    price = flight.get("price", {}).get("raw")
                    if price and min_price <= price <= max_price:
                        airline = flight.get("legs", [{}])[0].get("carriers", [{}])[0].get("name", "Unknown")
                        times = flight.get("legs", [{}])[0].get("duration", {}).get("humanReadable", "")
                        st.success(f"{airline} - {times} - ${price}")

