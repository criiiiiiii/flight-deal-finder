import streamlit as st
import requests
import json
from datetime import date, datetime, timedelta
import pandas as pd
import os

# ─── Configuration ────────────────────────────────────────────────────────────
API_KEY  = "215a6826f2mshc7e99c81ebbe6e0p129a86jsn13e40defdfae"
API_HOST = "flights-sky.p.rapidapi.com"
BASE_URL = f"https://{API_HOST}/web/flights"
HEADERS  = {
    "x-rapidapi-host": API_HOST,
    "x-rapidapi-key":  API_KEY
}

# ─── Load region_airports.json ────────────────────────────────────────────────
REGION_FILE = "region_airports.json"
if os.path.exists(REGION_FILE):
    with open(REGION_FILE, "r") as f:
        REGION_AIRPORTS = json.load(f)
else:
    st.error(f"Missing {REGION_FILE} — please add it to your repo with your full lists.")
    st.stop()
ALL_REGIONS = list(REGION_AIRPORTS.keys())

# ─── Helpers ─────────────────────────────────────────────────────────────────

def fmt_dt(iso: str) -> str:
    dt = datetime.fromisoformat(iso)
    return dt.strftime("%A, (%B %-d) %I:%M %p")

def search_cheapest(trip, origin, dest, depart, rtn, adults, kids, pmin, pmax):
    ep = "search-one-way" if trip=="One-way" else "search-roundtrip"
    url = f"{BASE_URL}/{ep}"
    params = {
        "placeIdFrom": origin,
        "placeIdTo":   dest,
        "departDate":  depart.strftime("%Y-%m-%d"),
        "adults":      str(adults),
        "children":    str(kids),
        "currency":    "USD"
    }
    if trip=="Round-trip":
        params["returnDate"] = rtn.strftime("%Y-%m-%d")
    if pmin is not None: params["minPrice"] = str(pmin)
    if pmax is not None: params["maxPrice"] = str(pmax)

    r = requests.get(url, headers=HEADERS, params=params)
    if r.status_code != 200:
        return None
    data    = r.json().get("data",{})
    itins   = data.get("itineraries",{})
    results = itins.get("results",[])
    if not results:
        return None
    return min(results, key=lambda x: x.get("price",{}).get("raw", float("inf")))

def build_row(origin, result):
    legs = result.get("legs", [])
    frm = legs[0]["origin"]["displayCode"] if legs else ""
    to  = legs[-1]["destination"]["displayCode"] if legs else ""
    dep = fmt_dt(legs[0]["departure"])   if legs else ""
    arr = fmt_dt(legs[-1]["arrival"])     if legs else ""
    stops = max(len(legs)-1,0)
    layovers = []
    for i in range(len(legs)-1):
        airport = legs[i]["destination"]["displayCode"]
        arr_t   = datetime.fromisoformat(legs[i]["arrival"])
        dep_t   = datetime.fromisoformat(legs[i+1]["departure"])
        delta   = dep_t - arr_t
        hrs, rem = divmod(delta.seconds,3600)
        mins = rem//60
        layovers.append(f"{airport} ({hrs}h{mins:02d}m)")
    stops_str = f"{stops}" + (": " + ", ".join(layovers) if layovers else "")

    mk  = legs[0].get("carriers",{}).get("marketing",[]) if legs else []
    airline = mk[0].get("name","") if mk else ""
    price   = result.get("price",{}).get("raw",None)
    fnums   = [seg.get("flightNumber","") for seg in legs]
    flights = ", ".join([f for f in fnums if f])

    return {
        "From":        frm,
        "To":          to,
        "Depart":      dep,
        "Arrive":      arr,
        "Stops":       stops_str,
        "Airline":     airline,
        "Flight #":    flights,
        "Price (USD)": price
    }

# ─── Streamlit App ───────────────────────────────────────────────────────────

def main():
    st.set_page_config(page_title="Flight Finder by Region", layout="wide")
    st.title("✈️ Family Flight Finder (by Region & Cost)")

    # Departure Airport
    origin_map = {
        "Detroit (DTW)": "DTW",
        "Windsor (YQG)": "YQG",
        "Toronto (YYZ)": "YYZ"
    }
    origin_lbl = st.selectbox("Departure Airport", list(origin_map.keys()))
    origin     = origin_map[origin_lbl]

    # Region selector (full list from JSON)
    region = st.selectbox("Destination Region", ALL_REGIONS)

    # Trip Type
    trip_type = st.radio("Trip Type", ["One-way","Round-trip"], horizontal=True)

    # Dates
    tomorrow    = date.today() + timedelta(days=1)
    depart_date = st.date_input("Departure Date", tomorrow)
    if trip_type=="Round-trip":
        length     = st.slider("Trip Length (days)",1,30,7)
        return_date= depart_date + timedelta(days=length)
        st.caption(f"🔁 Return Date: {return_date}")
    else:
        return_date = None

    # Passengers
    adults   = st.slider("Adults",1,6,2)
    children = st.slider("Children",0,4,1)

    # Price filters (blank = any)
    min_text = st.text_input("Min Price ($)", "")
    max_text = st.text_input("Max Price ($)", "")
    try:
        min_price = int(min_text) if min_text.strip() else None
        max_price = int(max_text) if max_text.strip() else None
    except ValueError:
        st.error("Price must be numeric or blank")
        return

    if st.button("🔍 Search by Region"):
        st.info(f"Scanning airports in {region}…")
        rows=[]
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
            st.warning("No flights found.")
            return

        df = pd.DataFrame(rows).sort_values("Price (USD)").head(10)
        st.write(f"### Top 10 cheapest flights to {region}")
        st.dataframe(df.reset_index(drop=True), use_container_width=True)

if __name__=="__main__":
    main()






