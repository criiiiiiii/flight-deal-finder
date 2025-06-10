import streamlit as st
import requests
from datetime import date, timedelta
import pandas as pd

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
    url = f"{BASE_URL}/auto-complete"
    params = {"q": query}
    r = requests.get(url, headers=HEADERS, params=params)
    if r.status_code == 200:
        items = r.json().get("data", [])
        if items:
            return items[0].get("placeId")
    return None

def search_flights(
    trip_type, place_from, place_to,
    depart_date, return_date,
    adults, children, min_price, max_price
):
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
    if min_price > 0:
        params["minPrice"] = str(min_price)
    if max_price > 0:
        params["maxPrice"] = str(max_price)

    r = requests.get(url, headers=HEADERS, params=params)
    if r.status_code != 200:
        return None, f"Search failed: {r.status_code} {r.text}"

    data        = r.json().get("data", {})
    itins       = data.get("itineraries", {})
    results     = itins.get("results", [])
    return results, None

def format_results(results):
    """
    Transform raw JSON results into a pandas DataFrame with
    the columns we care about.
    """
    rows = []
    for r in results:
        # price
        price = r.get("price",{}).get("raw", None)
        # route codes
        frm = r.get("placeFrom",{}).get("code")
        to  = r.get("placeTo",{}).get("code")
        # stops (legs)
        legs = r.get("legs", [])
        stops = len(legs) - 1
        # departure/arrival
        depart_times = [leg.get("departure") for leg in legs]
        arrive_times = [leg.get("arrival") for leg in legs]
        departure = depart_times[0] if depart_times else None
        arrival   = arrive_times[-1] if arrive_times else None
        # marketing carrier name (take first)
        carriers = legs[0].get("carriers",{}).get("marketing",[])
        airline  = carriers[0].get("name") if carriers else None

        rows.append({
            "From":        frm,
            "To":          to,
            "Departure":   departure.replace("T"," ") if departure else "",
            "Arrival":     arrival.replace("T"," ") if arrival else "",
            "Stops":       stops,
            "Airline":     airline,
            "Price (USD)": price
        })
    df = pd.DataFrame(rows)
    # sort by price
    df = df.sort_values("Price (USD)")
    return df

# ─── Streamlit App ───────────────────────────────────────────────────────────

def main():
    st.set_page_config(page_title="Family Flight Finder", layout="wide")
    st.title("✈️ Family Flight Finder (Flights Sky API)")

    # Origin
    origin_map = {"Detroit (DTW)":"DTW","Windsor (YQG)":"YQG","Toronto (YYZ)":"YYZ"}
    origin_lbl = st.selectbox("Departure Airport", list(origin_map.keys()))
    origin     = origin_map[origin_lbl]

    # Destination
    dest_input = st.text_input("Destination (city or IATA code)", "LAX").strip()

    # Trip type
    trip_type = st.radio("Trip Type", ["One-way","Round-trip"], horizontal=True)

    # Dates
    tomorrow    = date.today() + timedelta(days=1)
    depart_date = st.date_input("Departure Date", tomorrow)
    if trip_type=="Round-trip":
        length      = st.slider("Trip Length (days)", 1, 30, 7)
        return_date = depart_date + timedelta(days=length)
        st.caption(f"🔁 Return Date: {return_date}")
    else:
        return_date = None

    # Passengers
    adults   = st.slider("Adults",   1, 6, 2)
    children = st.slider("Children", 0, 4, 1)

    # Price filters
    min_price = st.number_input("Min Price ($)", 0, 10000, 0, step=50)
    max_price = st.number_input("Max Price ($)", 0, 10000, 1500, step=50)

    if st.button("🔍 Search Flights"):
        # Resolve dest
        if len(dest_input)==3 and dest_input.isalpha():
            dest_code = dest_input.upper()
        else:
            dest_code = get_place_id(dest_input)
        if not dest_code:
            st.error("🚫 Could not resolve destination. Try again.")
            return

        st.info("Searching…")
        results, err = search_flights(
            trip_type, origin, dest_code,
            depart_date, return_date,
            adults, children,
            min_price, max_price
        )
        if err:
            st.error(err); return
        if not results:
            st.warning("No flights found."); return

        # Format & display
        df = format_results(results)
        st.write("### Results", df.shape[0], "options found")
        st.dataframe(df.reset_index(drop=True))

if __name__=="__main__":
    main()


