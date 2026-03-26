def get_imd_stations():
    # PRECISE COORDINATE DICTIONARY
    # We round to 1 decimal place to ensure matches even if the IMD JSON fluctuates slightly
    NAME_LOOKUP = {
        (8.5, 77.0): "Thiruvananthapuram (Airport)",
        (8.5, 76.9): "Thiruvananthapuram",
        (8.7, 76.7): "Varkala",
        (8.9, 76.6): "Kollam",
        (9.0, 76.9): "Punalur",
        (9.6, 76.5): "Kottayam",
        (10.2, 76.4): "Kochi",
        (10.5, 76.3): "Vellanikara",
        (10.8, 76.7): "Palakkad",
        (10.8, 76.2): "Pattambi",
        (10.8, 76.0): "Thavanur",
        (11.0, 75.9): "Tirur",
        (11.3, 75.8): "Kozhikode",
        (11.9, 75.4): "Kannur"
    }

    try:
        res = requests.get(IMD_JSON_URL, verify=False, timeout=25)
        data = res.json()
        stations = []
        
        for feature in data.get('features', []):
            p = feature['properties']
            lon, lat = p.get('Longitude', 0), p.get('Latitude', 0)
            
            if 74.5 <= lon <= 77.5 and 8.0 <= lat <= 13.0:
                temp = p.get('D1F_Mx_Tem') or p.get('temp', 0)
                hum = p.get('D1_RH_0830') or p.get('rh', 0)
                
                # ROUND COORDINATES FOR MATCHING
                coord_key = (round(lat, 1), round(lon, 1))
                name = NAME_LOOKUP.get(coord_key)
                
                # Fallback to IMD provided name or AWS label
                if not name:
                    name = p.get('Stat_Name') or p.get('District') or f"AWS {round(lat, 2)}"

                # HEAT STATUS LOGIC
                status = "Normal"
                if temp >= 38: status = "Alert"
                elif temp >= 36: status = "Watch"

                # REAL FEEL CALCULATION
                real_feel = temp
                if temp >= 27 and hum > 0:
                    real_feel = round(0.5 * (temp + 61.0 + ((temp - 68.0) * 1.2) + (hum * 0.094)), 1)

                stations.append({
                    "name": name,
                    "lat": lat, "lon": lon,
                    "temp": temp,
                    "status": status,
                    "departure": f"+{p.get('D1F_Mx_Dep', 0)}" if p.get('D1F_Mx_Dep', 0) > 0 else p.get('D1F_Mx_Dep', 0),
                    "humidity": hum,
                    "real_feel": real_feel,
                    "rainfall": p.get('D1_Rainfall', 0),
                    "warning_code": p.get('warning_color', 4),
                    "sunrise": p.get('Sr_Time'),
                    "sunset": p.get('Ss_Time')
                })
        return stations
    except: return []
