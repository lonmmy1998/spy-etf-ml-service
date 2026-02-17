from fastapi import FastAPI, Body
import joblib
import pandas as pd
from pydantic import BaseModel
from typing import List, Dict, Any
from fastapi import HTTPException
import traceback


app = FastAPI()


class PredictRequest(BaseModel):
    rows: List[Dict[str, Any]]


class PredictResponse(BaseModel):
    prob_1d: float
    label_1d: int
    prob_5d: float
    label_5d: int
    prob_20d: float
    label_20d: int


# 啟動時先把模型載入(避免每次請求都重讀檔案)
bundle_1d = joblib.load("artifacts/model_spy_1d.joblib")
bundle_5d = joblib.load("artifacts/model_spy_5d.joblib")
bundle_20d = joblib.load("artifacts/model_spy_20d.joblib")

models = {
    "1d": bundle_1d["model"],
    "5d": bundle_5d["model"],
    "20d": bundle_20d["model"],
}
# 三個模型用的特徵欄位順序一樣：先以 5d 為主
feature_cols = bundle_5d["feature_cols"]

# Swagger UI 用的範例 ，讓 /docs 不再顯示 additionalProp1
EXAMPLE_PAYLOAD = {
    "rows": [
        {
            "日期": "2025-01-28",
            "ETF代碼": "SPY",
            **{c: 0.0 for c in feature_cols},
        }
    ]
}

cols_not_features = ["日期", "ETF代碼", "未來1日漲跌(目標)", "未來5日漲跌(目標)", "未來20日漲跌(目標)"]


@app.get("/health")
def health():
    return {"status": "ok"}

# 用 excel 最後一天算一次


@app.get("/predict_last")
def predict_last():
    return {
        "message": "This endpoint is disabled in Docker mode. Use POST /predict with JSON rows."
    }


# 把 users 的 rows 轉成 DataFrame 再預測


@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest = Body(..., example=EXAMPLE_PAYLOAD)):
    try:
        # rows 不能為空
        if not req.rows:
            raise HTTPException(status_code=400, detail="rows 不能是空的")

        # 把 JSON 的 rows 變成 dataframe
        df_in = pd.DataFrame(req.rows)

        # 必要欄位檢查：日期一定要有
        if "日期" not in df_in.columns:
            raise HTTPException(status_code=400, detail="缺少必要欄位：日期")

        # 檢查特徵欄位是否齊全（以 feature_cols 為準）
        missing = [c for c in feature_cols if c not in df_in.columns]
        if missing:
            raise HTTPException(status_code=400, detail=f"缺少特徵欄位：{missing}")

        # 日期轉換（失敗回 400）
        try:
            df_in["日期"] = pd.to_datetime(df_in["日期"])
        except Exception:
            raise HTTPException(status_code=400, detail="日期格式錯誤，請用 YYYY-MM-DD")

        # 排序 + 前值填補
        df_in = df_in.sort_values("日期").ffill()

        # 取特徵並確保欄位順序一致
        x_in = df_in[feature_cols].copy()

        # 把所有特徵轉成數字
        try:
            x_in = x_in.apply(pd.to_numeric, errors="raise")
        except Exception:
            raise HTTPException(status_code=400, detail="特徵欄位需為數值，偵測到無法轉成數字內容")

        # 取最後一筆（保留 DataFrame 形狀）
        x_last = x_in.iloc[[-1]]

        # 三個模型推論（取 class=1 的機率）
        p1 = float(models["1d"].predict_proba(x_last)[0, 1])
        p5 = float(models["5d"].predict_proba(x_last)[0, 1])
        p20 = float(models["20d"].predict_proba(x_last)[0, 1])

        # 正確回傳 keys + 正確 label
        return {
            "prob_1d": p1, "label_1d": int(p1 >= 0.5),
            "prob_5d": p5, "label_5d": int(p5 >= 0.5),
            "prob_20d": p20, "label_20d": int(p20 >= 0.5),
        }

    except Exception as e:
        print("PREDICT ERROR:", repr(e))
        print(traceback.format_exc())
        raise
