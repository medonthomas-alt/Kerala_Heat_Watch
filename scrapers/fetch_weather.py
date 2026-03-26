import requests
from bs4 import BeautifulSoup
import json
import re
import urllib3
from datetime import datetime
import os

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 1. PRECISE STATION MAPPING (Rounding to 1 decimal for stability)
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

def get_ksdma_meta():
    url = "https://sdma.kerala.gov.in/temperature/"
    base_url = "https://sdma.kerala.gov.in"
    try:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, verify=False, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        maps = {"max": None, "min": None, "humid": None}
        
        # Map Link Chasing
        max_l = soup.find('a', string=re.compile("Maximum Temperature", re.I))
        if max_l: maps["max"] = max_l.get('href') if max_l.get('href').startswith('http') else base_url + max_l.get('href')
        min_l = soup.find('a', string=re.compile("Minimum Temperature", re.I))
        if min_l: maps["min"] = min_l.get('href') if min_l.get('href').startswith('http') else base_url + min_l.get('href')
        humid_img = soup.find('img', src=re.compile("Hot-Humid", re.I))
        if humid_img: maps["humid"] = humid_img.get('src') if humid_img.get('src').startswith('http') else base_url + humid_img.get('src')

        all_p = [p.get_text(strip=True) for p in soup.find_all('p') if len(p.get_text()) > 30][:3]
        return {
            "alert_header": "ഉയർന്ന താപനില മുന്നറിയിപ്പ് – മഞ്ഞ അലർട്ട്",
            "alert_paragraphs": all_p,
            "max_map": maps["max"], "min_map": maps["min"], "humid_map": maps["humid"],
            "sync_at": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
    except: return {}

def get_imd_stations():
    url = "https://dss.imd.gov.in/dwr_img/GIS/CD_Status_Forecast.json"
    try:
        res = requests.get(url, verify=False, timeout=20)
        data = res.json()
        stations = []
        for feature in data.get('features', []):
            p = feature['properties']
            lon, lat = p.get('Longitude', 0), p.get('Latitude', 0)
            
            # Kerala boundary check
            if 74.5 <= lon <= 77.5 and 8.0 <= lat <= 13.0:
                temp = p.get('D1F_Mx_Tem') or p.get('temp', 0)
                hum = p.get('D1_RH_0830') or p.get('rh', 0)
                
                # Coordinate matching for Precise Names
                coord_key = (round(lat, 1), round(lon, 1))
                name = NAME_LOOKUP.get(coord_key) or p.get('Stat_Name') or p.get('District') or f"AWS {round(lat, 2)}"

                # Determine Status
                status = "Normal"
                if temp >= 38: status = "Alert"
                elif temp >= 36: status = "Watch"

                # Heat Index (Real Feel)
                real_feel = temp
                if temp >= 27 and hum > 0:
                    real_feel = round(0.5 * (temp + 61.0 + ((temp - 68.0) * 1.2) + (hum * 0.094)), 1)

                stations.append({
                    "name": name, "lat": lat, "lon": lon,
                    "temp": temp, "status": status,
                    "departure": f"+{p.get('D1F_Mx_Dep', 0)}" if p.get('D1F_Mx_Dep', 0) > 0 else p.get('D1F_Mx_Dep', 0),
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
