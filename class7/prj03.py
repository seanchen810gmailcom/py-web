"""
這個程式會建立一個簡單的天氣查詢 GUI 應用程式，使用 OpenWeatherMap API 取得指定城市的天氣資訊。
功能：
    1. 輸入城市名稱後按「搜尋」按鈕。
    2. 取得該城市的天氣描述、溫度、濕度，以及天氣圖示。
    3. 顯示攝氏或華氏溫度（使用 Checkbutton 切換）。
"""

############################### 匯入模組 #########################
import requests  # 發送 HTTP 請求用的套件，需先安裝 pip install requests
import os
import sys
from ttkbootstrap import *  # 進階版的 tkinter 介面元件套件，需先安裝 pip install ttkbootstrap
from PIL import Image, ImageTk  # 圖片讀取與 tkinter 圖片顯示
from tkinter import messagebox  # 顯示錯誤訊息的對話框

############################## 定義常數 ########################
API_KEY = "63ccac7b9230476e7c07e7bad8bf519c"  # OpenWeatherMap API key
BACE_URL = "https://api.openweathermap.org/data/2.5/weather?"  # 天氣資料 API 基礎網址
UNITS = "metric"  # 溫度單位：metric 表示攝氏
LANG = "zh_tw"  # 回傳語言：繁體中文
ICON_BACE_URL = "https://openweathermap.org/img/wn/"  # 天氣圖示 URL 基礎網址

####################### 設定工作目錄 ########################
# 將工作目錄切換到目前程式所在資料夾，方便讀取同目錄下的檔案
os.chdir(sys.path[0])

####################### 建立視窗 ########################
window = Tk()  # 建立主視窗
window.title("Label Image")  # 設定視窗標題

##################### 設定字體 #####################
font_size = 20  # 全域字型大小
window.option_add("*font", {"Helvetica", font_size})  # 設定預設字型

##################### 設定主題 #####################
style = Style(theme="minty")  # 使用 ttkbootstrap 的 Minty 主題
style.configure("my.TButton", font=("Helvetica", font_size))  # 設定按鈕字型
style.configure(
    "my.TCheckbutton", font=("Helvetica", font_size)
)  # 設定 Checkbutton 字型

############################## 主程式 ##########################


def show_result():
    """查詢城市天氣，並更新 GUI 顯示。"""
    # 更新 Checkbutton 狀態標籤，顯示目前是否使用攝氏
    check_label.config(text=str(check_type.get()))

    # 取得使用者輸入的城市名稱
    city_name = entry.get().strip()
    print("城市名稱：", city_name)

    # 組成 API 查詢 URL
    send_url = f"{BACE_URL}appid={API_KEY}&q={city_name}&units={UNITS}&lang={LANG}"
    print(f"發送的URL：{send_url}")

    # 送出請求並取得回應
    response = requests.get(send_url)
    info = response.json()  # 解析 JSON 回應

    # 如果沒有回傳 404，就代表成功取得天氣資訊
    if "main" in info:
        humidity = info["main"]["humidity"]  # 濕度
        temperature = info["main"]["temp"]  # 溫度
        weather = info["weather"][0]["description"]  # 天氣描述文字
        icon_code = info["weather"][0]["icon"]  # 天氣圖示代碼
        icon_url = f"{ICON_BACE_URL}{icon_code}@2x.png"

        # 下載天氣圖示圖片
        print(f"下載天氣圖標：{icon_url}")
        icon_response = requests.get(icon_url)
        if icon_response.status_code == 200:
            # 成功下載後，儲存為 weather.png
            with open("weather.png", "wb") as icon_file:
                icon_file.write(icon_response.content)
        else:
            print("無法下載天氣圖標")
            messagebox.showerror("錯誤", "無法下載天氣圖標")

        # 將圖片轉成 tkinter 可顯示的格式
        image = Image.open("weather.png")
        weather_photo = ImageTk.PhotoImage(image)
        weather_label.config(image=weather_photo)
        weather_label.image = weather_photo  # 保留參考，避免被垃圾回收

        # 根據 Checkbutton 的值顯示攝氏或華氏
        if check_type.get():
            temp_label.config(text=f"{temperature}°C")
        else:
            temp_label.config(text=f"{temperature * 1.8 + 32}°F")

        # 更新濕度與天氣描述
        hum_label.config(text=f"{humidity}%")
        what_weather.config(text=weather)
    else:
        # 查無該城市時顯示錯誤訊息
        print(f"無法取得 {city_name} 的天氣資訊，請確認城市名稱是否正確。")
        messagebox.showerror(
            "錯誤", f"無法取得 {city_name} 的天氣資訊，請確認城市名稱是否正確。"
        )


########################## 建立 UI 元件 ########################
# 城市輸入提示文字
label = Label(window, text="請輸入想搜尋的城市")
label.grid(row=0, column=0, columnspan=2, padx=10, pady=10)

# 搜尋按鈕，按下後呼叫 show_result
button = Button(window, text="搜尋", command=show_result)
button.grid(row=0, column=5, columnspan=2, padx=10, pady=10)

# 城市名稱輸入框
entry = Entry(window, width=30)
entry.grid(row=0, column=3, columnspan=2, padx=10, pady=10)

# 顯示天氣圖示的 Label
weather_label = Label(window, text="放圖片")
weather_label.grid(row=6, column=0, columnspan=2, padx=10, pady=10, sticky="W")

# 顯示天氣描述的 Label
what_weather = Label(window, text="")
what_weather.grid(row=2, column=3, columnspan=2, padx=10, pady=10)

# 顯示溫度的 Label
temp_label = Label(window, text="")
temp_label.grid(row=2, column=3)

# 顯示濕度的 Label
hum_label = Label(window, text="")
hum_label.grid(row=3, column=2)

# BooleanVar 會與 Checkbutton 同步，儲存 True/False
check_type = BooleanVar()
check_type.set(True)  # 預設為 True（顯示攝氏）

# 顯示目前 Checkbutton 狀態的標籤
check_label = Label(window, text="True")
check_label.grid(row=3, column=4)

# 建立 Checkbutton，切換攝氏 / 華氏
check = Checkbutton(
    window,
    variable=check_type,
    onvalue=True,
    offvalue=False,
    command=show_result,
    style="my.TCheckbutton",
)
check.grid(row=3, column=3)

############################### 啟動主迴圈 ########################
window.mainloop()
