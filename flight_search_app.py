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

# ─── Airports Organized by Region → Country → IATA Codes ───────────────────────
REGION_AIRPORTS = {
    "North America": {
        "United States": ["LAX","JFK","ORD","ATL","DFW","MIA","SEA","SFO","DTW","DEN"],
        "Canada":        ["YYZ","YVR","YUL","YOW","YWG"],
        "Mexico":        ["MEX","CUN","GDL","MTY"]
    },
    "Central America": {
        "Panama":       ["PTY"],
        "El Salvador":  ["SAL"],
        "Guatemala":    ["GUA"],
        "Costa Rica":   ["SJO"]
    },
    "South America": {
        "Brazil":       ["GRU","GIG","BSB"],
        "Argentina":    ["EZE","AEP"],
        "Chile":        ["SCL"],
        "Colombia":     ["BOG"],
        "Peru":         ["LIM"]
    },
    "Europe": {
        "United Kingdom": ["LHR","LGW","MAN"],
        "France":         ["CDG","ORY"],
        "Germany":        ["FRA","MUC"],
        "Spain":          ["MAD","BCN"],
        "Netherlands":    ["AMS"],
        "Italy":          ["FCO","MXP"]
    },
    "Asia": {
        "China":          ["PEK","PVG","CAN"],
        "Japan":          ["NRT","KIX"],
        "Singapore":      ["SIN"],
        "Thailand":       ["BKK"],
        "UAE":            ["DXB","AUH"]
    },
    "Oceania": {
        "Australia":      ["SYD","MEL","BNE","PER"],
        "New Zealand":    ["AKL","WLG"]
    },
    "Africa": {
        "South Africa":   ["JNB","CPT"],
        "Egypt":          ["CAI"],
        "Morocco":        ["CMN"]
    },
    "Middle East": {
        "Qatar":          ["DOH"],
        "Saudi Arabia":   ["JED","RUH"],
        "Israel":         ["TLV"]
    }
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
    endpoint = "search-one-way" if trip_type=="One-way" else "search-roundtrip"
    url = f"{BASE_URL}/{endpoint}"
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
    # Return the single cheapest result
    return min(results, key=lambda x: x.get("price",{}).get("raw", float('inf')))

def build_row(origin, result):
    legs = result.get("legs", [])
    # To: full name + code
    if legs:
        dest_info = legs[-1]["destination"]
        to = f"{dest_info.get('name','')} ({dest_info.get('displayCode','')})"
    else:
        to = ""
    # Depart / Arrive
    if legs:
        dep = fmt_dt(legs[0]["departure"])
        arr = fmt_dt(legs[-1]["arrival"])
    else:
        dep = arr = ""
    # Layovers
    layovers = []
    for i in range(len(legs)-1):
        stop = legs[i]["destination"]
        airport_name = stop.get("name","")
        code         = stop.get("displayCode","")
        arr_t = datetime.fromisoformat(legs[i]["arrival"])
        dep_t = datetime.fromisoformat(legs[i+1]["departure"])
        delta = dep_t - arr_t
        hrs, rem = divmod(delta.seconds,3600)
        mins = rem//60
        layovers.append(f"{airport_name} ({code}) – {hrs}h{mins:02d}m")
    stops_str = f"{len(layovers)} stop(s)" + (": " + "; ".join(layovers) if layovers else "")
    # Airline
    mk = legs[0].get("carriers",{}).get("marketing",[]) if legs else []
    airline = mk[0].get("name","") if mk else ""
    # Flight #
    fnums = [seg.get("flightNumber","") for seg in legs]
    flights = ", ".join([f for f in fnums if f])
    # Price
    price = result.get("price",{}).get("raw", None)

    return {
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
    st.title("✈️ Family Flight Finder (by Region & Country)")

    # 1) Departure
    origin_map = {"Detroit (DTW)": "DTW", "Windsor (YQG)": "YQG", "Toronto (YYZ)": "YYZ"}
    origin_lbl = st.selectbox("Departure Airport", list(origin_map.keys()))
    origin     = origin_map[origin_lbl]

    # 2) Region
    region = st.selectbox("Destination Region", ALL_REGIONS)

    # 3) Country multi-select (based on chosen region)
    available_countries = list(REGION_AIRPORTS[region].keys())
    selected_countries  = st.multiselect("Destination Country(ies)", available_countries, default=available_countries)

    # 4) Trip Type
    trip_type = st.radio("Trip Type", ["One-way", "Round-trip"], horizontal=True)

    # 5) Dates
    tomorrow    = date.today() + timedelta(days=1)
    depart_date = st.date_input("Departure Date", tomorrow)
    if trip_type=="Round-trip":
        length     = st.slider("Trip Length (days)", 1, 30, 7)
        return_date= depart_date + timedelta(days=length)
        st.caption(f"🔁 Return Date: {return_date.strftime('%B %-d, %Y')}")
    else:
        return_date = None

    # 6) Passengers
    adults   = st.slider("Adults", 1, 6, 2)
    children = st.slider("Children", 0, 4, 1)

    # 7) Price filters
    min_text = st.text_input("Min Price ($), blank=any", "")
    max_text = st.text_input("Max Price ($), blank=any", "")
    try:
        min_price = int(min_text) if min_text.strip() else None
        max_price = int(max_text) if max_text.strip() else None
    except ValueError:
        st.error("Price must be numeric or blank")
        return

    # 8) Search
    if st.button("🔍 Search by Region & Country"):
        st.info(f"Scanning airports in {region} → {selected_countries}…")
        rows = []
        for country in selected_countries:
            airports = REGION_AIRPORTS[region][country]
            for dest in airports:
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
        st.write(f"### Top 10 cheapest flights to {region} ({', '.join(selected_countries)})")
        st.dataframe(df.reset_index(drop=True), use_container_width=True)

if __name__=="__main__":
    main()






