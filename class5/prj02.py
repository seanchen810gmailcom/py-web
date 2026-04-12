#######################匯入模組#######################
from ttkbootstrap import *  #! pip install ttkbootstrap -U 這一行一定要先在終端機安裝才能用增強版的tkinter
import sys
import os

#######################設定工作目錄#########################
os.chdir(sys.path[0])  # 設定工作目錄
#########################建立視窗########################
window = Tk()  # 建立視窗
window.title("GUI")  # 設定視窗標題


#####################定義函數########################
# 顯示計算結果的函式
def show_result():
    entry_text = entry.get()  # 取得Entry的文字
    try:
        result = eval(entry_text)  # 計算結果
    except:
        result = "計算錯誤"
    label.config(text=result)


#####################設定字體#####################
font_size = 20  # 設定字型大小
window.option_add("*font", {"Helvetica", font_size})  # 設定字型
# 設定預設字型，這裡設定為Helvetica，大小為20
#####################設定主題#####################
style = Style(theme="minty")  # 設定主題exee
style.configure("my.TButton", font=("Helvetica", font_size))  # 設定按鈕的字型
#######################建立標籤#########################
# 顯示計算結果的label
label = Label(window, text="計算結果:")
label.grid(row=2, column=0, columnspan=2, padx=10, pady=10)
#########################建立按鈕#########################
# 顯示計算結果
button = Button(window, text="顯示計算結果", command=show_result, style="my.TButton")
button.grid(row=1, column=0, columnspan=2, padx=10, pady=10)
###########################建立Entry物件#########################
# entry物件
entry = Entry(window, width=30)
entry.grid(row=0, column=0, columnspan=2, padx=10, pady=10)
# padx, pady 為元件與元件之間的間距
window.mainloop()  # 啟動視窗的事件迴圈
