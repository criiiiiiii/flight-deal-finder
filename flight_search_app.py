import streamlit as st
import requests
from datetime import date, datetime, timedelta
import pandas as pd

# ─── Configuration ────────────────────────────────────────────────────────────
API_KEY  = "215a6826f2mshc7e99c81ebbe6e0p129a86jsn13e40defdfae"
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
    if min_price>0:
        params["minPrice"] = str(min_price)
    if max_price>0:
        params["maxPrice"] = str(max_price)

    r = requests.get(url, headers=HEADERS, params=params)
    if r.status_code != 200:
        return None, f"Search failed: {r.status_code} {r.text}"

    data    = r.json().get("data", {})
    itins   = data.get("itineraries", {})
    results = itins.get("results", [])
    return results, None

def format_datetime_iso(dt_iso: str) -> str:
    """
    Converts an ISO timestamp into:
      Monday, (June 9) 07:00 AM
    """
    dt = datetime.fromisoformat(dt_iso)
    # %-d is day without leading zero on Linux
    return dt.strftime("%A, (%B %-d) %I:%M %p")

def format_results(results):
    rows = []
    for r in results:
        legs = r.get("legs", [])
        # From/To
        frm = legs[0]["origin"].get("displayCode","")    if legs else ""
        to  = legs[-1]["destination"].get("displayCode","") if legs else ""
        # Departure/Arrival formatting
        departure_iso = legs[0].get("departure") if legs else None
        arrival_iso   = legs[-1].get("arrival") if legs else None
        departure = format_datetime_iso(departure_iso) if departure_iso else ""
        arrival   = format_datetime_iso(arrival_iso)   if arrival_iso   else ""
        # Stops
        stops = max(len(legs)-1, 0)
        # Airline
        marketing = legs[0].get("carriers",{}).get("marketing",[]) if legs else []
        airline   = marketing[0].get("name","") if marketing else ""
        # Price
        price = r.get("price",{}).get("raw", None)

        rows.append({
            "From":        frm,
            "To":          to,
            "Depart":      departure,
            "Arrive":      arrival,
            "Stops":       stops,
            "Airline":     airline,
            "Price (USD)": price
        })

    df = pd.DataFrame(rows)
    df = df.sort_values("Price (USD)")
    return df

# ─── Streamlit App ───────────────────────────────────────────────────────────

def main():
    st.set_page_config(page_title="Family Flight Finder", layout="wide")
    st.title("✈️ Family Flight Finder (Flights Sky API)")

    # Departure Airport
    origin_map = {
        "Detroit (DTW)": "DTW",
        "Windsor (YQG)": "YQG",
        "Toronto (YYZ)": "YYZ"
    }
    origin_lbl = st.selectbox("Select Departure Airport", list(origin_map.keys()))
    origin     = origin_map[origin_lbl]

    # Destination
    dest_input = st.text_input("Destination (city or IATA code)", "LAX").strip()

    # Trip Type
    trip_type = st.radio("Trip Type", ["One-way", "Round-trip"], horizontal=True)

    # Dates
    tomorrow    = date.today() + timedelta(days=1)
    depart_date = st.date_input("Departure Date", tomorrow)
    if trip_type=="Round-trip":
        length      = st.slider("Trip Length (days)", 1, 30, 7)
        return_date = depart_date + timedelta(days=length)
        st.caption(f"🔁 Return Date: {return_date.strftime('%B %-d, %Y')}")
    else:
        return_date = None

    # Passengers
    adults   = st.slider("Adults",   1, 6, 2)
    children = st.slider("Children", 0, 4, 1)

    # Price Filters
    min_price = st.number_input("Min Price ($)", 0, 10000, 0, step=50)
    max_price = st.number_input("Max Price ($)", 0, 10000, 1500, step=50)

    if st.button("🔍 Search Flights"):
        # Resolve destination
        if len(dest_input)==3 and dest_input.isalpha():
            dest_code = dest_input.upper()
        else:
            st.info("Resolving destination…")
            dest_code = get_place_id(dest_input)
        if not dest_code:
            st.error("🚫 Could not resolve destination.")
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

        df = format_results(results)
        st.write(f"### Found {df.shape[0]} options")
        st.dataframe(df.reset_index(drop=True), use_container_width=True)

if __name__=="__main__":
    main()


