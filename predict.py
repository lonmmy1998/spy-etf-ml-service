import joblib
import pandas as pd

# 1 讀取模型
bundle = joblib.load("artifacts/model_spy_5d.joblib")
modle = bundle["model"]
feature_cols = bundle["feature_cols"]

# 2 讀資料
df = pd.read_excel("data/etf.xlsx", sheet_name="SPY")

# 3 做出 x (像train.py一樣)
cols_not_features = ["日期", "ETF代碼", "未來1日漲跌(目標)", "未來5日漲跌(目標)", "未來20日漲跌(目標)"]
x = df.drop(columns=cols_not_features)

# 4 取最後一天那一筆來預測
x_last = x[feature_cols].iloc[[-1]]

# 5 預測「上漲(=1)」的機率
p = float(modle.predict_proba(x_last)[0, 1])
label = int(p >= 0.5)

print({"prob_5d": p, "label_5d": label})
