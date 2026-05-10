# 認識裝飾詞（Decorators)的用法
# ============================
# 第一段：函式可以傳給另一個函式
# ============================
# 先認識一個重要觀念：函式可以像變數一樣傳來傳去
# 定義一個簡單的函式
def say_hello():
    print("hello")

# 定義一個可以「接收函式」當作參數的函式
def run_with_announce(func):
    print("開始執行函式")
    func()  # 呼叫「傳進來的函式」
    print("結束執行函式")

# 直接呼叫：一般我們平常呼叫函式的方式
print("直接呼叫")
say_hello()  # 直接呼叫函式

print()
print("透過 run_with_announce 呼叫：")
run_with_announce(say_hello)  # 注意：這裡是「把函式本身」當作參數傳入（不是 say_hello()）
# ============================

# 第二段：手寫一個最基本的 decorator（無參數版本）
# - decorator 會「接收一個函式」並回傳一個「包裝後的新函式」
def gift_wrap(func):
    # wrapper 是包裝後要回傳的新函式
    def wrapper():
        print("=======================")
        func()  # 在 wrapper 裡面呼叫原本的 func
        print("=======================")
    return wrapper  # 回傳 wrapper（注意：是函式本身，不是 wrapper()）

# 不用 @ 語法時：手動把 say_hello 變成「包裝後的版本」
say_hello = gift_wrap(say_hello)
say_hello()

# 第三段：使用 @decorator 語法糖
# - @gift_wrap 其實等同於：say_hello = gift_wrap(say_hello)
@gift_wrap
def say_hello():
    print("hello")
say_hello()

# 第四段：有參數的 decorator（三層結構）
# 外層先接收 decorator 的參數（name/description）
# 中層再接收要被裝飾的函式（func）
# 內層回傳真正會被呼叫的 wrapper
def register_command(name, description):  # 外層：接收參數
    print(f"[登記]指令/{name}：{description}")

    def decorator(func):  # 中層：接收函式
        def wrapper():  # 內層：包裝後的函式（最後真正被呼叫的是它）
            print(f"[執行]指令/{name}")
            func()  # 執行傳入的函式
        return wrapper
    return decorator

# @register_command(...) 會先執行外層 register_command，回傳 decorator，
# 然後再把 hello_command 丟進 decorator 裡面做包裝
@register_command("greet", "打招呼的指令")
def hello_command():
    print("Hello, World!")
hello_command()
