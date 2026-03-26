import requests
import json
import os
from datetime import datetime

def get_dss_weather():
    url = "https://dss.imd.gov.in/dwr_img/GIS/CD_Status_Forecast.json"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    # List of Kerala districts to match specifically if 'State' tag is weird
    kerala_districts = [
        "KASARAGOD", "KANNUR", "WAYANAD", "KOZHIKODE", "MALAPPURAM", 
        "PALAKKAD", "THRISSUR", "ERNAKULAM", "IDUKKI", "KOTTAYAM", 
        "ALAPPUZHA", "PATHANAMTHITTA", "KOLLAM", "THIRUVANANTHAPURAM"
    ]

    try:
        # verify=False is necessary for dss.imd.gov.in
        response = requests.get(url, headers=headers, timeout=20, verify=False)
        
        if response.status_code == 200:
            data = response.json()
            all_features = data.get("features", [])
            kerala_results = {}

            for feature in all_features:
                props = feature.get("properties", {})
                state = str(props.get("State", "")).upper().strip()
                dist = str(props.get("District", "")).upper().strip()
                
                # Logic: If State is Kerala OR the District is in our Kerala list
                if state == "KERALA" or dist in kerala_districts:
                    kerala_results[dist.capitalize()] = {
                        "status": props.get("Status", "Normal"),
                        "day1_color": props.get("Day1_Color", "4"), # 
                        "warning_code": props.get("Day1", "1"),    # 
                        "temp_max": props.get("Today_Max_temp", "N/A"),
                        "last_update": datetime.now().strftime("%Y-%m-%d %H:%M")
                    }
            
            if kerala_results:
                print(f"✅ Found {len(kerala_results)} Kerala districts!")
            else:
                # Debug: Print one sample to see what the state/district fields actually look like
                if all_features:
                    print("Sample Properties:", all_features[0].get("properties", {}))
        else:
            print(f"❌ Server error: {response.status_code}")

    except Exception as e:
        print(f"❌ Script Error: {e}")
        kerala_results = {"error": str(e)}

    os.makedirs('data', exist_ok=True)
    with open('data/weather.json', 'w') as f:
        json.dump(kerala_results, f, indent=4)

if __name__ == "__main__":
    get_dss_weather()
