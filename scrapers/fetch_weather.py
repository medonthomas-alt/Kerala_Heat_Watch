import requests
from bs4 import BeautifulSoup
import json
import re
import urllib3
from datetime import datetime
import os

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
KSDMA_URL = "https://sdma.kerala.gov.in/temperature/"
IMD_JSON_URL = "https://dss.imd.gov.in/dwr_img/GIS/CD_Status_Forecast.json"
BASE_URL = "https://sdma.kerala.gov.in"
HEADERS = {"User-Agent": "Mozilla/5.0"}

# District Mapper for Clean Names
DISTRICT_MAP = {
    (8.48, 76.95): "Thiruvananthapuram",
    (9.0, 76.92): "Punalur (Kollam)",
    (9.49, 76.33): "Alappuzha",
    (9.59, 76.52): "Kottayam",
    (10.15, 76.39): "Kochi (CIAL)",
    (10.54, 76.27): "Thrissur",
    (10.77, 76.65): "Palakkad",
    (11.25, 75.77): "Kozhikode",
    (11.87, 75.37): "Kannur",
    (12.5, 75.0): "Kasaragod"
}

def get_ksdma_meta():
    try:
        res = requests.get(KSDMA_URL, headers=HEADERS, verify=False, timeout=20)
        soup = BeautifulSoup(res.text, 'html.parser')
        maps = {"max": None, "min": None, "humid": None}
        
        # Link Chasing
        max_l = soup.find('a', string=re.compile("Maximum Temperature", re.I))
        if max_l: maps["max"] = max_l.get('href') if max_l.get('href').startswith('http') else BASE_URL + max_l.get('href')
        min_l = soup.find('a', string=re.compile("Minimum Temperature", re.I))
        if min_l: maps["min"] = min_l.get('href') if min_l.get('href').startswith('http') else BASE_URL + min_l.get('href')
        humid_img = soup.find('img', src=re.compile("Hot-Humid", re.I))
        if humid_img: maps["humid"] = humid_img.get('src') if humid_img.get('src').startswith('http') else BASE_URL + humid_img.get('src')

        all_p = [p.get_text(strip=True) for p in soup.find_all('p') if len(p.get_text()) > 30][:3]
        return {
            "alert_header": "ഉയർന്ന താപനില മുന്നറിയിപ്പ് – മഞ്ഞ അലർട്ട്",
            "alert_paragraphs": all_p,
            "max_map": maps["max"], "min_map": maps["min"], "humid_map": maps["humid"],
            "sync_at": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
    except: return {}

def get_imd_stations():
    try:
        res = requests.get(IMD_JSON_URL, verify=False, timeout=25)
        data = res.json()
        stations = []
        for feature in data.get('features', []):
            p = feature['properties']
            lon, lat = round(p.get('Longitude', 0), 2), round(p.get('Latitude', 0), 2)
            
            # Kerala boundary check
            if 74.5 <= lon <= 77.5 and 8.0 <= lat <= 13.0:
                temp = p.get('D1F_Mx_Tem')
                hum = p.get('D1_RH_0830')
                dep = p.get('D1F_Mx_Dep')
                
                # Name Cleanup
                name = DISTRICT_MAP.get((lat, lon)) or p.get('Stat_Name') or p.get('District') or f"Station {lat}"

                # Calculation for Heat Index
                real_feel = temp
                if temp and hum and temp >= 27:
                    real_feel = round(0.5 * (temp + 61.0 + ((temp - 68.0) * 1.2) + (hum * 0.094)), 1)

                stations.append({
                    "name": name, "lat": lat, "lon": lon,
                    "temp": temp, "departure": f"+{dep}" if dep and dep > 0 else dep,
                    "humidity": hum, "real_feel": real_feel,
                    "warning_code": p.get('warning_color', 4),
                    "sunrise": p.get('Sr_Time'), "sunset": p.get('Ss_Time')
                })
        return stations
    except: return []

if __name__ == "__main__":
    final_data = {"meta": get_ksdma_meta(), "stations": get_imd_stations()}
    os.makedirs('data', exist_ok=True)
    with open('data/weather.json', 'w', encoding='utf-8') as f:
        json.dump(final_data, f, indent=2, ensure_ascii=False)
    print("✅ Sync Successful.")
