#######################匯入模組#######################f
# 匯入 ttkbootstrap 模組，提供教美麗的tkinter界面
from ttkbootstrap import *  #! pip install ttkbootstrap -U 這一行一定要先在終端機安裝才能用增強版的tkinter

# 匯入sys、os模組，用來設定工作目錄
import sys
import os

#######################設定工作目錄########################
os.chdir(sys.path[0])
#######################建立視窗########################
window = Tk()  # 建立視窗
window.title("GUI")  # 設定視窗標題
#####################設定字體#####################
font_size = 20  # 設定字型大小
window.option_add("*font", {"Helvetica", font_size})  # 設定字型
# 設定預設字型，這裡設定為Helvetica，大小為20
#####################設定主題#####################
style = Style(theme="minty")  # 設定主題exee
style.configure("my.TButton", font=("Helvetica", font_size))  # 設定按鈕的字型
