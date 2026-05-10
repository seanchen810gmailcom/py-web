#######################模組#######################
# asyncio 是 Python 內建的非同步工具。
# 可以把它想成「任務小管家」： 如果某件事需要等網路回應，他可以先去安排別的事，不會讓整個城市傻傻卡住
import asyncio
import discord # pip install -U discord.py；這個套件負責和Discord 溝通
import os # 用來讀取環境變數
from dotenv import load_dotenv # pip install python-dotenv；這個套件負責讀取 .env 檔案

#######################初始化#######################
load_dotenv() # 讀取.env檔案Ｍ讓程式可以拿到DC_BOT_TOKEN這類資料

# event loop 可以想成「非同步任務的轉盤」：
# 哪個工作先做、哪個工作要等一下，會由這個轉盤幫忙安排。
# Python 3.10+ 在主程式裡不一定會先自動準備好這個轉盤，
# 所以我們自己先建立一個給Discord使用。
asyncio.set_event_loop(asyncio.new_event_loop())

# Intent 可以想成「先跟Discord勾選：我想收到哪些類型的通知」
# 如果沒有先打開某個 Intent，Discord就不會把那種資酪送給機器人。
intents = discord.Intents.default()
intents.message_content = True # 允許機器人看到訊息真正的文字內容，這樣她才知道有人是不是輸入了Hello

bot = discord.Client(intents=intents) # 建立機器人本體，並把 intents 交給它
tree = discord.app_commands.CommandTree(bot) # 建立一個「指令樹」，讓我們可以在裡面登記指令
#######################事件#######################

#######################指令#######################

#######################啟動#######################