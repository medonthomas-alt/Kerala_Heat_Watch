import requests
import json
import os
from datetime import datetime

# 1. The 14 Districts and their coordinates
districts = {
    "Kasaragod": [12.510, 74.985], "Kannur": [11.874, 75.370],
    "Wayanad": [11.610, 76.083], "Kozhikode": [11.258, 75.780],
    "Malappuram": [11.073, 76.074], "Palakkad": [10.786, 76.654],
    "Thrissur": [10.527, 76.214], "Ernakulam": [9.931, 76.267],
    "Idukki": [9.850, 76.915], "Kottayam": [9.591, 76.522],
    "Alappuzha": [9.498, 76.338], "Pathanamthitta": [9.264, 76.787],
    "Kollam": [8.893, 76.614], "Trivandrum": [8.524, 76.936]
}

# 2. Find the working date (tries Today and Yesterday)
def get_weather():
    headers = {"User-Agent": "Mozilla/5.0"}
    date_to_use = datetime.now().strftime("%Y%m%d") + "00"
    all_data = {}

    for name, coords in districts.items():
        url = f"https://mausamgram.imd.gov.in/test4_mme.php?lat_gfs={coords[0]}&lon_gfs={coords[1]}&date={date_to_use}_3hr_0p125"
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                all_data[name] = response.json()
        except:
            print(f"Skipping {name} due to error")
    
    # Save the results to our data folder
    os.makedirs('data', exist_ok=True)
    with open('data/weather.json', 'w') as f:
        json.dump(all_data, f)

if __name__ == "__main__":
    get_weather()
