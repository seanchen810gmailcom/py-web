#######################匯入模組#######################
from tkinter import *
import os


# 匯入thinter模組，用*匯入所有內容
#######################定義函數########################
def open_safari():
    os.system("open -a Safari")  # 使用os.system()方法打開Safari瀏覽器


def open_function():
    label.config(text="Hello, World!", bg="black", fg="red")  # 更新標籤的文字內容


def close_function():
    label.config(text="", bg=windows.cget("bg"))  # 清空標籤的文字內容，清掉背景顏色


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
btn2 = Button(
    windows, text="Close Screen", command=close_function
)  # 創建一個按鈕，點擊後執行open_safari函數
btn2.pack()  # 使用pack()方法將按鈕放在視窗中
##########################建立標籤#####################
label = Label(windows, text="")  # 創建一個標籤，顯示文字
label.pack()  # 使用pack()方法將標籤放在視窗中
#######################運行應用程式#####################
# 開始執行主回圈，等待用戶操作
windows.mainloop()
