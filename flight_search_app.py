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

# Map of country → region (extend as needed)
REGION_MAP = {
    "United States":      "North America",
    "Canada":             "North America",
    "Mexico":             "North America",
    "Guatemala":          "Central America",
    "Costa Rica":         "Central America",
    "Panama":             "Central America",
    "Brazil":             "South America",
    "Argentina":          "South America",
    "Chile":              "South America",
    "United Kingdom":     "Europe",
    "France":             "Europe",
    "Germany":            "Europe",
    "Italy":              "Europe",
    "Spain":              "Europe",
    "China":              "Asia",
    "Japan":              "Asia",
    "India":              "Asia",
    "Australia":          "Oceania",
    "New Zealand":        "Oceania",
    "South Africa":       "Africa",
    "Egypt":              "Africa",
    "Morocco":            "Africa",
    "United Arab Emirates":"Middle East",
    "Saudi Arabia":       "Middle East",
    "Qatar":              "Middle East"
}
# Static lists for filter controls
ALL_REGIONS  = sorted(set(REGION_MAP.values()))
ALL_COUNTRIES= sorted(REGION_MAP.keys())

# ─── Helpers ─────────────────────────────────────────────────────────────────

def get_place_id(q: str) -> str:
    r = requests.get(f"{BASE_URL}/auto-complete", headers=HEADERS, params={"q": q})
    if r.status_code==200:
        data = r.json().get("data", [])
        if data:
            return data[0].get("placeId")
    return None

def search_flights(trip, frm, to, depart, rtn, adults, kids, pmin, pmax):
    ep    = "search-one-way" if trip=="One-way" else "search-roundtrip"
    url   = f"{BASE_URL}/{ep}"
    params= {
        "placeIdFrom": frm,
        "placeIdTo":   to,
        "departDate":  depart.strftime("%Y-%m-%d"),
        "adults":      str(adults),
        "children":    str(kids),
        "currency":    "USD"
    }
    if trip=="Round-trip":
        params["returnDate"] = rtn.strftime("%Y-%m-%d")
    if pmin>0: params["minPrice"] = str(pmin)
    if pmax>0: params["maxPrice"] = str(pmax)

    r = requests.get(url, headers=HEADERS, params=params)
    if r.status_code!=200:
        return None, f"Search error {r.status_code}: {r.text}"

    data    = r.json().get("data",{})
    itins   = data.get("itineraries",{})
    return itins.get("results",[]), None

def fmt_dt(iso: str) -> str:
    dt = datetime.fromisoformat(iso)
    return dt.strftime("%A, (%B %-d) %I:%M %p")

def build_df(results):
    rows=[]
    for r in results:
        legs = r.get("legs", [])
        frm  = legs[0]["origin"]["displayCode"]  if legs else ""
        to   = legs[-1]["destination"]["displayCode"] if legs else ""
        dep  = fmt_dt(legs[0]["departure"]) if legs else ""
        arr  = fmt_dt(legs[-1]["arrival"])   if legs else ""
        stops= max(len(legs)-1, 0)
        mk   = legs[0].get("carriers",{}).get("marketing",[]) if legs else []
        airline = mk[0].get("name","") if mk else ""
        country = legs[-1]["destination"].get("country","") if legs else ""
        region  = REGION_MAP.get(country, "Other")
        fnums   = [seg.get("flightNumber","") for seg in legs]
        flights = ", ".join([f for f in fnums if f])
        price   = r.get("price",{}).get("raw", None)

        rows.append({
            "From":        frm,
            "To":          to,
            "Depart":      dep,
            "Arrive":      arr,
            "Stops":       stops,
            "Airline":     airline,
            "Country":     country,
            "Region":      region,
            "Flight #":    flights,
            "Price (USD)": price
        })

    df = pd.DataFrame(rows).sort_values("Price (USD)")
    return df

# ─── Streamlit App ───────────────────────────────────────────────────────────

def main():
    st.set_page_config(page_title="Family Flight Finder", layout="wide")
    st.title("✈️ Family Flight Finder (Flights Sky API)")

    # 1) Departure Airport
    origin_map = {"Detroit (DTW)":"DTW","Windsor (YQG)":"YQG","Toronto (YYZ)":"YYZ"}
    origin_lbl = st.selectbox("Departure Airport", list(origin_map.keys()))
    origin     = origin_map[origin_lbl]

    # 2) Destination
    dest_inp = st.text_input("Destination (city or IATA code)", "LAX").strip()

    # 3) Trip Type
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
    adults = st.slider("Adults",1,6,2)
    kids   = st.slider("Children",0,4,1)

    # 6) Price
    pmin = st.number_input("Min Price ($)",0,10000,0,step=50)
    pmax = st.number_input("Max Price ($)",0,10000,1500,step=50)

    # 7) Search
    if st.button("🔍 Search"):
        if len(dest_inp)==3 and dest_inp.isalpha():
            dest = dest_inp.upper()
        else:
            st.info("Resolving destination…")
            dest = get_place_id(dest_inp)
        if not dest:
            st.error("🚫 Could not resolve destination.")
            return

        st.info("Searching…")
        results, err = search_flights(
            trip_type, origin, dest,
            depart_date, return_date,
            adults, kids, pmin, pmax
        )
        if err:
            st.error(err); return
        if not results:
            st.warning("No flights found."); return

        df = build_df(results)

        # Sidebar filters
        st.sidebar.header("Refine Results")
        sel_air = st.sidebar.multiselect("Airline", sorted(df["Airline"].unique()))
        sel_reg = st.sidebar.multiselect("Region", ALL_REGIONS)
        sel_cty = st.sidebar.multiselect("Country", ALL_COUNTRIES)

        if sel_air:
            df = df[df["Airline"].isin(sel_air)]
        if sel_reg:
            df = df[df["Region"].isin(sel_reg)]
        if sel_cty:
            df = df[df["Country"].isin(sel_cty)]

        st.write(f"### {df.shape[0]} options found")
        st.dataframe(df.reset_index(drop=True), use_container_width=True)

if __name__=="__main__":
    main()




