import requests
from bs4 import BeautifulSoup
import json
import re
import os
from datetime import datetime
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def scrape_ksdma():
    url = "https://sdma.kerala.gov.in/temperature/"
    base_url = "https://sdma.kerala.gov.in"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        response = requests.get(url, headers=headers, verify=False, timeout=20)
        soup = BeautifulSoup(response.text, 'html.parser')
        maps = {"max": None, "min": None, "humid": None}

        # 1. Map Logic: Chasing Hyperlinks for T-MAX/T-MIN
        max_link = soup.find('a', string=re.compile("Maximum Temperature", re.I))
        if max_link:
            path = max_link.get('href')
            maps["max"] = path if path.startswith('http') else base_url + path

        min_link = soup.find('a', string=re.compile("Minimum Temperature", re.I))
        if min_link:
            path = min_link.get('href')
            maps["min"] = path if path.startswith('http') else base_url + path

        # 2. Map Logic: Finding Embedded Humid Map
        humid_img = soup.find('img', src=re.compile("Hot-Humid", re.I))
        if humid_img:
            src = humid_img.get('src')
            maps["humid"] = src if src.startswith('http') else base_url + src

        # 3. Text Logic: Perfect 3-Line Scrape
        content = soup.find('div', class_='entry-content') or soup
        all_p = [p.get_text(strip=True) for p in content.find_all('p') if len(p.get_text()) > 20]
        
        return {
            "meta": {
                "alert_header": "ഉയർന്ന താപനില മുന്നറിയിപ്പ് – മഞ്ഞ അലർട്ട്",
                "alert_paragraphs": all_p[:3],
                "max_map": maps["max"],
                "min_map": maps["min"],
                "humid_map": maps["humid"],
                "sync_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        }
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    data = scrape_ksdma()
    if data:
        os.makedirs('data', exist_ok=True)
        with open('data/weather.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
