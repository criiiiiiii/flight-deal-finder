import streamlit as st
import requests
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
    Hits /auto-complete to resolve a city/airport name into the API's placeId.
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
    Calls the one-way or round-trip search endpoint once,
    then returns the data->itineraries->results list directly.
    """
    endpoint = "search-one-way" if trip_type=="One-way" else "search-roundtrip"
    url = f"{BASE_URL}/{endpoint}"

    params = {
        "placeIdFrom": place_from,
        "placeIdTo":   place_to,
        "departDate":  depart_date.strftime("%Y-%m-%d"),
        "adults":      str(adults),
        "children":    str(children),
        "currency":    "USD"
    }
    if trip_type=="Round-trip":
        params["returnDate"] = return_date.strftime("%Y-%m-%d")
    if min_price>0:
        params["minPrice"] = str(min_price)
    if max_price>0:
        params["maxPrice"] = str(max_price)

    r = requests.get(url, headers=HEADERS, params=params)
    if r.status_code != 200:
        return None, f"Search failed: {r.status_code} {r.text}"

    # Drill into response
    resp_json   = r.json()
    data        = resp_json.get("data", resp_json)
    itineraries = data.get("itineraries", {})
    results     = itineraries.get("results", [])

    return results, None

# ─── Streamlit App ───────────────────────────────────────────────────────────

def main():
    st.set_page_config(page_title="Family Flight Finder", layout="centered")
    st.title("✈️ Family Flight Finder (Flights Sky API)")

    # 1) Departure airport (fixed list)
    origin_map = {
        "Detroit (DTW)": "DTW",
        "Windsor (YQG)": "YQG",
        "Toronto (YYZ)": "YYZ"
    }
    origin_label = st.selectbox("Select Departure Airport", list(origin_map.keys()))
    origin_code  = origin_map[origin_label]

    # 2) Destination (free text or IATA)
    dest_input = st.text_input("Enter Destination (city or IATA code)", "LAX").strip()

    # 3) Trip type
    trip_type = st.radio("Trip Type", ["One-way", "Round-trip"])

    # 4) Dates
    tomorrow    = date.today() + timedelta(days=1)
    depart_date = st.date_input("Departure Date", tomorrow)
    if trip_type=="Round-trip":
        length     = st.slider("Trip Length (days)", 1, 30, 7)
        return_date= depart_date + timedelta(days=length)
        st.caption(f"🔁 Return Date: {return_date}")
    else:
        return_date = None

    # 5) Passengers
    adults   = st.slider("Adults",   1, 6, 2)
    children = st.slider("Children", 0, 4, 1)

    # 6) Price filters
    min_price = st.number_input("Minimum Price ($)", 0, 10000, 0, step=50)
    max_price = st.number_input("Maximum Price ($)", 0, 10000, 1500, step=50)

    # 7) Search button
    if st.button("🔍 Search Flights"):
        # Resolve destination
        if len(dest_input)==3 and dest_input.isalpha():
            dest_code = dest_input.upper()
        else:
            st.info("Resolving destination…")
            dest_code = get_place_id(dest_input)
        if not dest_code:
            st.error("🚫 Could not resolve destination; try a city name or IATA code.")
            return

        st.info("Searching flights…")
        results, err = search_flights(
            trip_type, origin_code, dest_code,
            depart_date, return_date,
            adults, children,
            min_price, max_price
        )
        if err:
            st.error(err)
            return
        if not results:
            st.warning("No flights found.")
            return

        st.success(f"Found {len(results)} flights:")
        for i, r in enumerate(results, 1):
            price = r.get("price", {}).get("raw", r.get("price","N/A"))
            frm   = r.get("placeFrom",{}).get("code", origin_code)
            to    = r.get("placeTo",{}).get("code", dest_code)
            airline = r.get("airline",{}).get("name","Unknown")
            st.markdown(f"**{i}. {frm} → {to} — ${price}**\n\nAirline: {airline}")
            st.json(r)  # raw JSON dump for you to refine

if __name__=="__main__":
    main()

