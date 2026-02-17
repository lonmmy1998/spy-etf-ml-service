import pandas as pd
import joblib
from sklearn.metrics import roc_auc_score
from xgboost import XGBClassifier


# 1 讀資料
df = pd.read_excel("data/etf.xlsx", sheet_name="SPY")

# 2 設定目標與特徵
targets = {
    "1d": "未來1日漲跌(目標)",
    "5d": "未來5日漲跌(目標)",
    "20d": "未來20日漲跌(目標)",
}
# 3 定義哪些欄位不能當特徵
cols_not_features = [
    "日期",
    "ETF代碼",
    "未來1日漲跌(目標)",
    "未來5日漲跌(目標)",
    "未來20日漲跌(目標)",
]
# 4 先把 x 做出來
x_all = df.drop(columns=cols_not_features)
# 若 x 裡有 inf，先當成缺失值處理
x_all = x_all.replace([float("inf"), float("-inf")], pd.NA)

for tag, y_col in targets.items():
    print("\n==", tag, "==")

    # 5 取出y
    y_all = df[y_col]

    # 6 過濾掉 y 是 Nan 的列（20d通常有）
    mask = y_all.notna()

    x = x_all.loc[mask].copy()
    y = y_all.loc[mask].copy()

    # y 若有 inf 也排除
    y = y.replace([float("inf"), float("-inf")], pd.NA)
    ok = y.notna()
    x = x.loc[ok]
    y = y.loc[ok]

    # 7 轉型： y 變 0/1 int，並把 index 重排（避免造成問題）
    x = x.reset_index(drop=True)
    y = y.astype(int).reset_index(drop=True)

    # 8 重新算切分點（每個 horizon 的資料長度可能不同
    n = len(x)
    cut = int(n * 0.8)

    x_train = x.iloc[:cut]
    x_test = x.iloc[cut:]
    y_train = y.iloc[:cut]
    y_test = y.iloc[cut:]

    # 9 長度驗收
    print("rows train:", len(x_train), "labels train", len(y_train))
    print("rows test:", len(x_test), "labels test", len(y_test))

    # 10 模型
    model = XGBClassifier(
        n_estimators=300,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        eval_metric="logloss",
    )

    model.fit(x_train, y_train)

    # 11 評估
    prob = model.predict_proba(x_test)[:, 1]
    print("len(prob):", len(prob))

    auc = roc_auc_score(y_test.to_numpy(), prob)
    print(f"auc({tag}) = {auc:.4f}")

    # 12 存檔
    out_path = f"artifacts/model_spy_{tag}.joblib"
    joblib.dump({"model": model, "feature_cols": list(x.columns)}, out_path)
    print("saved -> ", out_path)
