import streamlit as st
import requests
import time
from datetime import date, timedelta

# ─── Configuration ────────────────────────────────────────────────────────────
API_KEY = "215a6826f2mshc7e99c81ebbe6e0p129a86jsn13e40defdfae"
API_HOST = "flights-sky.p.rapidapi.com"
BASE_URL = f"https://{API_HOST}/web/flights"

HEADERS = {
    "x-rapidapi-host": API_HOST,
    "x-rapidapi-key": API_KEY
}

# ─── Helper Functions ─────────────────────────────────────────────────────────

def get_place_id(query: str) -> str:
    """
    Hits the /auto-complete endpoint to resolve a free-text airport/city
    into the API's internal placeId (typically the IATA code).
    """
    url = f"{BASE_URL}/auto-complete"
    params = {"q": query}
    r = requests.get(url, headers=HEADERS, params=params)
    if r.status_code == 200:
        items = r.json().get("data", [])
        if items:
            return items[0].get("placeId")
    return None

def search_flights(
    trip_type: str,
    place_from: str,
    place_to: str,
    depart_date: date,
    return_date: date,
    adults: int,
    children: int,
    min_price: float,
    max_price: float
):
    """
    Executes an initial search (one-way or round-trip), then if the response
    status is "incomplete", polls /search-incomplete until status == "complete".
    Returns (results_list, error_message).
    """
    # Pick the right endpoint
    endpoint = "search-one-way" if trip_type == "One-way" else "search-roundtrip"
    url = f"{BASE_URL}/{endpoint}"

    # Build query params
    params = {
        "placeIdFrom": place_from,
        "placeIdTo": place_to,
        "departDate": depart_date.strftime("%Y-%m-%d"),
        "adults": str(adults),
        "children": str(children),
    }
    if trip_type == "Round-trip":
        params["returnDate"] = return_date.strftime("%Y-%m-%d")
    if min_price > 0:
        params["minPrice"] = str(min_price)
    if max_price > 0:
        params["maxPrice"] = str(max_price)
    params["currency"] = "USD"

    # Initial search request
    resp = requests.get(url, headers=HEADERS, params=params)
    if resp.status_code != 200:
        return None, f"Search failed: {resp.status_code} {resp.text}"

    data = resp.json().get("data", {})
    context = data.get("context", {})
    status = context.get("status")
    token  = context.get("sessionId")
    itineraries = data.get("itineraries", {})

    # Poll if incomplete
    while status == "incomplete":
        time.sleep(1)
        inc_url = f"{BASE_URL}/search-incomplete"
        inc_params = {"token": token}
        inc_resp = requests.get(inc_url, headers=HEADERS, params=inc_params)
        if inc_resp.status_code != 200:
            return None, f"Incomplete fetch failed: {inc_resp.status_code}"
        inc_data    = inc_resp.json().get("data", {})
        context     = inc_data.get("context", {})
        status      = context.get("status")
        itineraries = inc_data.get("itineraries", {})

    # Extract final results array
    results = itineraries.get("results", [])
    return results, None

# ─── Streamlit App ───────────────────────────────────────────────────────────

def main():
    st.set_page_config(page_title="Family Flight Finder", layout="centered")
    st.title("✈️ Family Flight Finder (Flights Sky API)")

    # 1) Origin selection (fixed list)
    origin_map = {
        "Detroit (DTW)": "DTW",
        "Windsor (YQG)": "YQG",
        "Toronto (YYZ)": "YYZ"
    }
    origin_label = st.selectbox("Select Departure Airport", list(origin_map.keys()))
    origin_code  = origin_map[origin_label]

    # 2) Destination input (free-text, resolved via auto-complete)
    dest_input = st.text_input("Enter Destination (city or IATA code)", "LAX")

    # 3) Trip type toggle
    trip_type = st.radio("Trip Type", ["One-way", "Round-trip"])

    # 4) Dates + trip length
    earliest = date.today() + timedelta(days=1)
    depart_date = st.date_input("Departure Date", earliest)
    if trip_type == "Round-trip":
        trip_length = st.slider("Trip Length (days)", min_value=1, max_value=30, value=7)
        return_date = depart_date + timedelta(days=trip_length)
        st.caption(f"🔁 Return Date: {return_date.strftime('%Y-%m-%d')}")
    else:
        return_date = None

    # 5) Passenger counts
    adults   = st.slider("Adults",   min_value=1, max_value=6, value=2)
    children = st.slider("Children", min_value=0, max_value=4, value=1)

    # 6) Price filters
    min_price = st.number_input("Minimum Price ($)", min_value=0, value=0, step=50)
    max_price = st.number_input("Maximum Price ($)", min_value=0, value=1500, step=50)

    # Search button
    if st.button("🔍 Search Flights"):
        # Resolve destination to placeId
        st.info("Resolving destination…")
        dest_code = get_place_id(dest_input.strip())
        if not dest_code:
            st.error("🚫 Could not resolve destination. Try a different city or code.")
            return

        # Perform search + polling
        st.info("Searching for flights…")
        results, error = search_flights(
            trip_type,
            origin_code,
            dest_code,
            depart_date,
            return_date,
            adults,
            children,
            min_price,
            max_price
        )

        if error:
            st.error(error)
            return

        if not results:
            st.warning("No flights found for those parameters.")
            return

        # Display results
        st.success(f"Found {len(results)} flights!")
        for idx, r in enumerate(results, 1):
            # You can customize these fields based on what 'r' actually contains
            price = r.get("price", {}).get("raw", r.get("price", "N/A"))
            origin_iata = r.get("placeFrom", {}).get("code", origin_code)
            dest_iata   = r.get("placeTo",   {}).get("code", dest_code)
            st.markdown(f"### {idx}. {origin_iata} → {dest_iata} — **${price}**")
            st.json(r)  # dump full object for now; you can refine this layout

if __name__ == "__main__":
    main()

