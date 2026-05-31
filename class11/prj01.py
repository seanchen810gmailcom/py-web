#######################模組#######################
# asyncio 是 Python 內建的非同步工具。
# 可以把它想成「任務小管家」： 如果某件事需要等網路回應，他可以先去安排別的事，不會讓整個城市傻傻卡住
import asyncio
import discord # pip install -U discord.py；這個套件負責和Discord 溝通
import os # 用來讀取環境變數
from dotenv import load_dotenv # pip install python-dotenv；這個套件負責讀取 .env 檔案
import requests # pip install requests；這個套件負責幫我們發出 HTTP 請求，拿到網路上的資料
from myfunction.myfunction import WwatherAPI # 從我們自己寫的 myfunction 模組裡，拿到 WwatherAPI 這個類別，讓我們可以用它來查天氣

#######################初始化#######################
load_dotenv() # 讀取.env檔案，讓程式可以拿到DC_BOT_TOKEN這類資料

# event loop 可以想成「非同步任務的轉盤」：
# 哪個工作先做、哪個工作要等一下，會由這個轉盤幫忙安排。
# Python 3.10+ 在主程式裡不一定會先自動準備好這個轉盤，
# 所以我們自己先建立一個給Discord使用。
asyncio.set_event_loop(asyncio.new_event_loop())
# 建立一個新的 event loop，給Discord使用
# Intent 可以想成「先跟Discord勾選：我想收到哪些類型的通知」
# 如果沒有先打開某個 Intent，Discord就不會把那種資料送給機器人。
intents = discord.Intents.default()
intents.message_content = True # 允許機器人看到訊息真正的文字內容，這樣她才知道有人是不是輸入了Hello

bot = discord.Client(intents=intents) # 建立機器人本體，並把 intents 交給它
tree = discord.app_commands.CommandTree(bot) # 建立一個「指令樹」，讓我們可以在裡面登記指令

# 把WEATHER_API_KEY這個環境變數拿出來，準備給我們的 WwatherAPI 類別使用
weather_api_key = os.getenv("API_KEY") # 從環境變數拿到API金鑰
weather_api = WwatherAPI(weather_api_key) # 建立天氣API物件，讓後面可以用它查天氣、拿天氣圖示

def build_weather_enbed(weather_summary):
    """把整理好的天氣摘要排成Discord 卡牌。"""
    # weather_summary 已經是整理好的資料
    # 所以這個函式只要專心處理卡片外觀，不用再拆API原始資料
    embed = discord.Embed(
        title=f"{weather_summary['city_name']}的當前天氣",
        description=f"描述：{weather_summary['description']}",
        color=discord.Colour.from_str("#1E90FF"), # 這裡用了一個藍色的顏色代碼，讓卡片看起來比較有天氣的感覺
    )

    # get_icon_url() 會把圖示代碼組成圖片網址，再放到卡片右上角
    icon_url = weather_api.get_icon_url(weather_summary["icon_code"])
    embed.set_thumbnail(url=icon_url)

    embed.add_field(
        name="溫度",
        value=f"{weather_summary['temperature_celsius']}°C",
        inline=False, # 這裡設定為 False，讓溫度欄位獨占一行，看起來比較清楚
    )

    return embed

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
    print(f"{bot.user} is ready and online")
    # await：等這件事完成後再繼續往下
    # return：直接結束函式
    # tree.sync()：把slash 指令送去Discord登記
    await tree.sync() # 把我們在程式裡登記的指令，同步到 Discord 上，讓她知道我們有哪些指令可以用

@bot.event
async def on_message(message):
    # message 就是一則剛剛出現在頻道的訊息
    if message.author == bot.user: # 如果這則訊息的作者是機器人自己，就不理他（避免無限循環）
        return

    if message.content == "Hello": # 如果這則訊息的內容是 Hello
        await message.channel.send("Hey!") # 就回 Hey!
        print("有人打招呼了！") # 在終端機印出「有人打招呼了！」，讓我們知道這件事發生了

    #!會傳到頻道裡的每個人

#######################指令#######################
@tree.command(name="hello", description="Say hello to the bot")
async def hello(interaction: discord.Interaction):
    """輸入/hello，機器人會回傳hey!"""
    # interaction 就是這次使用指令時送來的資料包
    # 裡面包含是誰按的，在哪裡按的，指令相關資訊
    await interaction.response.send_message("Hey!") # 回覆這個指令，內容是 Hey!
    #!只會傳給使用者

# / weather 的重點是：
# 把「查資料」交給WeatherAPI，把「回應使用者」留在Bot主程式處理
@tree.command(name="weather", description="取得當前天氣資訊")
async def weather(interaction: discord.Interaction, city_name: str):
    """輸入/ weather 並提供城市名稱，會回傳當前天氣資訊。"""
    # defer() 會先告訴Discord「機器人正在處理中」，
    # 這樣查天氣需要一點時間時，指令就不會因為等太久而失敗。
    await interaction.response.defer() # 告訴Discord「機器人正在處理指令，請稍等」

    city = city_name.strip() # 去掉使用者輸入的城市名稱前後的空白，讓資料更乾淨

    if not weather_api.api_key: # 如果我們沒有成功拿到API金鑰，就回覆錯誤訊息
        await interaction.followup.send("尚未設定Weather API金鑰，無法查詢天氣資訊。")
        return

    try:
        # 向WeatherAPI拿整理好的天氣摘要，
        # 主程式只要處理結果，不用自己拆很多層字典
        weather_summary = weather_api.get_weather_summary(city)

    except (requests.RequestException, ValueError):
        await interaction.followup.send("查詢天氣資訊時發生錯誤，請稍後再試。")
        return

    if weather_summary is None:
        await interaction.followup.send(f"找不到{city}的天氣資訊，請確認城市名稱是否正確。")
        return

    embed = build_weather_enbed(weather_summary) # 把天氣摘要排成一張好看的卡片
    await interaction.followup.send(embed=embed) # 回覆這個指令，內容是剛剛做好的天氣卡片

#######################啟動#######################
def main():
    token = os.getenv("DC_BOT_TOKEN") # 從環境變數拿到機器人的 token

    if not token: # 如果沒有成功拿到機器人 token，就不要啟動機器人
        print("錯誤：尚未設定 DC_BOT_TOKEN")
        return

    bot.run(token) # 啟動機器人

# 如果這份檔案是「直接執行」，
# 就呼叫 main() 啟動機器人！
if __name__ == "__main__":
    main() # 正式啟用程式