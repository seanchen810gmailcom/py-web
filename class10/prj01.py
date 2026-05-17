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
# 建立一個新的 event loop，給Discord使用
# Intent 可以想成「先跟Discord勾選：我想收到哪些類型的通知」
# 如果沒有先打開某個 Intent，Discord就不會把那種資酪送給機器人。
intents = discord.Intents.default()
intents.message_content = True # 允許機器人看到訊息真正的文字內容，這樣她才知道有人是不是輸入了Hello

bot = discord.Client(intents=intents) # 建立機器人本體，並把 intents 交給它
tree = discord.app_commands.CommandTree(bot) # 建立一個「指令樹」，讓我們可以在裡面登記指令
#######################事件#######################
"""
@bot.event 這種寫法叫做裝飾器，
可以把它寫成幫下面的函式貼上一張「事件處理員」標籤。
def 是一般函式，通常會照順序一路做完。
async def 是可以搭配 await 的函式；
遇到需要等一下的工作時，
他可以先暫停，等事情完後再回來繼續做。
"""
@bot.event
async def on_ready():
    print(f"{bot.user}is ready and online")
    # await：等這件事完成後再繼續往下
    # return：直接結束函式
    # tree.sync()：把slash 指令送去Discord登記
    await tree.sync() # 把我們在程式裡登記的指令，同步到 Discord 上，讓她知道我們有哪些指令可以用
@bot.event
async def on_message(message):
    # messafe 就是一則剛剛出現在頻道的訊息
    if message.author == bot.user: # 如果這則訊息的作者是機器人自己，就不理他（避免無限循環）
        return
    if message.content == "Hello": # 如果這則訊息的內容是 Hello
        await message.channel.send("Hey!") # 就回 Hello, World!
        print("有人打招呼了！") # 在終端機印出「有人打招呼了！」，讓我們知道這件事發生了
    #!會傳到頻道裡的每個人
#######################指令#######################
@tree.command(name="hello",description="Say hello to the bot")
async def hello(interaction: discord.Interaction):
    """輸入/hello，機器人會回傳hey!"""
    # interaction 就是這次使用指令時送來的資料包
    # 裡面包含是誰按的，在哪裡暗的，指令相關資訊
    await interaction.response.send_message("Hey!") # 回覆這個指令，內容是 Hello, World!
    #!只會傳給使用者
#######################啟動#######################
def main():
    bot.run(os.getenv("DC_BOT_TOKEN")) # 從環境變數拿到機器人的 token，然後啟動機器人
    print("有人打招呼了！") # 在終端機印出「有人打招呼了！」，讓我們知道這件事發生了
#如果這份檔案室「直接執行」，
# 就呼叫 main() 啟動機器人！

if __name__=="__main__":
    main() #正式啟用程式