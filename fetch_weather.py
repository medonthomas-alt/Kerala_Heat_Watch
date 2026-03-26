import requests
import json
import os
from datetime import datetime

def get_dss_weather():
    url = "https://dss.imd.gov.in/dwr_img/GIS/CD_Status_Forecast.json"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    print("🛰️ Accessing IMD Decision Support System...")

    try:
        # verify=False handles common government SSL certificate issues
        response = requests.get(url, headers=headers, timeout=20, verify=False)
        
        if response.status_code == 200:
            # Some IMD APIs return a string that needs to be parsed twice
            data = response.json()
            if isinstance(data, str):
                data = json.loads(data)
            
            kerala_data = {}

            # Search through the list for Kerala districts [cite: 287]
            for item in data:
                if item.get("State") == "KERALA":
                    district = item.get("District")
                    # Mapping data based on the District Warning API structure 
                    kerala_data[district] = {
                        "status": item.get("Status", "No Data"),
                        "day1_color": item.get("Day1_Color", "4"), # Default to Green 
                        "day2_color": item.get("Day2_Color", "4"),
                        "warning_code": item.get("Day1", "1"),    # Default to No Warning 
                        "last_update": datetime.now().strftime("%Y-%m-%d %H:%M")
                    }
            
            if kerala_data:
                print(f"✅ Successfully mapped {len(kerala_data)} Kerala districts.")
            else:
                print("⚠️ Connection successful, but Kerala was not found in the list.")
        else:
            print(f"❌ Server rejected request (Status {response.status_code})")

    except Exception as e:
        print(f"❌ Script Error: {e}")
        kerala_data = {"error": str(e)}

    # Save to the data folder for your website to read
    os.makedirs('data', exist_ok=True)
    with open('data/weather.json', 'w') as f:
        json.dump(kerala_data, f, indent=4)

if __name__ == "__main__":
    get_dss_weather()
