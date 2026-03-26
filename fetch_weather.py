import requests
import json
import os

def get_imd_data():
    # വിലാസം മാറ്റം: പുതിയ API ലിസ്റ്റ് പ്രകാരം
    aws_url = "https://city.imd.gov.in/api/aws_data_api.php"
    
    headers = {"User-Agent": "Mozilla/5.0"}
    all_kerala_data = {}

    try:
        # കേരളത്തിലെ മൊത്തം AWS ഡാറ്റ എടുക്കാൻ ശ്രമിക്കുന്നു
        response = requests.get(aws_url, headers=headers, timeout=15, verify=False)
        if response.status_code == 200:
            data = response.json()
            # കേരളത്തിലെ സ്റ്റേഷനുകൾ മാത്രം അരിച്ചെടുക്കുന്നു
            for station in data:
                if station.get("STATE") == "KERALA":
                    all_kerala_data[station["STATION"]] = {
                        "temp": station.get("CURR TEMP"),
                        "humidity": station.get("RH"),
                        "district": station.get("DISTRICT"),
                        "last_update": station.get("DATE") + " " + station.get("TIME")
                    }
            print(f"✅ {len(all_kerala_data)} കേരള സ്റ്റേഷനുകളിലെ വിവരങ്ങൾ ലഭിച്ചു.")
    except Exception as e:
        print(f"❌ പിശക്: {e}")

    # ഡാറ്റ സേവ് ചെയ്യുന്നു
    os.makedirs('data', exist_ok=True)
    with open('data/weather.json', 'w') as f:
        json.dump(all_kerala_data, f, indent=4)

if __name__ == "__main__":
    get_imd_data()
