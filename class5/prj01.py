#######################匯入模組#######################
from ttkbootstrap import *  #! pip install ttkbootstrap -U 這一行一定要先在終端機安裝才能用增強版的tkinter
import sys
import os
from PIL import Image, ImageTk
from tkinter import filedialog  #! 因為TTK沒有這一個功能，所以必須去從最原始的TK匯入


#######################定義函數########################
def open_file():
    global file_path
    # 選則檔案, initialdir為初始目錄，這裡設定為程式所有目錄
    file_path = filedialog.askopenfilename(initialdir=sys.path[0])
    label2.config(text=file_path)  # 顯示檔名


def show_image():
    global file_path
    image = Image.open(file_path)  # 打開圖片檔案
    """
    調整圖片大小，讓他適合畫布的大小
    Image.LANCZOS 是一種縮放魔法，就像把大象照片縮小放進相匡時，他會很仔細地把顏色混合好，讓圖片縮小後還是清楚好看，不會變得模糊或鋸齒狀
    """
    image = image.resize(
        (canvas.winfo_width(), canvas.winfo_height()), Image.Resampling.LANCZOS
    )
    # 轉換成tkinter可以用的格式
    photo = ImageTk.PhotoImage(image)
    # 在畫布上顯示圖片，圖片的左上角會對齊畫布的左上角
    canvas.create_image(0, 0, anchor="nw", image=photo)
    canvas.image = photo  # 保留圖片，避免被垃圾回收機制回收


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
label1 = Label(window, text="選擇檔案:")
label1.grid(row=0, column=0, sticky="E")

label2 = Label(window, text="無")
label2.grid(row=0, column=1, sticky="E")
#########################建立按鈕#########################
button = Button(
    window, text="瀏覽", command=open_file, style="my.TButton"
)  # 設定、按鈕樣式
button.grid(row=0, column=2, sticky="W")
button2 = Button(
    window, text="顯示", command=show_image, style="my.TButton"
)  # 設定、按鈕樣式
button2.grid(row=1, column=0, columnspan=3, sticky="EW")
canvas = Canvas(window, width=600, height=600)
canvas.grid(row=2, column=0, columnspan=3)
window.mainloop()  # 啟動視窗的事件迴圈
