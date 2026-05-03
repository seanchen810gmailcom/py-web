"""
使用json：
    json_str = json.dumps(data)  # 將Python物件轉換為JSON字串
    data = json.loads(json_str)  # 將JSON字串轉換回Python
"""

###############################匯入模組#########################
import requests  # 載入requests 套件（用來發送請求）內建json模組
import os
import sys

##############################定義常數########################
API_KEY = "63ccac7b9230476e7c07e7bad8bf519c"  # API key
BACE_URL = "https://api.openweathermap.org/data/2.5/weather?"
UNITS = "metric"  # 單位（公制）
LANG = "zh_tw"  # 語言（繁體中文）
ICON_BACE_URL = "https://openweathermap.org/img/wn/"  # 天氣圖標基礎URL
##############################主程式########################
city_name = input("請輸入程式名稱：")  # 輸入程式名稱
os.chdir(sys.path[0])  # 設定工作目錄
# 構建糗請求URL
send_url = f"{BACE_URL}appid={API_KEY}&q={city_name}&units={UNITS}&lang={LANG}"

print(f"發送的URL：{send_url}")
response = requests.get(send_url)  # 發送請求
info = response.json()  # 解析JSON格式的回應
if not (info.get("cod") == 404):  # 如果回應中沒有404錯誤碼，表示成功取得天氣資訊
    humidity = info["main"]["humidity"]  # 濕度
    temperature = info["main"]["temp"]  # 溫度
    weather = info["weather"][0]["description"]  # 天氣狀況

    print(f"{city_name}的天氣狀況：{weather}")
    print(f"{city_name}的溫度：{temperature}°C")
    print(f"{city_name}的體感溫度：{info['main']['feels_like']}°C")
    print(f"{city_name}的濕度：{humidity}%")
    icon_code = info["weather"][0]["icon"]
    # 根據圖標代碼組合圖標下載網址
    icon_url = f"{ICON_BACE_URL}{icon_code}@2x.png"

    # 印出圖標網址並發送下載請求
    print(f"下載天氣圖標：{icon_url}")
    os.system(f"open -u '{icon_url}'")
    icon_response = requests.get(icon_url)
    # 若下載成功，就將圖標存成 png 檔案
    if icon_response.status_code == 200:
        """
        with open(...,"wb")的意思是：
            with 會在城市離開這個區塊時自動幫我們關檔，不用自己呼叫close()
            open(...,"web")代表用「二進位寫入」模式寫檔；圖片不是純文字，所以要用wb
        """
        with open(f"weather.png", "wb") as icon_file:
            # content 裡面是下載回來的原始位元組資料，write() 會把它寫進檔案
            icon_file.write(icon_response.content)
    else:
        print("無法下載天氣圖標")
else:
    print(f"無法取得{city_name}的天氣資訊，請確認城市名稱是否正確。")
