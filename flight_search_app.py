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
    "North America": [
        "LAX","JFK","ORD","ATL","DFW","MIA","SEA","SFO","YYZ","YVR"
    ],
    "Central America": [
        "PTY","SAL","GUA","SJO"
    ],
    "South America": [
        "GRU","EZE","SCL","BOG","LIM"
    ],
    "Europe": [
        "LHR","CDG","FRA","AMS","MAD","BCN","ZRH","MUC","FCO","IST"
    ],
    "Asia": [
        "HKG","BKK","SIN","NRT","PVG","ICN","DEL","DXB","KUL","MNL"
    ],
    "Oceania": [
        "SYD","MEL","AKL","BNE","PER"
    ],
    "Africa": [
        "JNB","CAI","CMN","NBO","ACC"
    ],
    "Middle East": [
        "DXB","DOH","JED","RUH","IST"
    ]
}

ALL_REGIONS = list(REGION_AIRPORTS.keys())

# ─── Helpers ─────────────────────────────────────────────────────────────────

def fmt_dt(iso: str) -> str:
    dt = datetime.fromisoformat(iso)
    return dt.strftime("%A, (%B %-d) %I:%M %p")

def search_cheapest(
    trip_type, origin, dest, depart, rtn,
    adults, children, pmin, pmax
):
    """
    Search flights to a single dest; return the cheapest result dict or None.
    """
    ep   = "search-one-way" if trip_type=="One-way" else "search-roundtrip"
    url  = f"{BASE_URL}/{ep}"
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
    if pmin>0: params["minPrice"] = str(pmin)
    if pmax>0: params["maxPrice"] = str(pmax)

    r = requests.get(url, headers=HEADERS, params=params)
    if r.status_code!=200:
        return None
    data    = r.json().get("data",{})
    itins   = data.get("itineraries",{})
    results = itins.get("results",[])
    if not results:
        return None
    # pick cheapest by price.raw
    cheapest = min(results, key=lambda x: x.get("price",{}).get("raw", float('inf')))
    return cheapest

def build_row(origin, result):
    """
    Given a result dict, extract a single summary row.
    """
    legs = result.get("legs", [])
    frm  = legs[0]["origin"]["displayCode"]   if legs else ""
    to   = legs[-1]["destination"]["displayCode"] if legs else ""
    dep  = fmt_dt( legs[0].get("departure") )  if legs else ""
    arr  = fmt_dt( legs[-1].get("arrival") )   if legs else ""
    stops= max(len(legs)-1,0)
    mk   = legs[0].get("carriers",{}).get("marketing",[]) if legs else []
    airline = mk[0].get("name","") if mk else ""
    price   = result.get("price",{}).get("raw", None)
    fnums   = [seg.get("flightNumber","") for seg in legs]
    flights = ", ".join([f for f in fnums if f])
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

    # 1) Departure
    origin_map = {"Detroit (DTW)":"DTW","Windsor (YQG)":"YQG","Toronto (YYZ)":"YYZ"}
    origin_lbl = st.selectbox("Departure Airport", list(origin_map.keys()))
    origin     = origin_map[origin_lbl]

    # 2) Region selector (replaces destination input)
    region = st.selectbox("Select Destination Region", ALL_REGIONS)

    # 3) Trip type
    trip_type = st.radio("Trip Type", ["One-way","Round-trip"], horizontal=True)

    # 4) Dates
    tomorrow    = date.today() + timedelta(days=1)
    depart_date = st.date_input("Departure Date", tomorrow)
    if trip_type=="Round-trip":
        length     = st.slider("Trip Length (days)",1,30,7)
        return_date= depart_date + timedelta(days=length)
        st.caption(f"🔁 Return Date: {return_date.strftime('%B %-d, %Y')}")
    else:
        return_date = None

    # 5) Passengers
    adults   = st.slider("Adults",1,6,2)
    children = st.slider("Children",0,4,1)

    # 6) Price filters
    min_price = st.number_input("Min Price ($)",0,10000,0,step=50)
    max_price = st.number_input("Max Price ($)",0,10000,1500,step=50)

    if st.button("🔍 Search by Region"):
        st.info(f"Searching top airports in {region}…")
        rows = []
        for dest in REGION_AIRPORTS[region]:
            cheapest = search_cheapest(
                trip_type, origin, dest,
                depart_date, return_date,
                adults, children,
                min_price, max_price
            )
            if cheapest:
                rows.append(build_row(origin, cheapest))

        if not rows:
            st.warning("No flights found in that region with those filters.")
            return

        df = pd.DataFrame(rows).sort_values("Price (USD)").head(10)
        st.write(f"### Top 10 cheapest flights to {region}")
        st.dataframe(df.reset_index(drop=True), use_container_width=True)

if __name__=="__main__":
    main()





