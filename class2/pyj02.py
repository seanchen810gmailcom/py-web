#######################匯入模組#######################
from tkinter import *
import os
import random

# 匯入thinter模組，用*匯入所有內容
#######################定義函數########################


def open_function():
    fg_random_color = "#" + "".join(
        [random.choice("0123456789ABCDEF") for i in range(6)]
    )  # 隨機生成一個顏色的十六進制值
    bg_random_color = "#" + "".join(
        [random.choice("0123456789ABCDEF") for i in range(6)]
    )  # 隨機生成一個顏色的十六進制值
    label.config(
        text="Hello, World!", bg=f"{bg_random_color}", fg=f"{fg_random_color}"
    )  # 更新標籤的文字內容
    """
    比對展開寫法：
    fg_random_color = "#"
    for i in range(6):
        fg_random_color += random.choice("0123456789abcdef")
    bg_random_color = "#"
    for i in range(6):
        bg_random_color += random.choice("0123456789abcdef")
    label.config(
        text="Hello, World!", bg=f"{bg_random_color}", fg=f"{fg_random
    """


#######################建立視窗########################
# 創建視窗
windows = Tk()
# 設定主視窗標題
windows.title("My First GUI")
windows.geometry("400x300")  # 設定視窗大小
windows.option_add("*Font", "行街行階 20")  # 設定全局字體
########################建立按鈕#####################
btn1 = Button(
    windows, text="Show Screen", command=open_function
)  # 創建一個按鈕，點擊後執行open_safari函數
btn1.pack()  # 使用pack()方法將按鈕放在視窗中
##########################建立標籤#####################
label = Label(windows, text="")  # 創建一個標籤，顯示文字
label.pack()  # 使用pack()方法將標籤放在視窗中
#######################運行應用程式#####################
# 開始執行主回圈，等待用戶操作
windows.mainloop()
