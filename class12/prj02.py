import requests

API_KEY = "63ccac7b9230476e7c07e7bad8bf519c"
BASE_URL = "https://api.openweathermap.org/data/2.5/forecast?"
UNITS = "metric"
LANG = "zh_tw"

city_name = "taipei"
send_url= (f"{BASE_URL}q={city_name}&appid={API_KEY}&units={UNITS}&lang={LANG}")

print(f"發送的URL：{send_url}")

response = requests.get(send_url)

response.raise_for_status()

info = response.json()

if "city" in info:
    for forecast in info["list"]:
        dt_txt = forecast["dt_txt"]
        temp = forecast["main"]["temp"]
        weather_description= forecast["weather"][0]["description"]

        print(dt_txt, temp, weather_description)
else:
    print("找不到城市")