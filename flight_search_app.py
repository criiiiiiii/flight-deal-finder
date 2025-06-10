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

# ─── FULL AIRPORT LISTS BY REGION ──────────────────────────────────────────────
REGION_AIRPORTS = {
    "North America": [
        "ATL","PEK","LAX","ORD","DFW","DEN","JFK","SFO","LAS","CLT",
        "MCO","EWR","PHX","IAH","SEA","MIA","MSP","BOS","DTW","PHL",
        "LGA","FLL","BWI","SLC","DCA","HOU","SAN","TPA","PDX","STL",
        # add more IATA codes as needed…
    ],
    "Central America": [
        "PTY","SAL","GUA","SJO","BZE","SAP","LIR","PTY","SJO","GUA"
    ],
    "South America": [
        "GRU","EZE","SCL","BOG","LIM","GIG","MVD","CWB","SBE","GYN",
        "REC","FOR","BEL","POA","BRC","CLO","CIX","LIM","EZE","SCL"
    ],
    "Europe": [
        "LHR","CDG","AMS","FRA","IST","MAD","BCN","MUC","HEL","DME",
        "FCO","LGW","ZRH","VIE","ARN","CPH","SVO","LED","ATH","BRU"
    ],
    "Asia": [
        "PEK","PVG","DXB","HKG","DEL","ICN","BKK","SIN","NRT","KUL",
        "CAN","DEN","CGK","MNL","TPE","SHA","SHJ","BOM","SYD","AKL"
    ],
    "Oceania": [
        "SYD","MEL","AKL","BNE","PER","CNS","OOL","WLG","CHC","ADL"
    ],
    "Africa": [
        "JNB","CAI","CMN","NBO","ACC","LOS","DUR","DRG","KRT","ADD"
    ],
    "Middle East": [
        "DXB","DOH","JED","RUH","IST","AMM","BEY","TLV","MCT","KWI"
    ]
}
ALL_REGIONS = list(REGION_AIRPORTS.keys())

# ─── Helper Functions ─────────────────────────────────────────────────────────

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
    data    = r.json().get("data",{})
    itins   = data.get("itineraries",{})
    results = itins.get("results",[])
    if not results:
        return None
    # cheapest by raw price
    return min(results, key=lambda x: x.get("price",{}).get("raw", float('inf')))

def build_row(origin, result):
    legs = result.get("legs", [])
    frm = legs[0]["origin"]["displayCode"]        if legs else ""
    to  = legs[-1]["destination"]["displayCode"]   if legs else ""
    dep_iso = legs[0].get("departure")             if legs else None
    arr_iso = legs[-1].get("arrival")              if legs else None
    dep = fmt_dt(dep_iso) if dep_iso else ""
    arr = fmt_dt(arr_iso) if arr_iso else ""
    # layovers
    layovers = []
    for i in range(len(legs) - 1):
        airport = legs[i]["destination"]["displayCode"]
        arr_t   = datetime.fromisoformat(legs[i]["arrival"])
        dep_t   = datetime.fromisoformat(legs[i+1]["departure"])
        delta   = dep_t - arr_t
        hrs, rem = divmod(delta.seconds, 3600)
        mins = rem // 60
        layovers.append(f"{airport} ({hrs}h{mins:02d}m)")
    stops_str = f"{len(legs)-1}" + (": " + ", ".join(layovers) if layovers else "")
    # airline & flight #
    mk = legs[0].get("carriers",{}).get("marketing",[]) if legs else []
    airline = mk[0].get("name","") if mk else ""
    fnums   = [seg.get("flightNumber","") for seg in legs]
    flights = ", ".join([f for f in fnums if f])
    price   = result.get("price",{}).get("raw",None)
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
    st.set_page_config(page_title="Family Flight Finder", layout="wide")
    st.title("✈️ Family Flight Finder (by Region & Cost)")

    # Departure airport
    origin_map = {
        "Detroit (DTW)": "DTW",
        "Windsor (YQG)": "YQG",
        "Toronto (YYZ)": "YYZ"
    }
    origin_lbl = st.selectbox("Departure Airport", list(origin_map.keys()))
    origin     = origin_map[origin_lbl]

    # Region
    region = st.selectbox("Destination Region", ALL_REGIONS)

    # Trip type
    trip_type = st.radio("Trip Type", ["One-way", "Round-trip"], horizontal=True)

    # Dates
    tomorrow    = date.today() + timedelta(days=1)
    depart_date = st.date_input("Departure Date", tomorrow)
    if trip_type=="Round-trip":
        length     = st.slider("Trip Length (days)", 1, 30, 7)
        return_date= depart_date + timedelta(days=length)
        st.caption(f"🔁 Return Date: {return_date.strftime('%B %-d, %Y')}")
    else:
        return_date = None

    # Passengers
    adults   = st.slider("Adults", 1, 6, 2)
    children = st.slider("Children", 0, 4, 1)

    # Price filters
    min_text = st.text_input("Min Price ($)", "")
    max_text = st.text_input("Max Price ($)", "")
    try:
        min_price = int(min_text) if min_text.strip() else None
        max_price = int(max_text) if max_text.strip() else None
    except ValueError:
        st.error("Price must be a number or left blank")
        return

    if st.button("🔍 Search by Region"):
        st.info(f"Scanning airports in {region}…")
        rows=[]
        for dest in REGION_AIRPORTS[region]:
            res = search_cheapest(
                trip_type, origin, dest,
                depart_date, return_date,
                adults, children,
                min_price, max_price
            )
            if res:
                rows.append(build_row(origin, res))

        if not rows:
            st.warning("No flights found for that region/filters.")
            return

        df = pd.DataFrame(rows).sort_values("Price (USD)").head(10)
        st.write(f"### Top 10 cheapest flights to {region}")
        st.dataframe(df.reset_index(drop=True), use_container_width=True)

if __name__=="__main__":
    main()







