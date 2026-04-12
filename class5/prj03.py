"""
使用json：
    json_str = json.dumps(data)  # 將Python物件轉換為JSON字串
    data = json.loads(json_str)  # 將JSON字串轉換回Python
"""

###############################匯入模組#########################
import requests  # 載入requests 套件（用來發送請求）內建json模組

##############################定義常數########################
API_KEY = "63ccac7b9230476e7c07e7bad8bf519c"  # API key
BASE_URL = "https://api.openweathermap.org/data/2.5/weather?"
UNITS = "metric"  # 單位（公制）
LANG = "zh_tw"  # 語言（繁體中文）
##############################主程式########################
city_name = input("請輸入程式名稱：")  # 輸入程式名稱

# 構建糗請求URL
send_url = f"{BASE_URL}appid={API_KEY}&q={city_name}&units={UNITS}&lang={LANG}"

print(f"發送的URL：{send_url}")
response = requests.get(send_url)  # 發送請求
info = response.json()  # 解析JSON格式的回應
