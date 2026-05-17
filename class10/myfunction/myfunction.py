##########################################匯入模組######################################
import requests #用來像天氣網站送出請求，並接住回傳資料

############################定義類別######################################
#這類別可以看成是把第一次實作天氣功能時的主程式流程拆開整理
# 原本查天氣，取圖示代碼，組圖是網址，下載圖片都寫在同一段；
# 現在改成一個方法只負責一件事，比較容易看出每個赤功能各自在做什麼
class WwatherAPI:
    """把OpenWeather 得查詢流程整理成重複使用的工具類別。"""
    def __init__(self, api_key,lang="zh_tw"):
        # __init__()專門負責準備共用設定
        #這樣就不用像早期把所有設定ˇ都直接寫在主程式那樣，
        #現在查詢時都重新主動處理API金鑰、語言、單位和網址前半段。
        self.api_key = api_key#api key是天氣網站辨認身份用的金鑰
        self.lang = "metric"#這一版固定用攝氏資料查詢
        self.lang = lang#lang 代表傳的語言，這裡使用繁體中文
        self.base_url = "https://api.openweathermap.org/data/2.5/weather?"
        self.icon_url = "https://openweathermap.org/img/wn/"
    def get_current_weather(self, city_name):
        #像天氣網站拿原始資料
        send_url = f"{self.base_url}q={city_name}&appid={self.api_key}&units={self.lang}"
        response = requests.get(send_url)
        return response.json() #回傳原始資料的 JSON 物件
    def get_icon_url(self,icon_code):
        #組出天氣圖是網址
        return f"{self.icon_base_url}{icon_code}@2x.png"
# ============================
