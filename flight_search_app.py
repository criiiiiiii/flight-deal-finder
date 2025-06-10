import streamlit as st
import requests
from datetime import date, datetime, timedelta
import pandas as pd

# ─── Configuration ────────────────────────────────────────────────────────────
API_KEY  = "215a6826f2mshc7e99c81ebbe6e0p129a86jsn13e40defdfae"
API_HOST = "flights-sky.p.rapidapi.com"
BASE_URL = f"https://{API_HOST}/web/flights"
HEADERS  = {
    "x-rapidapi-host": API_HOST,
    "x-rapidapi-key":  API_KEY
}

# Static region → top airports mapping
REGION_AIRPORTS = {
    "North America": ["LAX","JFK","ORD","ATL","DFW","MIA","SEA","SFO","YYZ","YVR"],
    "Central America": ["PTY","SAL","GUA","SJO"],
    "South America": ["GRU","EZE","SCL","BOG","LIM"],
    "Europe": ["LHR","CDG","FRA","AMS","MAD","BCN","ZRH","MUC","FCO","IST"],
    "Asia": ["HKG","BKK","SIN","NRT","PVG","ICN","DEL","DXB","KUL","MNL"],
    "Oceania": ["SYD","MEL","AKL","BNE","PER"],
    "Africa": ["JNB","CAI","CMN","NBO","ACC"],
    "Middle East": ["DXB","DOH","JED","RUH","IST"]
}
ALL_REGIONS = list(REGION_AIRPORTS.keys())

# ─── Helpers ─────────────────────────────────────────────────────────────────

def fmt_dt(iso: str) -> str:
    dt = datetime.fromisoformat(iso)
    return dt.strftime("%A, (%B %-d) %I:%M %p")

def search_cheapest(
    trip_type, origin, dest, depart, rtn,
    adults, children, min_price, max_price
):
    ep = "search-one-way" if trip_type=="One-way" else "search-roundtrip"
    url = f"{BASE_URL}/{ep}"
    params = {
        "placeIdFrom": origin,
        "placeIdTo":   dest,
        "departDate":  depart.strftime("%Y-%m-%d"),
        "adults":      str(adults),
        "children":    str(children),
        "currency":    "USD"
    }
    if trip_type=="Round-trip":
        params["returnDate"] = rtn.strftime("%Y-%m-%d")
    if min_price is not None:
        params["minPrice"] = str(min_price)
    if max_price is not None:
        params["maxPrice"] = str(max_price)

    r = requests.get(url, headers=HEADERS, params=params)
    if r.status_code != 200:
        return None
    data    = r.json().get("data", {})
    itins   = data.get("itineraries", {})
    results = itins.get("results", [])
    if not results:
        return None
    return min(results, key=lambda x: x.get("price", {}).get("raw", float('inf')))

def build_row(origin, result):
    legs = result.get("legs", [])
    frm    = legs[0]["origin"]["displayCode"]    if legs else ""
    to     = legs[-1]["destination"]["displayCode"] if legs else ""
    dep    = fmt_dt(legs[0]["departure"])        if legs else ""
    arr    = fmt_dt(legs[-1]["arrival"])         if legs else ""
    stops  = max(len(legs)-1, 0)
    mkt    = legs[0].get("carriers", {}).get("marketing", []) if legs else []
    airline= mkt[0].get("name","")                if mkt else ""
    price  = result.get("price", {}).get("raw", None)
    fnums  = [seg.get("flightNumber","") for seg in legs]
    flights= ", ".join([f for f in fnums if f])
    return {
        "From":        frm,
        "To":          to,
        "Depart":      dep,
        "Arrive":      arr,
        "Stops":       stops,
        "Airline":     airline,
        "Flight #":    flights,
        "Price (USD)": price
    }

# ─── Streamlit App ───────────────────────────────────────────────────────────

def main():
    st.set_page_config(page_title="Family Flight Finder", layout="wide")
    st.title("✈️ Family Flight Finder (by Region & Cost)")

    # 1) Departure Airport
    origin_map = {"Detroit (DTW)": "DTW", "Windsor (YQG)": "YQG", "Toronto (YYZ)": "YYZ"}
    origin_lbl = st.selectbox("Departure Airport", list(origin_map.keys()))
    origin     = origin_map[origin_lbl]

    # 2) Region selector
    region = st.selectbox("Destination Region", ALL_REGIONS)

    # 3) Trip type
    trip_type = st.radio("Trip Type", ["One-way", "Round-trip"], horizontal=True)

    # 4) Dates
    tomorrow    = date.today() + timedelta(days=1)
    depart_date = st.date_input("Departure Date", tomorrow)
    if trip_type=="Round-trip":
        length     = st.slider("Trip Length (days)", 1, 30, 7)
        return_date= depart_date + timedelta(days=length)
        st.caption(f"🔁 Return Date: {return_date.strftime('%B %-d, %Y')}")
    else:
        return_date = None

    # 5) Passengers
    adults   = st.slider("Adults", 1, 6, 2)
    children = st.slider("Children", 0, 4, 1)

    # 6) Price fields (optional; blank = any)
    min_text = st.text_input("Min Price ($) – leave blank for no minimum", "")
    max_text = st.text_input("Max Price ($) – leave blank for no maximum", "")
    try:
        min_price = int(min_text) if min_text.strip() else None
    except ValueError:
        st.error("Min Price must be a number or blank")
        return
    try:
        max_price = int(max_text) if max_text.strip() else None
    except ValueError:
        st.error("Max Price must be a number or blank")
        return

    # 7) Search
    if st.button("🔍 Search by Region"):
        st.info(f"Searching top airports in {region}…")
        rows = []
        for dest in REGION_AIRPORTS[region]:
            result = search_cheapest(
                trip_type, origin, dest,
                depart_date, return_date,
                adults, children,
                min_price, max_price
            )
            if result:
                rows.append(build_row(origin, result))

        if not rows:
            st.warning("No flights found in that region with those filters.")
            return

        df = pd.DataFrame(rows).sort_values("Price (USD)").head(10)
        st.write(f"### Top 10 cheapest flights to {region}")
        st.dataframe(df.reset_index(drop=True), use_container_width=True)

if __name__ == "__main__":
    main()





