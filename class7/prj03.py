"""
使用json：
    json_str = json.dumps(data)  # 將Python物件轉換為JSON字串
    data = json.loads(json_str)  # 將JSON字串轉換回Python
"""

###############################匯入模組#########################
import requests  # 載入requests 套件（用來發送請求）內建json模組
import os
import sys
from ttkbootstrap import *  #! pip install ttkbootstrap -U 這一行一定要先在終端機安裝才能用增強版的tkinter

# 匯入sys、os模組，用來設定工作目錄
from PIL import Image, ImageTk

##############################定義常數########################
API_KEY = "63ccac7b9230476e7c07e7bad8bf519c"  # API key
BACE_URL = "https://api.openweathermap.org/data/2.5/weather?"
UNITS = "metric"  # 單位（公制）
LANG = "zh_tw"  # 語言（繁體中文）
ICON_BACE_URL = "https://openweathermap.org/img/wn/"  # 天氣圖標基礎URL
#######################設定工作目錄########################
# 將工作目錄換到目前程式所在的資料夾，方便讀取相關檔案
os.chdir(sys.path[0])
#######################建立視窗########################
window = Tk()  # 建立視窗
window.title("Label Image")  # 設定視窗標題
######################讀取圖片####################
# 將PIL Image 物件轉換成 tkinter 可顯示的 PhotoImage 物件
#! 注意：需保留 img 的參照，否則圖片會被 Python 垃圾回收機制回收而消失
#####################設定字體#####################
font_size = 20  # 設定字型大小
window.option_add("*font", {"Helvetica", font_size})  # 設定字型
# 設定預設字型，這裡設定為Helvetica，大小為20
#####################設定主題#####################
style = Style(theme="minty")  # 設定主題exee
style.configure("my.TButton", font=("Helvetica", font_size))  # 設定按鈕的字型
style.configure("my.TCheckbutton", font=("Helvetica", font_size))
########################建立entry區塊######################


##############################主程式########################
############################建立函式##############################


def show_result():
    # Checkbutton 狀態改變時，將目前布林值顯示在標籤上
    check_label.config(text=str(check_type.get()))
    global city_name
    city_name = entry.get()  # 取得Entry的文字
    print("城市名稱：", city_name)
    send_url = f"{BACE_URL}appid={API_KEY}&q={city_name}&units={UNITS}&lang={LANG}"
    print(f"發送的URL：{send_url}")
    response = requests.get(send_url)  # 發送請求
    info = response.json()  # 解析JSON格式的回應
    if not (info.get("cod") == 404):  # 如果回應中沒有404錯誤碼，表示成功取得天氣資訊
        humidity = info["main"]["humidity"]  # 濕度
        temperature = info["main"]["temp"]  # 溫度
        weather = info["weather"][0]["description"]  # 天氣狀況
        icon_code = info["weather"][0]["icon"]
        icon_url = f"{ICON_BACE_URL}{icon_code}@2x.png"

        # 印出圖標網址並發送下載請求
        print(f"下載天氣圖標：{icon_url}")
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
        image = Image.open("weather.png")  # 暫時註釋，檢查文件是否存在
        if check_type.get() == True:
            temp_label.config(text=f"{temperature}°C")
        else:
            temp_label.config(text=f"{(temperature)*1.8+32}°F")
        weather_photo = ImageTk.PhotoImage(image)
        weather_label.config(image=weather_photo)
        weather_label.image = weather_photo
        hum_label.config(text=f"{humidity}%")
        what_weather.config(text=f"{weather}")
    else:
        print(f"無法取得{city_name}的天氣資訊，請確認城市名稱是否正確。")


label = Label(window, text="請輸入想搜尋的城市")
label.grid(row=0, column=0, columnspan=2, padx=10, pady=10)
button = Button(window, text="搜尋", command=show_result)
button.grid(row=0, column=5, columnspan=2, padx=10, pady=10)
entry = Entry(window, width=30)
entry.grid(row=0, column=3, columnspan=2, padx=10, pady=10)
weather_label = Label(window, text="放圖片")
what_weather = Label(window, text="")
what_weather.grid(row=2, column=3, columnspan=2, padx=10, pady=10)
weather_label.grid(row=6, column=0, columnspan=2, padx=10, pady=10, sticky="W")
temp_label = Label(window, text="")
temp_label.grid(row=2, column=3)
hum_label = Label(window, text="")
hum_label.grid(row=3, column=2)

# BooleanVar 是 tkinter / ttk 用來和元件同步的布林變數
check_type = BooleanVar()
# 預設為勾選擇狀態
check_type.set(True)
#########################建立標籤####################
# 建立標籤、顯示目前 Checkbutton 對應的布林值
check_label = Label(window, text="True")
# 將標籤放到視窗中的指定位置
check_label.grid(row=3, column=4)
##########################建立Checkbutton####################
# Checkbutton 會用 check_type 綁再一起
# 勾選時存 True，取消勾選將存 False 並在狀態改變時呼叫 on_switch_change
check = Checkbutton(
    window,
    variable=check_type,
    onvalue=True,
    offvalue=False,
    command=(show_result),
    style="my.TCheckbutton",
)
# 將 Checkbutton 放到視窗中的指定位置
check.grid(row=3, column=3)
#############################建立標籤########################

###############################迴圈#######################
window.mainloop()
