#######################匯入模組#######################
# 匯入 ttkbootstrap 模組，提供教美麗的tkinter界面
from ttkbootstrap import *  #! pip install ttkbootstrap -U 這一行一定要先在終端機安裝才能用增強版的tkinter

# 匯入sys、os模組，用來設定工作目錄
import sys
import os
from PIL import Image, ImageTk


#############################定義函式##########################
def on_switch_change():
    # Checkbutton 狀態改變時，將目前布林值顯示在標籤上
    check_label.config(text=str(check_type.get()))


#######################設定工作目錄########################
# 將工作目錄切換到目前程式所在的資料夾，方便讀取相關檔案
os.chdir(sys.path[0])
#######################建立視窗########################
window = Tk()  # 建立視窗
window.title("Label Image")  # 設定視窗標題
######################讀取圖片####################
image = Image.open("weather.png")  # 暫時註釋，檢查文件是否存在
weather_photo = ImageTk.PhotoImage(image)
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
#########################建立標籤####################
weather_label = Label(window, image=weather_photo)
weather_label.pack(padx=20, pady=20)
weather_label.image = weather_photo
window.mainloop()
