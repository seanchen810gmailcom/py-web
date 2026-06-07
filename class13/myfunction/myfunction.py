##########################################匯入模組######################################
import requests # 用來向天氣網站送出請求，並接住回傳資料

############################定義類別######################################
# 這個類別可以看成是把第一次實作天氣功能時的主程式流程拆開整理
# 原本查天氣、取圖示代碼、組圖示網址、下載圖片都寫在同一段；
# 現在改成一個方法只負責一件事，比較容易看出每個功能各自在做什麼
class WwatherAPI:
    """把 OpenWeather 的查詢流程整理成重複使用的工具類別。"""

    def __init__(self, api_key, lang="zh_tw"):
        # __init__() 專門負責準備共用設定
        # 這樣就不用像早期把所有設定都直接寫在主程式那樣，
        # 現在查詢時會重新主動處理 API 金鑰、語言、單位和網址前半段。
        self.api_key = api_key # api_key 是天氣網站辨認身份用的金鑰
        self.lang = lang # lang 代表回傳的語言，這裡預設使用繁體中文
        self.units = "metric" # units 代表單位，metric 是攝氏溫度
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"
        self.forecast_url = "https://api.openweathermap.org/data/2.5/forecast?"
        self.icon_base_url = "https://openweathermap.org/img/wn/"

    def get_current_weather(self, city_name):
        # 向天氣網站拿原始資料
        send_url = f"{self.base_url}?q={city_name}&appid={self.api_key}&units={self.units}&lang={self.lang}"
        response = requests.get(send_url)
        response.raise_for_status() # 如果 HTTP 狀態碼是錯誤，就直接丟出錯誤
        return response.json() # 回傳原始資料的 JSON 物件

    def get_icon_url(self, icon_code):
        # 組出天氣圖示網址
        return f"{self.icon_base_url}{icon_code}@2x.png"

    def get_weather_summary(self, city_name):
        """查詢目前天氣，並整理成更容易使用的摘要資料"""
        # 這裡把原本較完整的 API 資料，整理成比較好閱讀的天氣小抄。
        # 和第一次直接在主程式裡拆資料相比，這一步多做了「資料整理」功能分割：
        # 主程式之後只要拿整理好的結果來用，就不用每次自己拆很多層字典
        info = self.get_current_weather(city_name)

        if "weather" in info and "main" in info:
            return {
                "city_name": info.get("name", city_name),
                "temperature_celsius": round(info["main"]["temp"], 2),
                "description": info["weather"][0].get("description", ""),
                "icon_code": info["weather"][0].get("icon", ""),
            }

        return None # 如果 API 回傳的資料裡沒有我們需要的資訊，就回傳 None

    def get_icon(self, icon_code):
        # 這個方法和第一次實作時下載圖示的那一段最接近。
        # 差別是現在把流程拆成兩小步：
        # 1. get_icon_url() 先負責組圖示網址
        # 2. get_icon() 再負責把圖片原始資料抓出來
        # 這樣學生會比較容易看出「組網址」和「下載圖片」是兩件不同的事。
        icon_url = self.get_icon_url(icon_code)
        response = requests.get(icon_url)

        if response.status_code == 200:
            return response.content # 回傳圖片的原始資料

        return None # 如果下載圖片失敗，就回傳 None
    def get_forecast(self, city_name):
        # get_forecast() 和 get_current_weather() 做的事情很像，
        # 都是像天氣網站拿回原始資料。
        # 差別是這裡會拿到未來美3小時一筆的預報清單。
        send_url = (
            f"{self.forecast_url}q={city_name}&appid={self.api_key}"
            f"&units={self.units}&lang={self.lang}"
        )
        response = requests.get(send_url)
        response.raise_for_status()
        return response.json()
    def get_forcast_summary(self,city_name,count=10):
        """查詢未來天氣預報，並整理成更容易使用的摘要清單。"""
        # 這裡和get_weather_summary()的想法一樣，
        # 先把API回傳的原始資料整理好，再交給主程式使用。
        # 這樣Discord bpt或GUI程式就不用每次自己拆很多層字典。
        forecast_count=max(0,count)
        try:
            info=self.get_forecast(city_name)
        except requests.HTTPError as error:
            response = error.response
            if response is not None and response.status_code == 404:
                return None
            raise
        if "city" not in info or "list" not in info:
            return None
        city_label = info["city"].get("name", city_name)
        forecast_summary = []

        for forecast in info["list"][:forecast_count]:
            forecast_summary.append(
                {
                    "city_name": city_label,
                    "datetime": forecast["dt_txt"],
                    "temperature_celsius": round(forecast["main"]["temp"],2),
                    "description": forecast["weather"][0]["description"],
                    "icon_code": forecast["weather"][0]["icon"]
                }
            )
        return forecast_summary
        
