import os
import json
import pandas as pd

# 讀SPY
df = pd.read_excel("data/etf.xlsx", sheet_name="SPY")

# 跟 API 一樣丟掉目標欄位，避免不小心把未來資訊帶進去
drop_cols = ["未來1日漲跌(目標)", "未來5日漲跌(目標)", "未來20日漲跌(目標)"]
df = df.drop(columns=[c for c in drop_cols if c in df.columns])

# 把日期轉成字串，讓 JSON 可以存
df["日期"] = pd.to_datetime(df["日期"]).dt.strftime("%Y-%m-%d")

# 取最後 30 筆
rows = df.tail(3).to_dict(orient="records")

# 包成 API 需要的格式
payload = {"rows": rows}

# 存成檔案
os.makedirs("examples", exist_ok=True)

with open("examples/request.json", "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False)

print("saved -> examples/request.json")
