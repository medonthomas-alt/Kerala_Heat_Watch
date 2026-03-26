import requests
import json
import os
from datetime import datetime

# ── SETTINGS ──────────────────────────────────────────────────────────────
# Kerala geographic boundary
# Any station inside this box is considered a Kerala station
KL_LAT_MIN = 8.0
KL_LAT_MAX = 13.0
KL_LON_MIN = 74.5
KL_LON_MAX = 77.6

# The three IMD data files we fetch
URLS = {
    "forecast":  "https://dss.imd.gov.in/dwr_img/GIS/CD_Status_Forecast.json",
    "observed":  "https://dss.imd.gov.in/dwr_img/GIS/Observed_Stations.json",
    "warnings":  "https://dss.imd.gov.in/dwr_img/GIS/HWCW_Status.json",
}

# Standard browser header so IMD server accepts our request
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer": "https://dss.imd.gov.in/dwr_img/GIS/heatwave.html",
}

# Official Kerala station names mapped to their IMD codes
# Source: IMD Station Directory
KERALA_STATION_NAMES = {
    "43352": "Alappuzha",
    "43315": "Kannur",
    "43253": "Kannur AMS",
    "43336": "Kochi (CIAL)",
    "43353": "Kochi (NAS)",
    "43355": "Kottayam",
    "43314": "Kozhikode",
    "43320": "Kozhikode (Airport)",
    "43335": "Palakkad",
    "43354": "Punalur",
    "43371": "Thiruvananthapuram",
    "43372": "Thiruvananthapuram (Airport)",
    "43357": "Thrissur (Vellanikara)",
    # Observed stations that fall inside Kerala
    "90061": "Thrissur (Vellanikara AWS)",
    "99461": "Kerala AWS 1",
    "94462": "Kerala AWS 2",
    "99528": "Kerala AWS 3",
    "30008": "Kerala AWS 4",
    "30010": "Kerala AWS 5",
}

# ── HELPER: fetch one JSON file ───────────────────────────────────────────
def fetch_json(url, label):
    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=30,
            verify=False  # IMD uses a non-standard SSL certificate
        )
        if response.status_code == 200:
            print(f"  ✅ {label} fetched successfully")
            return response.json()
        else:
            print(f"  ❌ {label} returned HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f"  ❌ {label} failed: {e}")
        return None

# ── HELPER: check if a station is inside Kerala ───────────────────────────
def is_kerala(lat, lon):
    if lat is None or lon is None:
        return False
    try:
        lat = float(lat)
        lon = float(lon)
        return KL_LAT_MIN <= lat <= KL_LAT_MAX and KL_LON_MIN <= lon <= KL_LON_MAX
    except:
        return False

# ── HELPER: get station name ──────────────────────────────────────────────
def get_name(stat_code, stat_name_from_data):
    code_str = str(stat_code)
    # Use our official name if we know it
    if code_str in KERALA_STATION_NAMES:
        return KERALA_STATION_NAMES[code_str]
    # Otherwise use the name from the data itself
    if stat_name_from_data:
        return stat_name_from_data
    return f"Station {code_str}"

# ── HELPER: extract one station's data from properties ───────────────────
def extract_station(props, source):
    stat_code = str(props.get("Stat_Code", ""))
    stat_name = props.get("Stat_Name", "")
    lat = props.get("Latitude")
    lon = props.get("Longitude")

    return {
        # Identity
        "stat_code":   stat_code,
        "name":        get_name(stat_code, stat_name),
        "lat":         lat,
        "lon":         lon,
        "source":      source,  # "forecast" or "observed"

        # Yesterday's actual observation
        "obs_max":     props.get("PD_Mx_Temp"),
        "obs_min":     props.get("D1_Mn_Temp"),
        "obs_dep":     props.get("PD_Mx_Dep"),   # departure from normal
        "rainfall":    props.get("Pt_24_Rain"),
        "humidity":    props.get("D1_RH_0830"),

        # Today's forecast
        "fc_max":      props.get("D1F_Mx_Tem"),
        "fc_min":      props.get("D1F_Mn_Tem"),
        "fc_dep":      props.get("D1F_Mx_Dep"),
        "fc_weather":  props.get("D1F_Weathr"),

        # 7-day forecast
        "day2_max":    props.get("D2_Mx_Temp"),
        "day2_min":    props.get("D2_Mn_Temp"),
        "day2_weather":props.get("D2_Weather"),

        "day3_max":    props.get("D3_Mx_Temp"),
        "day3_min":    props.get("D3_Mn_Temp"),
        "day3_weather":props.get("D3_Weather"),

        "day4_max":    props.get("D4_Mx_Temp"),
        "day4_min":    props.get("D4_Mn_Temp"),
        "day4_weather":props.get("D4_Weather"),

        "day5_max":    props.get("D5_Mx_Temp"),
        "day5_min":    props.get("D5_Mn_Temp"),
        "day5_weather":props.get("D5_Weather"),

        "day6_max":    props.get("D6_Mx_Temp"),
        "day6_min":    props.get("D6_Mn_Temp"),
        "day6_weather":props.get("D6_Weather"),

        "day7_max":    props.get("D7_Mx_Temp"),
        "day7_min":    props.get("D7_Mn_Temp"),
        "day7_weather":props.get("D7_Weather"),

        # Sun and moon times
        "sunrise":     props.get("Sr_Time"),
        "sunset":      props.get("Ss_Time"),

        # Warning colour — filled in later from HWCW_Status.json
        "warning_color": None,
        "warning_text":  None,
    }

# ── HELPER: determine alert level from temperature ────────────────────────
def get_alert(temp):
    if temp is None:
        return {"level": "unknown", "ml": "അജ്ഞാതം", "en": "Unknown"}
    if temp >= 42:
        return {"level": "extreme", "ml": "അതീവ ജാഗ്രത", "en": "Extreme Danger"}
    if temp >= 40:
        return {"level": "warning", "ml": "മുന്നറിയിപ്പ്", "en": "Warning"}
    if temp >= 38:
        return {"level": "alert",   "ml": "അലേർട്ട്",      "en": "Alert"}
    if temp >= 36:
        return {"level": "watch",   "ml": "ജാഗ്രത",        "en": "Watch"}
    return     {"level": "normal",  "ml": "സാധാരണ",       "en": "Normal"}

# ── MAIN FUNCTION ─────────────────────────────────────────────────────────
def fetch_all():
    print("\n🌡  Kerala Heat Watch — Data Fetch Starting")
    print(f"    Time: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}")
    print("─" * 50)

    # ── Step 1: Fetch all three files ─────────────────────────────────────
    forecast_data  = fetch_json(URLS["forecast"],  "CD_Status_Forecast")
    observed_data  = fetch_json(URLS["observed"],  "Observed_Stations")
    warnings_data  = fetch_json(URLS["warnings"],  "HWCW_Status")

    # ── Step 2: Extract all Kerala stations from forecast + observed ──────
    kerala_stations = {}  # keyed by stat_code

    for source_label, geojson in [("forecast", forecast_data), ("observed", observed_data)]:
        if not geojson:
            continue
        features = geojson.get("features", [])
        for feature in features:
            props = feature.get("properties", {})
            lat   = props.get("Latitude")
            lon   = props.get("Longitude")

            if not is_kerala(lat, lon):
                continue  # skip non-Kerala stations

            stat_code = str(props.get("Stat_Code", ""))
            if not stat_code:
                continue

            # If this station already came from forecast, don't overwrite with observed
            # Forecast data is more complete
            if stat_code in kerala_stations and source_label == "observed":
                continue

            station = extract_station(props, source_label)
            kerala_stations[stat_code] = station

    print(f"\n  📍 Kerala stations found: {len(kerala_stations)}")

    # ── Step 3: Add warning colours from HWCW_Status.json ────────────────
    if warnings_data:
        features = warnings_data.get("features", [])
        matched = 0
        for feature in features:
            props     = feature.get("properties", {})
            stat_code = str(props.get("Stat_Code", ""))
            if stat_code in kerala_stations:
                # Warning colour: 1=Red(severe), 2=Orange, 3=Yellow, 4=Green(normal)
                color_code = props.get("Day1_Color") or props.get("HW_Color") or props.get("Color")
                kerala_stations[stat_code]["warning_color"] = color_code
                matched += 1
        print(f"  🚨 Warning colours matched: {matched} stations")

    # ── Step 4: Add computed alert level for each station ─────────────────
    for code, station in kerala_stations.items():
        temp = station.get("fc_max") or station.get("obs_max")
        station["alert"] = get_alert(temp)

    # ── Step 5: Build final output ────────────────────────────────────────
    # Convert dict to list, sorted south to north by latitude
    stations_list = sorted(
        kerala_stations.values(),
        key=lambda s: s.get("lat") or 0
    )

    output = {
        "meta": {
            "source":       "India Meteorological Department",
            "source_urls":  list(URLS.values()),
            "fetched_at":   datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "station_count": len(stations_list),
            "note":         "Stations filtered by Kerala geographic boundary (lat 8-13, lon 74.5-77.6)"
        },
        "stations": stations_list
    }

    # ── Step 6: Save to data/weather.json ────────────────────────────────
    os.makedirs("data", exist_ok=True)
    output_path = "data/weather.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n  💾 Saved to {output_path}")
    print(f"  ✅ Done — {len(stations_list)} Kerala stations in weather.json")
    print("─" * 50)

    # Print a quick summary
    print("\n  Station summary:")
    for s in stations_list:
        temp  = s.get("fc_max") or s.get("obs_max")
        alert = s["alert"]["en"]
        print(f"    {s['name']:<30} {str(temp)+'°C':<8} {alert}")

# ── RUN ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings()  # suppress SSL warning since IMD uses non-standard cert
    fetch_all()
