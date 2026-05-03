#######################匯入模組#######################
# 匯入 ttkbootstrap 模組，提供教美麗的tkinter界面
from ttkbootstrap import *  #! pip install ttkbootstrap -U 這一行一定要先在終端機安裝才能用增強版的tkinter

# 匯入sys、os模組，用來設定工作目錄
import sys
import os


#############################定義函式##########################
def on_switch_change():
    # Checkbutton 狀態改變時，將目前布林值顯示在標籤上
    check_label.config(text=str(check_type.get()))


#######################設定工作目錄########################
# 將工作目錄切換到目前程式所在的資料夾，方便讀取相關檔案
os.chdir(sys.path[0])
#######################建立視窗########################
window = Tk()  # 建立視窗
window.title("CheakButton")  # 設定視窗標題
#####################設定字體#####################
font_size = 20  # 設定字型大小
window.option_add("*font", {"Helvetica", font_size})  # 設定字型
# 設定預設字型，這裡設定為Helvetica，大小為20
#####################設定主題#####################
style = Style(theme="minty")  # 設定主題exee
style.configure("my.TButton", font=("Helvetica", font_size))  # 設定按鈕的字型
style.configure("my.TCheckbutton", font=("Helvetica", font_size))
#####################建立變數#####################
# BooleanVar 是 tkinter / ttk 用來和元件同步的布林變數
check_type = BooleanVar()
# 預設為勾選擇狀態
check_type.set(True)
#########################建立標籤####################
# 建立標籤、顯示目前 Checkbutton 對應的布林值
check_label = Label(window, text="True")
# 將標籤放到視窗中的指定位置
check_label.grid(row=1, column=2, padx=10, pady=10)
##########################建立Checkbutton####################
# Checkbutton 會用 check_type 綁再一起
# 勾選時存 True，取消勾選將存 False 並在狀態改變時呼叫 on_switch_change
check = Checkbutton(
    window,
    variable=check_type,
    onvalue=True,
    offvalue=False,
    command=on_switch_change,
    style="my.TCheckbutton",
)
# 將 Checkbutton 放到視窗中的指定位置
check.grid(row=1, column=1, padx=10, pady=10)

############################運行應用程式##################
# 開始執行主迴圈，等待使用者操作
window.mainloop()
