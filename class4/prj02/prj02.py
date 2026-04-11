#######################匯入模組#######################
from ttkbootstrap import *  #! pip install ttkbootstrap -U 這一行一定要先在終端機安裝才能用增強版的tkinter
import sys
import os
import os
import random
import sys
from PIL import Image, ImageTk

#######################定義函數########################
clicked = False  # 初始化變數


def test():
    global clicked
    if clicked == False:
        label2 = label.config(text="你好")  # 更新標籤的文字內容
        clicked = True
    elif clicked == True:
        babel2 = label.config(text="")  # 改回原本的文字
        clicked = False


def quit_windows():
    window.destroy()  # 關閉視窗


#######################建立視窗########################
window = Tk()  # 建立視窗
window.title("GUI")  # 設定視窗標題
#####################設定字型#####################
font_size = 20  # 設定字型大小
window.option_add("*font", ("Helvetica", font_size))  # 設定字型
# 設定預設字型，設定為Helvetica，大小為20
#####################設定主題#####################
style = Style(theme="superhero")  # 設定主題
"""
"my.TButton"嚰應名邏輯：
    就像幫東西貼標籤一樣，分成兩部分，用「.」隔開：
    前面的字元就是定義的物件名稱，如「my」
        前半段"my" → 自己取的名字，可以換成任何名字，例如"big"、"red"
        後半段 "TButton" → 固定寫法，代表「按鈕」這種元件
            T 是 Ttk （一種按鈕工具箱） 的縮寫
            就像「T恤」的T一樣，是平排名稱的開頭
常見元件的後半段爹法：
    按鈕 → TButton 標籤 → TLabel 輸入框 → TEntry
"""
style.configure("my.TButton", font=("Helvetica", font_size))  # 設定按鈕的字型
#######################設定工作目錄########################
os.chdir(sys.path[0])
#########################建立標籤#########################
"""
grip()方法的參數：
    格式：物件變數.grip(row=?, column=?, sticly=?, columnspan=?, rowspan=?)
    grop網格排列物件：
        row：橫排
        column：縱排
        sticky：對齊方式，裡面可以填入N、S、E、W，分別代表北、南、東、西，也可以填東南西北的組合
        columnspan：向右合併欄位
        rowspan：向下合併欄位
"""
label = Label(window, text="hello world")
label.grid(
    row=0, column=0, sticky="E"
)  # 使用grid()方法將標籤放在視窗中，並設定位置和對齊方式
#########################建立按鈕#########################
button1 = Button(
    window, text="瀏覽", command=test, style="my.TButton"
)  # 創建一個按鈕，點擊後執行test函數，使用自定義的樣式
button1.grid(row=1, column=0, sticky="EW", columnspan=2)
button2 = Button(
    window, text="結束", command=quit_windows, style="my.TButton"
)  # 創建一個按鈕，點擊後執行test函數，使用自定義的樣式
button2.grid(row=0, column=1, sticky="EW")
window.mainloop()
