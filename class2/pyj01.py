#######################匯入模組#######################
from tkinter import *
import os
import random

# 匯入thinter模組，用*匯入所有內容
#######################定義函數########################


def open_function():
    global aready_clicked
    if aready_clicked == False:
        label.config(text="Hello, World!", bg="red", fg="black")  # 更新標籤的文字內容
        aready_clicked = True
    else:
        label.config(text="Hello, World!", bg="green", fg="black")  # 更新標籤的文字內容
        aready_clicked = False


#######################建立視窗########################
# 創建視窗
windows = Tk()
# 設定主視窗標題
windows.title("My First GUI")
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
