#######################匯入模組#######################
from tkinter import *
import os
import random
import sys
from PIL import Image, ImageTk

# 要先 pip install pillow
# 匯入thinter模組，用*匯入所有內容
#######################設定工作目錄########################
os.chdir(sys.path[0])


#######################定義函數########################
def move_circle(event):
    # 取得按下的按鈕
    key = event.keysym
    print(key)
    if key == "Right":
        canvas.move(circle, 10, 0)
    elif key == "Left":
        canvas.move(circle, -10, 0)
    elif key == "Up":
        canvas.move(circle, 0, -10)
    elif key == "Down":
        canvas.move(circle, 0, 10)
    # 取得按下的按鈕
    elif key == "d":
        canvas.move(rectangle, 10, 0)
    elif key == "a":
        canvas.move(rectangle, -10, 0)
    elif key == "w":
        canvas.move(rectangle, 0, -10)
    elif key == "s":
        canvas.move(rectangle, 0, 10)


def exit_windows():
    windows.destroy()  # 關閉視窗


#######################建立視窗########################
# 創建視窗
windows = Tk()
# 設定主視窗標題
windows.title("My First GUI")
windows.option_add("*Font", "行街行階 20")  # 設定全局字體
#########################建立畫布#########################

canvas = Canvas(windows, width=600, height=600, bg="white")
canvas.pack()


#########################建立圖片######################
"""
【原始方式】tkinter 內建 PhotoImag，只支援PNG、GIF、PGM、PPM
    img = PhotoImage(file="小截圖 2026-03-22 上午9.30.04.png")

【Pillow 方式】使用 Image.open() 載入圖片
    好處：
        1. 支援幾乎所有格式（JPG、PNG、BMP、WebP、TIFF 等）
        2. 可在顯示前對圖片做處理（縮放、裁切、旋轉、濾鏡等）   
"""
# 設立視窗圖片
windows.iconbitmap("fruf8 thfyc 32x32.ico")  # 暫時註釋，檢查文件是否存在
#######################載入圖片########################
# tkinter 內建 PhotoImage，只支援 PNG、GIF、PGM、PPM 格式 （不支援JPG、BMP 等）
image = Image.open("小截圖 2026-03-22 上午9.30.04.png")  # 暫時註釋，檢查文件是否存在
img = ImageTk.PhotoImage(image)
# 將PIL Image 物件轉換成 tkinter 可顯示的 PhotoImage 物件
#! 注意：需保留 img 的參照，否則圖片會被 Python 垃圾回收機制回收而消失
#######################顯示圖片#########################
# 在畫布上顯示圖片，設定圖片的中心點座標為（300,300）
my_img = canvas.create_image(300, 300, image=img)  # 暫時註釋（img 為 None）
########################畫圓形#########################
# 在畫布上畫一個圓形，起始位置為（250,150），結束位置為（300,200），填充顏色為紅色
circle = canvas.create_oval(250, 150, 300, 200, fill="red")
rectangle = canvas.create_rectangle(50, 70, 70, 50, fill="blue")
msg = canvas.create_text(
    300, 100, text="Mac Book Pro!!!", fill="black", font=("Arial", 30)
)
#######################綁定按鍵事件######################
# 將案件事件綁定到畫面上，當按下指定的按鍵時，移動對應的物件
canvas.bind_all("<Key>", move_circle)
########################建立按鈕#####################
exit_btn = Button(windows, text="Exit", command=exit_windows)
exit_btn.pack()  # 使用pack()方法將按鈕放在視窗中
##########################建立標籤#####################

#######################運行應用程式#####################

# 開始執行主回圈，等待用戶操作
windows.mainloop()
